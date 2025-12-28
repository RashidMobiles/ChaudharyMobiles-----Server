from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from math import ceil
from pymongo import DESCENDING

from database import invoice_collection, get_next_invoice_number
from models import InvoiceRequest
from InvoiceMaker import generate_invoice
from pdf import compress_pdf
from cloudinaryUpload import upload_pdf

import cloudinary  # noqa: F401 (just loads config)

app = FastAPI(title="POS Invoice Server")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HELPERS ----------------
def serialize_invoice(invoice: dict) -> dict:
    invoice["_id"] = str(invoice["_id"])
    return invoice

# ---------------- CREATE INVOICE ----------------
@app.post("/invoice")
def create_invoice(payload: InvoiceRequest):
    invoice_number = get_next_invoice_number()

    invoice_data = {
        "invoice_no": invoice_number,
        "date": datetime.now().strftime("%d-%m-%Y"),
        "customer": {
            "name": payload.customer_name,
            "address": payload.customer_address,
        },
        "items": [item.model_dump() for item in payload.items],
        "payment": {
            "mode": payload.payment_mode
        }
    }

    # 1️⃣ Generate PDF (in memory)
    pdf_buffer = generate_invoice(invoice_data)

    # 2️⃣ Compress PDF (text-only → very small)
    compressed_pdf = compress_pdf(pdf_buffer)

    # 3️⃣ Upload to Cloudinary
    pdf_url = upload_pdf(compressed_pdf, invoice_number)

    # 4️⃣ Store metadata ONLY
    invoice_collection.insert_one({
        "invoice_number": invoice_number,
        "customer_name": payload.customer_name,
        "customer_address": payload.customer_address,
        "items": invoice_data["items"],
        "payment_mode": payload.payment_mode,
        "date": invoice_data["date"],
        "created_at": datetime.utcnow(),
        "pdf_url": pdf_url
    })

    return {
        "invoice_number": invoice_number,
        "pdf_url": pdf_url,
        "message": "Invoice created successfully"
    }

# ---------------- LIST INVOICES ----------------
@app.get("/invoices")
def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    skip = (page - 1) * limit
    total = invoice_collection.count_documents({})

    cursor = (
        invoice_collection
        .find({})
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    invoices = [serialize_invoice(inv) for inv in cursor]

    return {
        "invoices": invoices,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": ceil(total / limit) if total else 1
    }

# ---------------- SEARCH INVOICES ----------------
@app.get("/invoices/search")
def search_invoices(
    q: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    skip = (page - 1) * limit

    query = {
        "$or": [
            {"invoice_number": {"$regex": q, "$options": "i"}},
            {"customer_name": {"$regex": q, "$options": "i"}},
        ]
    }

    total = invoice_collection.count_documents(query)

    cursor = (
        invoice_collection
        .find(query)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    invoices = [serialize_invoice(inv) for inv in cursor]

    return {
        "invoices": invoices,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": ceil(total / limit) if total else 1
    }
