import pytest
import mysql.connector
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import os



# Load test environment variables
load_dotenv('.env.test')

from app.main import app
from app.core.database import get_db
from app.core.security import hash_password

# ----------------------------------------------------------------------
# Test database connection
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def db_connection():
    """Create a connection to the test database."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "3306"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_inventory_test")
    )
    yield conn
    conn.close()

@pytest.fixture(scope="function", autouse=True)
def clean_db(db_connection):
    """Truncate all tables before each test (except lookup tables)."""
    cursor = db_connection.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    tables = [
        "audit_log", "replenishment_suggestions", "stock_movements",
        "sale_line_items", "sale_transactions", "user_roles", "users",
        "products", "suppliers", "categories", "api_keys", "webhooks",
        "webhook_deliveries", "system_settings"
    ]
    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table}")
        except:
            pass
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    db_connection.commit()
    cursor.close()
    yield

# ----------------------------------------------------------------------
# Override the get_db dependency to use test DB
# ----------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session(db_connection):
    """Yield a connection for the test."""
    yield db_connection

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden dependency."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, base_url="http://test")
    app.dependency_overrides.clear()

# ----------------------------------------------------------------------
# Sample data fixtures
# ----------------------------------------------------------------------
@pytest.fixture(scope="function")
def sample_admin(db_session):
    """Create an admin user and return its ID, username, password."""
    from app.models.user import create_user
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"test_admin_{unique_id}",
        "email": f"admin_{unique_id}@example.com",
        "password": "adminpass",
        "role": "admin"
    }
    user_id = create_user(db_session, user_data)
    return user_id, user_data["username"], user_data["password"]

@pytest.fixture(scope="function")
def sample_manager(db_session):
    """Create a manager user."""
    from app.models.user import create_user
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"test_manager_{unique_id}",
        "email": f"manager_{unique_id}@example.com",
        "password": "managerpass",
        "role": "manager"
    }
    user_id = create_user(db_session, user_data)
    return user_id, user_data["username"], user_data["password"]

@pytest.fixture(scope="function")
def sample_clerk(db_session):
    """Create a clerk user."""
    from app.models.user import create_user
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"test_clerk_{unique_id}",
        "email": f"clerk_{unique_id}@example.com",
        "password": "clerkpass",
        "role": "clerk"
    }
    user_id = create_user(db_session, user_data)
    return user_id, user_data["username"], user_data["password"]

@pytest.fixture(scope="function")
def sample_product(db_session):
    """Create a sample product and return its SKU."""
    from app.models.product import create_product
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    product_data = {
        "sku": f"TEST{unique_id}",
        "barcode": f"123456{unique_id}",
        "name": f"Test Product {unique_id}",
        "cost_price": 50.00,
        "selling_price": 75.00,
        "quantity_in_stock": 100,
        "reorder_threshold": 10,
        "is_active": True
    }
    create_product(db_session, product_data)
    return product_data["sku"]

@pytest.fixture(scope="function")
def auth_headers_admin(client, sample_admin):
    user_id, username, password = sample_admin
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def auth_headers_manager(client, sample_manager):
    user_id, username, password = sample_manager
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def auth_headers_clerk(client, sample_clerk):
    user_id, username, password = sample_clerk
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}