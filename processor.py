import gevent
import redis
import json
import requests
from models.notifications import Notification, NotificationAudit
from models.customer_url import CustomerUrl
from config.db import get_db, Base, engine, SessionLocal
from utils.enums import NotificationStatus
from sqlalchemy.orm import Session
from main import upsert_notification

r = redis.Redis()
db = SessionLocal()

def consume_event(token):
    print('Starting')
    print(token)

    while True:
        data = r.rpop('notification_queue')
        print(data)
        if not data:
            gevent.sleep(2)
        else:
            data = json.loads(data)

            notif_db_data = db.query(Notification).join(CustomerUrl).filter(Notification.id==data['notification_id']).first()
            setattr(notif_db_data, 'status', NotificationStatus.ACTIVE)
            db.flush()
            db.add(NotificationAudit(
                notification_id=notif_db_data.id, 
                body=notif_db_data.body,
                status=notif_db_data.status,
                updated_by='processor'
            ))
            db.commit()

            headers = {
                'Authentication': f'Bearer {token}'
            }
            result = requests.post(url=data['customer_url'], data=data['body'], headers=headers)

            if result.status_code == 200:
                setattr(notif_db_data, 'status', NotificationStatus.COMPLETED)
                db.add(NotificationAudit(
                    notification_id=notif_db_data.id, 
                    body=notif_db_data.body,
                    status=notif_db_data.status,
                    details=result.content.decode('utf-8'),
                    updated_by='processor'
                ))
                db.commit()
            else:
                if data['retry_count'] < 3:
                    data['retry_count']+=1
                    upsert_notification(
                        'processor',
                        db, 
                        r, 
                        status=NotificationStatus.ERROR,
                        details=result.content.decode('utf-8'), 
                        notification_id=notif_db_data.id, 
                        push_to_redis=True,
                        retry_count=data['retry_count']
                    )
                else:
                    upsert_notification(
                        'processor',
                        db, 
                        r, 
                        status=NotificationStatus.FAILED,
                        details=result.content.decode('utf-8'), 
                        notification_id=notif_db_data.id, 
                        push_to_redis=False
                    )

def generate_token():
    return "some_token"

if __name__ == "__main__":
    running = []
    print('hello')
    token=generate_token()
    running.append(gevent.spawn(consume_event(token)))
    gevent.joinall(running)