from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, AnyUrl


class CustomerUrlBase(BaseModel):
    customer_id: int
    url: AnyUrl
