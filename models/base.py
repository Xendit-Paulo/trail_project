from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer


class BaseTable(object):
    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, onupdate=datetime.now())
    deleted_at = Column(DateTime)

    is_deleted = Column(Boolean, default=False)
