from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import os
import io

from models.certificate import (
    CertificateResponse,
    EligibilityResponse,
    CertificateCreate,
    CertificateUpdate
)
from config.database import get_database
from utils.dependencies import get_current_identity, require_admin_or_teacher
from utils.progress import compute_course_progress
from utils.s3_storage import get_s3_storage
from utils.certificate_generator import get_certificate_generator


router = APIRouter(prefix="/certificates", tags=["Certificates"])


def _all_videos_completed(db, student_uuid: str, course_uuid: str) -> tuple[bool, float]:
    """
    Check if all videos in a course are completed
    Returns: (is_completed, completion_percentage)
    """
    total = db.videos.count_documents({"course_uuid": course_uuid})
    if total == 0:
        return False, 0.0
    completed = db.user_progress.count_documents({
        "student_uuid": student_uuid,
        "course_uuid": course_uuid,
        "completed": True
    })
    percentage = (completed / total) * 100.0
    return completed >= total, percentage


async def _auto_generate_certificate(db, student_uuid: str, course_uuid: str):
    """
    Automatically generate certificate when student completes course
    Also generates and uploads certificate PDF file to S3
    """
    # Check if already has certificate
    existing = db.certificates.find_one({
        "student_uuid": student_uuid,
        "course_uuid": course_uuid
    })
    if existing:
        return existing

    # Check completion
    is_completed, percentage = _all_videos_completed(db, student_uuid, course_uuid)
    if not is_completed:
        return None

    # Generate certificate
    cid = str(uuid4())
    code = str(uuid4()).split("-")[0].upper()

    # Get student and course info
    student = db.students.find_one({"uuid_id": student_uuid})
    course = db.courses.find_one({"uuid_id": course_uuid})

    student_name = student.get("name") if student else None
    course_title = course.get("title") if course else None
    issued_at = datetime.utcnow()

    doc = {
        "certificate_id": cid,
        "course_uuid": course_uuid,
        "student_uuid": student_uuid,
        "student_name": student_name,
        "course_title": course_title,
        "issued_at": issued_at,
        "code": code,
        "url": None,
        "certificate_file_key": None,
        "revoked": False,
        "revoked_at": None,
        "notes": "Auto-generated on course completion",
        "completion_percentage": percentage,
    }
    db.certificates.insert_one(doc)

    # Auto-generate and upload certificate PDF file
    if student_name and course_title:
        try:
            storage_key, s3_url = await _generate_and_upload_certificate_file(
                certificate_id=cid,
                student_name=student_name,
                course_title=course_title,
                completion_date=issued_at,
                certificate_code=code,
                completion_percentage=percentage,
                format="pdf"
            )

            # Update certificate with PDF URL
            db.certificates.update_one(
                {"certificate_id": cid},
                {"$set": {
                    "url": s3_url,
                    "certificate_file_key": storage_key
                }}
            )
            doc["url"] = s3_url
            doc["certificate_file_key"] = storage_key
        except Exception as e:
            # Log error but don't fail certificate creation
            print(f"Failed to generate certificate file: {e}")

    return doc


def _enrich_certificate(db, cert: dict) -> dict:
    """Enrich certificate with student and course names"""
    if not cert.get("student_name"):
        student = db.students.find_one({"uuid_id": cert["student_uuid"]})
        if student:
            cert["student_name"] = student.get("name")

    if not cert.get("course_title"):
        course = db.courses.find_one({"uuid_id": cert["course_uuid"]})
        if course:
            cert["course_title"] = course.get("title")

    return cert


async def _generate_and_upload_certificate_file(
    certificate_id: str,
    student_name: str,
    course_title: str,
    completion_date: datetime,
    certificate_code: str,
    completion_percentage: float,
    format: str = "pdf"  # "pdf" or "png"
) -> tuple[str, str]:
    """
    Generate certificate file and upload to S3
    Returns: (storage_key, s3_url)
    """
    generator = get_certificate_generator()
    storage = get_s3_storage()

    # Generate certificate
    if format == "pdf":
        file_bytes = generator.generate_certificate_pdf(
            student_name,
            course_title,
            completion_date,
            certificate_code,
            completion_percentage
        )
        filename = f"certificate_{certificate_code}.pdf"
        content_type = "application/pdf"
    else:  # png
        file_bytes = generator.generate_certificate_image(
            student_name,
            course_title,
            completion_date,
            certificate_code,
            completion_percentage
        )
        filename = f"certificate_{certificate_code}.png"
        content_type = "image/png"

    # Create a file-like object for upload
    class FileWrapper:
        def __init__(self, file_bytes, filename, content_type):
            self.file = file_bytes
            self.filename = filename
            self.content_type = content_type

        async def read(self, size=-1):
            return self.file.read(size)

        async def seek(self, offset):
            return self.file.seek(offset)

    file_wrapper = FileWrapper(file_bytes, filename, content_type)

    # Upload to S3
    storage_key, size, mime, s3_url = await storage.upload_file(
        file_wrapper,
        folder="certificates"
    )

    return storage_key, s3_url


