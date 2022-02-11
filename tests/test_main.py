import os, sys

from fastapi.testclient import TestClient
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from unittest.mock import MagicMock, call, patch
import datetime
sys.path.append('.')


from config.db import Base
from main import app, get_db

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


FAKE_TIME = datetime.datetime.now()

@pytest.fixture
def patch_datetime_now(monkeypatch):

    class mydatetime:
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr(datetime, 'datetime', mydatetime)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_post_customer_url(
        patch_datetime_now,
        test_db
    ):
    response = client.post(
        '/customer_url', 
        json={'customer_id': 104, "url": "https://some_url.com"}
    )
    assert response.status_code == 200
    assert response.json() == {
        'created_at': datetime.date.today().strftime('%Y-%m-%dT00:00:00'),
        'customer_id': 104,
        'deleted_at': None,
        'id': 1,
        'is_deleted': False,
        'updated_at': None,
        'url': 'https://some_url.com'
        }