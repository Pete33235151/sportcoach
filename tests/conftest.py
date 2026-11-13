import os
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app_with_temp_db():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SPORTCOACH_DATABASE_URL"] = "sqlite:///" + tmp + "/test.db"
        os.environ["SPORTCOACH_DEMO_MODE"] = "true"
        from app.main import app
        yield app


@pytest.fixture
def client(app_with_temp_db):
    with TestClient(app_with_temp_db) as c:
        yield c