# ===== STUDENT ENDPOINTS =====

@router.get("/my-certificates", response_model=List[CertificateResponse])
async def get_my_certificates(identity = Depends(get_current_identity)):
    """Get all certificates for the logged-in student"""
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")

    db = get_database()
    certs = list(db.certificates.find({
        "student_uuid": identity["user_uuid"],
        "revoked": False
    }))

    # Enrich with names
    results = []
    for cert in certs:
        enriched = _enrich_certificate(db, cert)
        results.append(CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"}))

    return results


@router.get("/course/{course_uuid}/eligibility", response_model=EligibilityResponse)
async def check_certificate_eligibility(course_uuid: str, identity = Depends(get_current_identity)):
    """Check if student is eligible for certificate"""
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")

    db = get_database()

    # Must be assigned
    if not db.user_courses.find_one({
        "student_uuid": identity["user_uuid"],
        "course_uuid": course_uuid,
        "status": "active"
    }):
        raise HTTPException(status_code=403, detail="Course not assigned")

    # Check for existing certificate
    cert = db.certificates.find_one({
        "student_uuid": identity["user_uuid"],
        "course_uuid": course_uuid
    })

    if cert:
        enriched = _enrich_certificate(db, cert)
        return EligibilityResponse(
            eligible=True,
            reason=None,
            certificate=CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"}),
            completion_percentage=cert.get("completion_percentage", 100.0)
        )

    # Check completion status
    is_completed, percentage = _all_videos_completed(db, identity["user_uuid"], course_uuid)

    return EligibilityResponse(
        eligible=is_completed,
        reason=None if is_completed else f"Course completion: {percentage:.1f}%. Complete all videos to earn certificate.",
        certificate=None,
        completion_percentage=percentage
    )


@router.post("/course/{course_uuid}/claim", response_model=CertificateResponse)
async def claim_certificate(course_uuid: str, identity = Depends(get_current_identity)):
    """Student claims certificate after completing course"""
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")

    db = get_database()

    # Must be assigned
    if not db.user_courses.find_one({
        "student_uuid": identity["user_uuid"],
        "course_uuid": course_uuid,
        "status": "active"
    }):
        raise HTTPException(status_code=403, detail="Course not assigned")

    # Check for existing certificate
    existing = db.certificates.find_one({
        "student_uuid": identity["user_uuid"],
        "course_uuid": course_uuid
    })
    if existing:
        enriched = _enrich_certificate(db, existing)
        return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})

    # Check completion
    is_completed, percentage = _all_videos_completed(db, identity["user_uuid"], course_uuid)
    if not is_completed:
        raise HTTPException(
            status_code=400,
            detail=f"Course not fully completed. Progress: {percentage:.1f}%"
        )

    # Generate certificate (now async)
    cert = await _auto_generate_certificate(db, identity["user_uuid"], course_uuid)
    enriched = _enrich_certificate(db, cert)

    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


@router.get("/verify/{code}", response_model=CertificateResponse)
async def verify_certificate(code: str):
    """Public endpoint to verify certificate by code"""
    db = get_database()
    cert = db.certificates.find_one({"code": code})

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.get("revoked"):
        raise HTTPException(status_code=400, detail="This certificate has been revoked")

    enriched = _enrich_certificate(db, cert)
    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


# ===== ADMIN ENDPOINTS =====

