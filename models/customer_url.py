from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String

from config.db import Base
from models.base import BaseTable


class CustomerUrl(Base, BaseTable):
    __tablename__ = "customer_url"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    customer_id = Column(Integer)
    url = Column(String)