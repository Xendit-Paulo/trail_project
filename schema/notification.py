from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class NotificationBase(BaseModel):
    customer_id: int
    body: dict
