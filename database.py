from pymongo import MongoClient, ReturnDocument
import gridfs
import os

# MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient("mongodb+srv://ramizanas6_db_user:Badmosh9517@rashidmobilesdata.iyygq7p.mongodb.net/?appName=RashidMobilesData")
db = client["posdb"]

fs = gridfs.GridFS(db)
invoice_collection = db["invoices"]
counter_collection = db["counters"]


def get_next_invoice_number():
    counter = counter_collection.find_one_and_update(
        {"_id": "invoice"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return str(counter["seq"]).zfill(7)
