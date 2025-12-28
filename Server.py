from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from datetime import datetime
from math import ceil
from pymongo import DESCENDING
from bson import ObjectId

from database import fs, invoice_collection, get_next_invoice_number
from models import InvoiceRequest
from InvoiceMaker import generate_invoice


app = FastAPI(title="POS Invoice Server")


# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
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

    # Generate PDF (in-memory)
    pdf_file = generate_invoice(invoice_data)

    # Store PDF in GridFS
    pdf_id = fs.put(
        pdf_file,
        filename=f"invoice_{invoice_number}.pdf",
        contentType="application/pdf"
    )

    # Store invoice metadata
    invoice_collection.insert_one({
        "invoice_number": invoice_number,
        "customer_name": payload.customer_name,
        "customer_address": payload.customer_address,
        "items": invoice_data["items"],
        "payment_mode": payload.payment_mode,
        "date": invoice_data["date"],
        "created_at": datetime.utcnow(),
        "pdf_id": pdf_id
    })

    return {
        "invoice_number": invoice_number,
        "download_url": f"/invoice/{invoice_number}/pdf",
        "message": "Invoice created successfully"
    }


# ---------------- DOWNLOAD PDF ----------------
@app.get("/invoice/{invoice_number}/pdf")
def download_invoice_pdf(invoice_number: str):
    invoice = invoice_collection.find_one(
        {"invoice_number": invoice_number}
    )

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    grid_out = fs.get(invoice["pdf_id"])

    pdf_bytes = grid_out.read()  # ✅ IMPORTANT

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="invoice_{invoice_number}.pdf"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        }
    )



# ---------------- LIST INVOICES (PAGINATION) ----------------
@app.get("/invoices")
def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    skip = (page - 1) * limit

    total = invoice_collection.count_documents({})

    cursor = (
        invoice_collection
        .find({}, {"pdf_id": 0})  # exclude heavy field
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
        .find(query, {"pdf_id": 0})
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
