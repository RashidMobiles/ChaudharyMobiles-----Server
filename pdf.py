# pdf_utils.py
import pikepdf
from io import BytesIO

def compress_pdf(input_buffer: BytesIO) -> BytesIO:
    input_buffer.seek(0)

    pdf = pikepdf.open(input_buffer)
    output_buffer = BytesIO()

    pdf.save(
        output_buffer,
        compress_streams=True,
        optimize_streams=True
    )

    output_buffer.seek(0)
    return output_buffer