@router.get("/all", response_model=List[CertificateResponse])
async def list_all_certificates(
    course_uuid: Optional[str] = None,
    student_uuid: Optional[str] = None,
    revoked: Optional[bool] = None,
    identity = Depends(require_admin_or_teacher)
):
    """List all certificates with optional filters"""
    db = get_database()

    query = {}
    if course_uuid:
        query["course_uuid"] = course_uuid
    if student_uuid:
        query["student_uuid"] = student_uuid
    if revoked is not None:
        query["revoked"] = revoked

    certs = list(db.certificates.find(query).sort("issued_at", -1))

    results = []
    for cert in certs:
        enriched = _enrich_certificate(db, cert)
        results.append(CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"}))

    return results


@router.get("/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(certificate_id: str, identity = Depends(get_current_identity)):
    """Get specific certificate by ID"""
    db = get_database()
    cert = db.certificates.find_one({"certificate_id": certificate_id})

    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Students can only see their own certificates
    if identity["role"] == "student" and cert["student_uuid"] != identity["user_uuid"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    enriched = _enrich_certificate(db, cert)
    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


@router.post("/issue", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def admin_issue_certificate(
    certificate: CertificateCreate,
    identity = Depends(require_admin_or_teacher)
):
    """Admin manually issues certificate - also auto-generates PDF file"""
    db = get_database()

    # Check if certificate already exists
    existing = db.certificates.find_one({
        "student_uuid": certificate.student_uuid,
        "course_uuid": certificate.course_uuid
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Certificate already exists for this student and course"
        )

    # Check completion
    is_completed, percentage = _all_videos_completed(
        db,
        certificate.student_uuid,
        certificate.course_uuid
    )

    # Generate certificate
    cid = str(uuid4())
    code = str(uuid4()).split("-")[0].upper()

    # Get student and course info
    student = db.students.find_one({"uuid_id": certificate.student_uuid})
    course = db.courses.find_one({"uuid_id": certificate.course_uuid})

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    student_name = student.get("name")
    course_title = course.get("title")
    issued_at = datetime.utcnow()

    doc = {
        "certificate_id": cid,
        "course_uuid": certificate.course_uuid,
        "student_uuid": certificate.student_uuid,
        "student_name": student_name,
        "course_title": course_title,
        "issued_at": issued_at,
        "code": code,
        "url": None,
        "certificate_file_key": None,
        "revoked": False,
        "revoked_at": None,
        "notes": f"Manually issued by {identity['role']}",
        "completion_percentage": percentage,
    }
    db.certificates.insert_one(doc)

    # Auto-generate and upload certificate PDF file
    if student_name and course_title:
        try:
            storage_key, s3_url = await _generate_and_upload_certificate_file(
                certificate_id=cid,
                student_name=student_name,
                course_title=course_title,
                completion_date=issued_at,
                certificate_code=code,
                completion_percentage=percentage,
                format="pdf"
            )

            # Update certificate with PDF URL
            db.certificates.update_one(
                {"certificate_id": cid},
                {"$set": {
                    "url": s3_url,
                    "certificate_file_key": storage_key
                }}
            )
            doc["url"] = s3_url
            doc["certificate_file_key"] = storage_key
        except Exception as e:
            # Log error but don't fail certificate creation
            print(f"Failed to generate certificate file: {e}")

    return CertificateResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.put("/{certificate_id}", response_model=CertificateResponse)
async def update_certificate(
    certificate_id: str,
    update: CertificateUpdate,
    identity = Depends(require_admin_or_teacher)
):
    """Update certificate details"""
    db = get_database()

    cert = db.certificates.find_one({"certificate_id": certificate_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    update_data = update.model_dump(exclude_unset=True)

    # If revoking, add revoked_at timestamp
    if update_data.get("revoked") is True and not cert.get("revoked"):
        update_data["revoked_at"] = datetime.utcnow()

    # If un-revoking, clear revoked_at
    if update_data.get("revoked") is False:
        update_data["revoked_at"] = None

    db.certificates.update_one(
        {"certificate_id": certificate_id},
        {"$set": update_data}
    )

    updated_cert = db.certificates.find_one({"certificate_id": certificate_id})
    enriched = _enrich_certificate(db, updated_cert)

    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


@router.post("/{certificate_id}/upload", response_model=CertificateResponse)
async def upload_certificate_file(
    certificate_id: str,
    file: UploadFile = File(...),
    identity = Depends(require_admin_or_teacher)
):
    """Upload certificate PDF/image file"""
    db = get_database()

    cert = db.certificates.find_one({"certificate_id": certificate_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Validate file type (PDF or images)
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and image files are allowed"
        )

    storage = get_s3_storage()

    # Delete old certificate file if exists
    if cert.get("certificate_file_key"):
        storage.delete_file(cert["certificate_file_key"])

    # Upload new certificate file
    storage_key, size, mime, s3_url = await storage.upload_file(
        file,
        folder="certificates"
    )

    # Update database
    db.certificates.update_one(
        {"certificate_id": certificate_id},
        {"$set": {
            "url": s3_url,
            "certificate_file_key": storage_key
        }}
    )

    updated_cert = db.certificates.find_one({"certificate_id": certificate_id})
    enriched = _enrich_certificate(db, updated_cert)

    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: str,
    identity = Depends(require_admin_or_teacher)
):
    """Delete certificate (admin only)"""
    db = get_database()

    cert = db.certificates.find_one({"certificate_id": certificate_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Delete certificate file from S3 if exists
    if cert.get("certificate_file_key"):
        storage = get_s3_storage()
        storage.delete_file(cert["certificate_file_key"])

    db.certificates.delete_one({"certificate_id": certificate_id})
    return None


@router.post("/{certificate_id}/revoke", response_model=CertificateResponse)
async def revoke_certificate(
    certificate_id: str,
    identity = Depends(require_admin_or_teacher)
):
    """Revoke a certificate"""
    db = get_database()

    cert = db.certificates.find_one({"certificate_id": certificate_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    db.certificates.update_one(
        {"certificate_id": certificate_id},
        {"$set": {
            "revoked": True,
            "revoked_at": datetime.utcnow()
        }}
    )

    updated_cert = db.certificates.find_one({"certificate_id": certificate_id})
    enriched = _enrich_certificate(db, updated_cert)

    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


@router.post("/{certificate_id}/restore", response_model=CertificateResponse)
async def restore_certificate(
    certificate_id: str,
    identity = Depends(require_admin_or_teacher)
):
    """Restore a revoked certificate"""
    db = get_database()

    cert = db.certificates.find_one({"certificate_id": certificate_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    db.certificates.update_one(
        {"certificate_id": certificate_id},
        {"$set": {
            "revoked": False,
            "revoked_at": None
        }}
    )

    updated_cert = db.certificates.find_one({"certificate_id": certificate_id})
    enriched = _enrich_certificate(db, updated_cert)

    return CertificateResponse(**{k: v for k, v in enriched.items() if k != "_id"})


@router.post("/{certificate_id}/generate-file", response_model=CertificateResponse)
async def generate_certificate_file(
    certificate_id: str,
    format: str = "pdf",  # pdf or png
    identity = Depends(require_admin_or_teacher)
):
    """
    Auto-generate certificate file (PDF or PNG) and upload to S3
    """
    db = get_database()

    cert = db.certificates.find_one({"certificate_id": certificate_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Enrich to get student name and course title
    enriched = _enrich_certificate(db, cert)

    if not enriched.get("student_name"):
        raise HTTPException(status_code=400, detail="Student name not found")
    if not enriched.get("course_title"):
        raise HTTPException(status_code=400, detail="Course title not found")

    # Validate format
    if format not in ["pdf", "png"]:
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'png'")

    # Delete old certificate file if exists
    if cert.get("certificate_file_key"):
        storage = get_s3_storage()
        storage.delete_file(cert["certificate_file_key"])

    # Generate and upload new certificate
    storage_key, s3_url = await _generate_and_upload_certificate_file(
        certificate_id=enriched["certificate_id"],
        student_name=enriched["student_name"],
        course_title=enriched["course_title"],
        completion_date=enriched["issued_at"],
        certificate_code=enriched["code"],
        completion_percentage=enriched.get("completion_percentage", 100.0),
        format=format
    )

    # Update database
    db.certificates.update_one(
        {"certificate_id": certificate_id},
        {"$set": {
            "url": s3_url,
            "certificate_file_key": storage_key
        }}
    )

    updated_cert = db.certificates.find_one({"certificate_id": certificate_id})
    enriched_updated = _enrich_certificate(db, updated_cert)

    return CertificateResponse(**{k: v for k, v in enriched_updated.items() if k != "_id"})
