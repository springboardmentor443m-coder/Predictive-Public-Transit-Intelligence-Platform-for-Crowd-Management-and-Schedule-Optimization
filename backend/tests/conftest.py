import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Shared in-memory SQLite database URI
TEST_DB_URL = "sqlite:///file:testdb?mode=memory&cache=shared"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-testing-purposes"

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.core.security import create_access_token

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False, "uri": True}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


from unittest.mock import patch, AsyncMock

@pytest.fixture(scope="function", autouse=True)
def mock_mta_network_calls():
    with patch("app.services.live_data.ingestion.mta_provider.fetch_all_normalized_entities", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.live_data.ingestion.ingestion_service.start") as mock_start, \
         patch("app.services.live_data.ingestion.ingestion_service.stop") as mock_stop:
        mock_fetch.return_value = ([], [], [])
        yield mock_fetch

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session) -> Generator:
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session) -> User:
    user = UserService.get_by_email(db_session, "admin@test.io")
    if not user:
        user = UserService.create(
            db_session,
            UserCreate(
                email="admin@test.io",
                name="Test Admin",
                password="TestPassword123!",
                role=UserRole.ADMIN,
                is_active=True
            )
        )
    return user


@pytest.fixture
def operator_user(db_session) -> User:
    user = UserService.get_by_email(db_session, "operator@test.io")
    if not user:
        user = UserService.create(
            db_session,
            UserCreate(
                email="operator@test.io",
                name="Test Operator",
                password="TestPassword123!",
                role=UserRole.OPERATOR,
                is_active=True
            )
        )
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(subject=admin_user.id, role=admin_user.role.value)


@pytest.fixture
def operator_token(operator_user: User) -> str:
    return create_access_token(subject=operator_user.id, role=operator_user.role.value)


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def operator_headers(operator_token: str) -> dict:
    return {"Authorization": f"Bearer {operator_token}"}
