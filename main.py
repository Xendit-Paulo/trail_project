from fastapi import FastAPI

from models import customer_url
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, UploadFile
import redis
import json

from config.db import get_db, Base, engine
from models.exceptions import InvalidField
from models.customer_url import CustomerUrl
from schema.customer_url import CustomerUrlBase
from models.notifications import Notification, NotificationAudit
from schema.notification import NotificationBase
from utils.exception_handler import invalid_field_exception_handler
from utils.enums import NotificationStatus

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_exception_handler(InvalidField, invalid_field_exception_handler)

r = redis.Redis()

@app.post('/customer_url')
def post_customer_url(
        payload: CustomerUrlBase, 
        db: Session=Depends(get_db)
    ):

    existing_customer_url = db.query(CustomerUrl).filter(
        CustomerUrl.customer_id == payload.customer_id
        ).first()

    if existing_customer_url:
        raise InvalidField('customer_id', '400', 'Customer_id already exists')

    else:
        customer_url = CustomerUrl(**payload.dict())
        db.add(customer_url)
        db.commit()
        db.refresh(customer_url)
        return customer_url

@app.post('/notification')
def post_notification(
        payload: NotificationBase, 
        db: Session=Depends(get_db)
    ):
    existing_customer = db.query(CustomerUrl).filter(
        CustomerUrl.customer_id == payload.customer_id
        ).first()
    if not existing_customer:
        raise InvalidField('customer_id', '400', 'Customer_id does not exist')
    
    notification_object = upsert_notification(
        "service", 
        db, 
        r, 
        customer_url_id=existing_customer.id, 
        body=payload.body, 
        status=NotificationStatus.INITIALIZED, 
    )

    return notification_object


@app.post('/notification/{notification_id}/retry')
def post_retry(
        notification_id, 
        db: Session=Depends(get_db)
    ):
    notif_data = db.query(Notification).filter(Notification.id==notification_id).first()
    if not notif_data:
        raise InvalidField('notification_id', '400', 'Notification id does not exist')

    # if notif_data.status != NotificationStatus.FAILED:
    #     raise InvalidField('notification_id', '400', 'Notification has not yet failed')

    notif_data = upsert_notification(
        'service', 
        db, 
        r, 
        notification_id=notif_data.id,
        status=NotificationStatus.INITIALIZED
    )

    return notif_data


def upsert_notification(
        updated_by,
        db, 
        redis, 
        details=None, 
        notification_id=None, 
        customer_url_id=None, 
        body=None, 
        status=None, 
        push_to_redis=True,
        retry_count=1
    ):
    if notification_id:
        notification = db.query(Notification).filter(Notification.id==notification_id).first()
        setattr(notification, 'status', status)
        db.flush()
        customer_url_id = notification.customer_url_id
    else:
        notification = Notification(
            customer_url_id=customer_url_id,
            body=body,
            status=status
        )
        db.add(notification)
        db.flush()

    notif_audit = NotificationAudit(
        notification_id=notification.id,
        body=notification.body,
        status=notification.status,
        details=details,
        updated_by=updated_by
    )
    db.add(notif_audit)

    customer_details = db.query(CustomerUrl).filter(CustomerUrl.id==customer_url_id).first()

    if push_to_redis:
        redis_data = {
            'status': notification.status,
            'body': notification.body,
            'customer_id': customer_details.customer_id,
            'customer_url': customer_details.url,
            'notification_id': notification.id,
            'retry_count': retry_count
        }
        redis.lpush('notification_queue', json.dumps(redis_data))
    db.commit()
    db.refresh(notification)

    return notification