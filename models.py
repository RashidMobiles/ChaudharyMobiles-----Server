from pydantic import BaseModel, model_validator
from typing import List, Optional, Literal


ItemCategory = Literal["Phone", "Charger"]
PaymentMode = Literal["Cash", "Online", "EMI"]


class InvoiceItem(BaseModel):
    category: ItemCategory
    item_name: str
    quantity: int
    price: float

    imei_1: Optional[str] = None
    imei_2: Optional[str] = None

    charger_included: Optional[bool] = False
    charger_name: Optional[str] = None
    charger_serial_number: Optional[str] = None

    serial_number: Optional[str] = None

    @model_validator(mode="after")
    def validate_logic(self):
        if self.category == "Phone":
            if not self.imei_1:
                raise ValueError("Phone requires IMEI 1")

            if self.charger_included:
                if not self.charger_name or not self.charger_serial_number:
                    raise ValueError("Charger details required if charger included")

        if self.category == "Charger":
            if not self.serial_number:
                raise ValueError("Charger requires serial number")

        return self


class InvoiceRequest(BaseModel):
    customer_name: str
    customer_address: str
    items: List[InvoiceItem]
    payment_mode: PaymentMode
