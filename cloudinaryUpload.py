# cloudinary_upload.py
import cloudinary.uploader

def upload_pdf_to_cloudinary(pdf_buffer, invoice_number: str) -> str:
    result = cloudinary.uploader.upload(
        pdf_buffer,
        resource_type="raw",   # IMPORTANT for PDFs
        public_id=f"invoices/invoice_{invoice_number}",
        format="pdf",
        overwrite=True
    )

    return result["secure_url"]
