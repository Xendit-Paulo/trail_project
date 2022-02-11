import os
import gevent
import redis
import json
import requests
from models.notifications import Notification, NotificationAudit
from models.customer_url import CustomerUrl
from config import db
from utils.enums import NotificationStatus
from sqlalchemy.orm import Session
import main

r = redis.Redis()

def consume_event(token):
    print('Starting')

    while True:
        data = r.rpop('notification_queue')
        print(data)
        if not data:
            gevent.sleep(2)
        else:
            data = json.loads(data)
            process_event(data, token)


def process_event(data, token):
    connection = db.SessionLocal()

    notif_db_data = connection.query(Notification).join(CustomerUrl).filter(Notification.id==data['notification_id']).first()
    setattr(notif_db_data, 'status', NotificationStatus.ACTIVE)
    connection.flush()
    connection.add(NotificationAudit(
        notification_id=notif_db_data.id, 
        body=notif_db_data.body,
        status=notif_db_data.status,
        updated_by='processor'
    ))
    connection.commit()

    headers = {
        'Authentication': f'Bearer {token}'
    }
    result = requests.post(url=data['customer_url'], data=data['body'], headers=headers)

    if result.status_code == 200:
        setattr(notif_db_data, 'status', NotificationStatus.COMPLETED)
        connection.add(NotificationAudit(
            notification_id=notif_db_data.id, 
            body=notif_db_data.body,
            status=notif_db_data.status,
            details=result.content.decode('utf-8'),
            updated_by='processor'
        ))
        connection.commit()
    else:
        if data['retry_count'] < 3:
            data['retry_count']+=1
            main.upsert_notification(
                'processor',
                connection, 
                r, 
                status=NotificationStatus.ERROR,
                details=result.content.decode('utf-8'), 
                notification_id=notif_db_data.id, 
                push_to_redis=True,
                retry_count=data['retry_count']
            )
        else:
            main.upsert_notification(
                'processor',
                connection, 
                r, 
                status=NotificationStatus.FAILED,
                details=result.content.decode('utf-8'), 
                notification_id=notif_db_data.id, 
                push_to_redis=False
            )



def generate_token():
    request_body = {
        'client_id': os.getenv('CLIENT_NOTIFICATION_CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_NOTIFICATION_CLIENT_SECRET')
    }
    response = requests.post('https://httpstat.us/200', data=request_body)
    response.content
    return "some_token"

if __name__ == "__main__":
    running = []
    token=generate_token()
    running.append(gevent.spawn(consume_event(token)))
    gevent.joinall(running)