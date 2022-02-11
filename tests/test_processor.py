import os, sys

from fastapi.testclient import TestClient
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from unittest.mock import MagicMock, call, patch
import datetime
import mock

sys.path.append('.')

import processor
from config.db import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@mock.patch('config.db.SessionLocal')
@mock.patch('requests.post')
def test_process_event_200_status_code(
        mock_requests_post,
        mock_session_local
    ):
    success_post = MagicMock()
    success_post.status_code = 200
    success_post.content.decode.return_value = 'Content Response'
    mock_requests_post.return_value = success_post
    
    session_local = MagicMock()
    session_local.add = MagicMock()
    session_local.commit = MagicMock()
    mock_session_local.return_value = session_local

    data_to_test = {'notification_id': 1, 'customer_url': 'some_url', 'body': {}, 'status': 'ACTIVE'}
    processor.process_event(
        data_to_test, 
        'some_token'
    )

    assert session_local.add.call_count == 2


@mock.patch('main.upsert_notification')
@mock.patch('config.db.SessionLocal')
@mock.patch('requests.post')
def test_process_event_500_status_code_for_retry(
        mock_requests_post,
        mock_session_local,
        mock_upsert_notification
    ):
    success_post = MagicMock()
    success_post.status_code = 500
    success_post.content.decode.return_value = 'Content Response'
    mock_requests_post.return_value = success_post
    
    session_local = MagicMock()
    session_local.add = MagicMock()
    session_local.commit = MagicMock()
    mock_session_local.return_value = session_local

    mock_upsert_notification.return_value = MagicMock()

    data_to_test = {'notification_id': 1, 'customer_url': 'some_url', 'body': {}, 'status': 'ACTIVE', 'retry_count': 1}
    processor.process_event(
        data_to_test, 
        'some_token'
    )


    assert session_local.add.call_count == 1
    assert mock_upsert_notification.call_args.kwargs['retry_count'] == 2
