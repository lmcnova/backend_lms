# Certificate Generation Setup Guide

## Quick Setup

### 1. Install Required Packages

The certificate generation feature requires two new packages:
- **Pillow** (PIL) - For image generation
- **ReportLab** - For PDF generation

Install them using:

```bash
cd "C:\Backup Project\backend_css"
pip install -r requirements.txt
```

Or install individually:

```bash
pip install Pillow==10.4.0 reportlab==4.2.5
```

### 2. Verify Installation

Test that packages are installed correctly:

```bash
python -c "import PIL; import reportlab; print('✓ All packages installed successfully!')"
```

You should see: `✓ All packages installed successfully!`

### 3. Configure AWS S3 (Required)

Make sure your `.env` file has AWS credentials configured:

```env
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
USE_S3=true
```

### 4. Test Certificate Generation

#### Option A: Complete a Course (Student Flow)

```bash
# 1. Login as student
POST /auth/login
{
    "email": "student@example.com",
    "password": "password"
}

# 2. Mark videos as complete
POST /progress/video/{video_uuid}/complete

# 3. Check for certificate (should auto-generate when all videos complete)
GET /certificates/my-certificates
```

#### Option B: Manually Issue Certificate (Admin Flow)

```bash
# 1. Login as admin
POST /auth/login
{
    "email": "admin@example.com",
    "password": "password"
}

# 2. Issue certificate
POST /certificates/issue
{
    "course_uuid": "course-uuid",
    "student_uuid": "student-uuid"
}

# Response should include:
{
    "certificate_id": "...",
    "code": "ABC123DE",
    "url": "https://your-bucket.s3.amazonaws.com/certificates/ABC123DE.pdf",  ← PDF generated!
    "certificate_file_key": "certificates/ABC123DE.pdf"
}
```

#### Option C: Manual PDF Generation

```bash
# Generate PDF for existing certificate
POST /certificates/{certificate_id}/generate-file?format=pdf

# Or generate PNG image
POST /certificates/{certificate_id}/generate-file?format=png
```

### 5. Verify Certificate PDF

#### Download from S3
```bash
# The certificate URL is returned in the response
curl "https://your-bucket.s3.amazonaws.com/certificates/ABC123DE.pdf" -o certificate.pdf

# Or use the presigned URL endpoint
GET /media/presigned-url?key=certificates/ABC123DE.pdf
```

#### Verify Certificate Details
```bash
# Public verification endpoint (no auth required)
GET /certificates/verify/ABC123DE
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'PIL'"
**Solution**: Install Pillow
```bash
pip install Pillow==10.4.0
```

### Issue: "ModuleNotFoundError: No module named 'reportlab'"
**Solution**: Install ReportLab
```bash
pip install reportlab==4.2.5
```

### Issue: "Failed to generate certificate file"
**Solutions**:
1. Check that AWS credentials are configured in `.env`
2. Verify S3 bucket exists and has correct permissions
3. Check that `USE_S3=true` in `.env`
4. Look at console logs for specific error messages

### Issue: Certificate created but no PDF URL
**Cause**: PDF generation failed but certificate was still created (by design)

**Solution**: Manually regenerate the PDF:
```bash
POST /certificates/{certificate_id}/generate-file?format=pdf
```

### Issue: Font not found warnings
**Note**: The certificate generator uses Arial font by default. If Arial is not available, it will fall back to the default system font. This is expected and won't cause errors.

## File Structure

```
backend_css/
├── requirements.txt                        # Updated with Pillow & ReportLab
├── utils/
│   ├── certificate_generator.py           # NEW: Certificate PDF/PNG generator
│   └── s3_storage.py                      # S3 upload utility
├── routes/
│   ├── certificates.py                    # Updated: Auto-generation integrated
│   └── progress.py                        # Updated: Triggers certificate creation
├── models/
│   └── certificate.py                     # Certificate data models
└── docs/
    ├── CERTIFICATE_MANAGEMENT.md          # Full API documentation
    ├── CERTIFICATE_AUTO_GENERATION.md     # Auto-generation feature docs
    └── SETUP_CERTIFICATE_GENERATION.md    # This file
```

## What Happens Automatically

### When Student Completes Course:
1. Student marks last video as complete
2. System detects all videos are completed
3. Certificate record created in database
4. **PDF automatically generated** with student name, course title, completion date
5. **PDF uploaded to S3**
6. Certificate record updated with PDF URL
7. Student can now download certificate

### When Admin Issues Certificate:
1. Admin calls `POST /certificates/issue`
2. Certificate record created
3. **PDF automatically generated and uploaded**
4. Response includes PDF URL

### When Student Claims Certificate:
1. Student calls `POST /certificates/course/{course_uuid}/claim`
2. System verifies completion
3. Certificate created with **PDF auto-generated**

## Certificate PDF Features

✅ Professional design with borders
✅ Student name prominently displayed
✅ Course title
✅ Completion date
✅ Unique verification code
✅ Completion percentage
✅ Verification URL
✅ Print-ready format
✅ Sharable on social media (PNG option)

## API Changes Summary

### Functions Modified:
- `_auto_generate_certificate()` → Now **async** and auto-generates PDF
- `admin_issue_certificate()` → Auto-generates PDF on issuance
- `claim_certificate()` → Awaits async certificate generation
- `update_video_progress()` → Awaits async certificate generation
- `mark_video_complete()` → Awaits async certificate generation

### New Endpoint:
- `POST /{certificate_id}/generate-file` - Manual PDF/PNG generation

### Response Changes:
All certificate responses now include:
```json
{
    "url": "https://bucket.s3.amazonaws.com/certificates/ABC123DE.pdf",
    "certificate_file_key": "certificates/ABC123DE.pdf"
}
```

## Testing Commands

```bash
# Install packages
pip install -r requirements.txt

# Verify installation
python -c "import PIL; import reportlab; print('OK')"

# Start server
uvicorn main:app --reload

# Test certificate generation (admin)
curl -X POST "http://localhost:8000/certificates/issue" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"course_uuid":"course-123","student_uuid":"student-456"}'

# Verify certificate (public)
curl -X GET "http://localhost:8000/certificates/verify/ABC123DE"
```

## Need Help?

- Check `CERTIFICATE_AUTO_GENERATION.md` for detailed feature documentation
- Check `docs/CERTIFICATE_MANAGEMENT.md` for complete API reference
- Check `docs/S3_UPLOAD_SETUP.md` for S3 configuration help

## Summary

Certificate generation is now fully automatic! Just install the required packages and certificates will auto-generate with professional PDFs when students complete courses. 🎉
