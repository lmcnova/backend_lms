"""
Certificate Generator
Generates certificate images and PDFs automatically
"""
import os
import io
from datetime import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor


class CertificateGenerator:
    """Generate certificate images and PDFs"""

    def __init__(self):
        self.width = 1200
        self.height = 850

    def _get_font(self, size: int, bold: bool = False):
        """Get font, fallback to default if custom not available"""
        try:
            if bold:
                return ImageFont.truetype("arial.ttf", size)
            return ImageFont.truetype("arial.ttf", size)
        except:
            # Fallback to default font
            return ImageFont.load_default()

    def generate_certificate_image(
        self,
        student_name: str,
        course_title: str,
        completion_date: datetime,
        certificate_code: str,
        completion_percentage: float = 100.0
    ) -> io.BytesIO:
        """
        Generate certificate as PNG image
        Returns BytesIO object containing the image
        """
        # Create blank certificate
        img = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(img)

        # Draw border
        border_color = '#2C5F7D'  # Professional blue
        border_width = 20
        draw.rectangle(
            [border_width, border_width,
             self.width - border_width, self.height - border_width],
            outline=border_color,
            width=15
        )

        # Draw inner border
        inner_margin = 40
        draw.rectangle(
            [inner_margin, inner_margin,
             self.width - inner_margin, self.height - inner_margin],
            outline='#D4AF37',  # Gold
            width=3
        )

        # Load fonts
        title_font = self._get_font(70, bold=True)
        subtitle_font = self._get_font(40)
        name_font = self._get_font(60, bold=True)
        course_font = self._get_font(45, bold=True)
        text_font = self._get_font(30)
        small_font = self._get_font(20)

        # Title: "CERTIFICATE"
        title_text = "CERTIFICATE"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw.text((title_x, 100), title_text, fill='#2C5F7D', font=title_font)

        # Subtitle: "OF COMPLETION"
        subtitle_text = "OF COMPLETION"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.width - subtitle_width) // 2
        draw.text((subtitle_x, 185), subtitle_text, fill='#666666', font=subtitle_font)

        # "This is to certify that"
        certify_text = "This is to certify that"
        certify_bbox = draw.textbbox((0, 0), certify_text, font=text_font)
        certify_width = certify_bbox[2] - certify_bbox[0]
        certify_x = (self.width - certify_width) // 2
        draw.text((certify_x, 280), certify_text, fill='#333333', font=text_font)

        # Student Name (larger, bold)
        name_bbox = draw.textbbox((0, 0), student_name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (self.width - name_width) // 2
        draw.text((name_x, 340), student_name, fill='#000000', font=name_font)

        # Draw underline for name
        draw.line(
            [name_x, 415, name_x + name_width, 415],
            fill='#D4AF37',
            width=3
        )

        # "has successfully completed"
        completed_text = "has successfully completed"
        completed_bbox = draw.textbbox((0, 0), completed_text, font=text_font)
        completed_width = completed_bbox[2] - completed_bbox[0]
        completed_x = (self.width - completed_width) // 2
        draw.text((completed_x, 445), completed_text, fill='#333333', font=text_font)

        # Course Title
        course_bbox = draw.textbbox((0, 0), course_title, font=course_font)
        course_width = course_bbox[2] - course_bbox[0]
        course_x = (self.width - course_width) // 2
        draw.text((course_x, 505), course_title, fill='#2C5F7D', font=course_font)

        # Draw underline for course
        draw.line(
            [course_x, 570, course_x + course_width, 570],
            fill='#D4AF37',
            width=3
        )

        # Completion percentage
        if completion_percentage < 100:
            percentage_text = f"with {completion_percentage:.1f}% completion"
        else:
            percentage_text = "with 100% completion"
        percentage_bbox = draw.textbbox((0, 0), percentage_text, font=text_font)
        percentage_width = percentage_bbox[2] - percentage_bbox[0]
        percentage_x = (self.width - percentage_width) // 2
        draw.text((percentage_x, 600), percentage_text, fill='#666666', font=text_font)

        # Date
        date_str = completion_date.strftime("%B %d, %Y")
        date_text = f"Date of Completion: {date_str}"
        date_bbox = draw.textbbox((0, 0), date_text, font=text_font)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (self.width - date_width) // 2
        draw.text((date_x, 670), date_text, fill='#333333', font=text_font)

        # Certificate Code
        code_text = f"Certificate Code: {certificate_code}"
        code_bbox = draw.textbbox((0, 0), code_text, font=small_font)
        code_width = code_bbox[2] - code_bbox[0]
        code_x = (self.width - code_width) // 2
        draw.text((code_x, 750), code_text, fill='#999999', font=small_font)

        # Verification text
        verify_text = f"Verify at: /certificates/verify/{certificate_code}"
        verify_bbox = draw.textbbox((0, 0), verify_text, font=small_font)
        verify_width = verify_bbox[2] - verify_bbox[0]
        verify_x = (self.width - verify_width) // 2
        draw.text((verify_x, 780), verify_text, fill='#999999', font=small_font)

        # Save to BytesIO
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)

        return img_bytes

    def generate_certificate_pdf(
        self,
        student_name: str,
        course_title: str,
        completion_date: datetime,
        certificate_code: str,
        completion_percentage: float = 100.0
    ) -> io.BytesIO:
        """
        Generate certificate as PDF
        Returns BytesIO object containing the PDF
        """
        # Create PDF in landscape A4
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))

        width, height = landscape(A4)

        # Draw border
        c.setStrokeColor(HexColor('#2C5F7D'))
        c.setLineWidth(10)
        c.rect(30, 30, width - 60, height - 60, stroke=1, fill=0)

        # Inner gold border
        c.setStrokeColor(HexColor('#D4AF37'))
        c.setLineWidth(2)
        c.rect(50, 50, width - 100, height - 100, stroke=1, fill=0)

        # Title: CERTIFICATE
        c.setFont("Helvetica-Bold", 48)
        c.setFillColor(HexColor('#2C5F7D'))
        title = "CERTIFICATE"
        title_width = c.stringWidth(title, "Helvetica-Bold", 48)
        c.drawString((width - title_width) / 2, height - 120, title)

        # Subtitle: OF COMPLETION
        c.setFont("Helvetica", 28)
        c.setFillColor(HexColor('#666666'))
        subtitle = "OF COMPLETION"
        subtitle_width = c.stringWidth(subtitle, "Helvetica", 28)
        c.drawString((width - subtitle_width) / 2, height - 160, subtitle)

        # This is to certify that
        c.setFont("Helvetica", 18)
        c.setFillColor(HexColor('#333333'))
        certify = "This is to certify that"
        certify_width = c.stringWidth(certify, "Helvetica", 18)
        c.drawString((width - certify_width) / 2, height - 220, certify)

        # Student Name
        c.setFont("Helvetica-Bold", 36)
        c.setFillColor(HexColor('#000000'))
        name_width = c.stringWidth(student_name, "Helvetica-Bold", 36)
        name_x = (width - name_width) / 2
        c.drawString(name_x, height - 270, student_name)

        # Underline for name
        c.setStrokeColor(HexColor('#D4AF37'))
        c.setLineWidth(2)
        c.line(name_x - 20, height - 280, name_x + name_width + 20, height - 280)

        # has successfully completed
        c.setFont("Helvetica", 18)
        c.setFillColor(HexColor('#333333'))
        completed = "has successfully completed"
        completed_width = c.stringWidth(completed, "Helvetica", 18)
        c.drawString((width - completed_width) / 2, height - 320, completed)

        # Course Title
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(HexColor('#2C5F7D'))
        course_width = c.stringWidth(course_title, "Helvetica-Bold", 28)
        course_x = (width - course_width) / 2
        c.drawString(course_x, height - 365, course_title)

        # Underline for course
        c.setStrokeColor(HexColor('#D4AF37'))
        c.setLineWidth(2)
        c.line(course_x - 20, height - 375, course_x + course_width + 20, height - 375)

        # Completion percentage
        c.setFont("Helvetica", 16)
        c.setFillColor(HexColor('#666666'))
        if completion_percentage < 100:
            percentage_text = f"with {completion_percentage:.1f}% completion"
        else:
            percentage_text = "with 100% completion"
        percentage_width = c.stringWidth(percentage_text, "Helvetica", 16)
        c.drawString((width - percentage_width) / 2, height - 410, percentage_text)

        # Date
        c.setFont("Helvetica", 16)
        c.setFillColor(HexColor('#333333'))
        date_str = completion_date.strftime("%B %d, %Y")
        date_text = f"Date of Completion: {date_str}"
        date_width = c.stringWidth(date_text, "Helvetica", 16)
        c.drawString((width - date_width) / 2, height - 450, date_text)

        # Certificate Code
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor('#999999'))
        code_text = f"Certificate Code: {certificate_code}"
        code_width = c.stringWidth(code_text, "Helvetica", 12)
        c.drawString((width - code_width) / 2, 100, code_text)

        # Verification URL
        verify_text = f"Verify at: /certificates/verify/{certificate_code}"
        verify_width = c.stringWidth(verify_text, "Helvetica", 12)
        c.drawString((width - verify_width) / 2, 80, verify_text)

        # Finalize PDF
        c.save()
        pdf_buffer.seek(0)

        return pdf_buffer

    def generate_both_formats(
        self,
        student_name: str,
        course_title: str,
        completion_date: datetime,
        certificate_code: str,
        completion_percentage: float = 100.0
    ) -> tuple[io.BytesIO, io.BytesIO]:
        """
        Generate both PNG and PDF formats
        Returns: (png_bytes, pdf_bytes)
        """
        png_bytes = self.generate_certificate_image(
            student_name,
            course_title,
            completion_date,
            certificate_code,
            completion_percentage
        )

        pdf_bytes = self.generate_certificate_pdf(
            student_name,
            course_title,
            completion_date,
            certificate_code,
            completion_percentage
        )

        return png_bytes, pdf_bytes


# Singleton instance
_generator_instance = None

def get_certificate_generator() -> CertificateGenerator:
    """Get CertificateGenerator singleton instance"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = CertificateGenerator()
    return _generator_instance
