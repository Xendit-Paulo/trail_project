from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, ForeignKey, JSON

from config.db import Base
from models.base import BaseTable


class Notification(Base, BaseTable):
    __tablename__ = "notification"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    customer_url_id = Column(Integer, ForeignKey('customer_url.id'))
    body = Column(JSON)
    status = Column(String)
    

class NotificationAudit(Base, BaseTable):
    __tablename__ = "notification_audit"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    notification_id = Column(Integer, ForeignKey('notification.id'))
    body = Column(JSON)
    status = Column(String)
    details = Column(JSON)
    updated_by = Column(String)
