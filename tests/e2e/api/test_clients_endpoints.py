"""End-to-end tests for Client API endpoints."""
from decimal import Decimal
from uuid import uuid4

import pytest  # type: ignore
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.infrastructure.database.models.client import Client as ClientModel  # type: ignore
from app.infrastructure.database.models.base import Base  # type: ignore


@pytest.fixture
async def test_client(async_engine, async_session):
    """Create a test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
class TestCreateClientEndpoint:
    """Test POST /api/v1/clients/ endpoint."""

    async def test_create_client_success(self, test_client, async_session):
        """Should create client and return 201."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678",
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan@example.com",
            "credit_limit": "5000.00",
            "tags": ["vip", "mayorista"]
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["phone"] == "+54 9 11 1234 5678"
        assert data["phone_normalized"] == "+5491112345678"
        assert data["first_name"] == "Juan"
        assert data["last_name"] == "Pérez"
        assert data["full_name"] == "Juan Pérez"
        assert data["email"] == "juan@example.com"
        assert Decimal(data["credit_limit"]) == Decimal("5000.00")
        assert Decimal(data["current_balance"]) == Decimal("0")
        assert Decimal(data["available_credit"]) == Decimal("5000.00")
        assert data["owes_money"] is False
        assert data["status"] == "active"
        assert "vip" in data["tags"]
        assert data["id"] is not None

    async def test_create_client_minimal_data(self, test_client, async_session):
        """Should create client with only required fields."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["phone"] == "+54 9 11 1234 5678"
        assert data["credit_limit"] == "0"

    async def test_create_client_duplicate_phone_returns_400(self, test_client, async_session):
        """Should return 400 when phone already exists."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678",
            "first_name": "First"
        }

        # Create first client
        response1 = await test_client.post("/api/v1/clients/", json=request_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create duplicate
        request_data["first_name"] = "Second"
        response2 = await test_client.post("/api/v1/clients/", json=request_data)

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response2.json()["detail"].lower()

    async def test_create_client_invalid_phone_returns_400(self, test_client, async_session):
        """Should return 400 for invalid phone number."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "invalid-phone"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_client_missing_required_field_returns_422(self, test_client):
        """Should return 422 when required field is missing."""
        request_data = {
            "first_name": "Juan"
            # Missing pharmacy_id and phone
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_client_invalid_email_returns_400(self, test_client, async_session):
        """Should return 400 for invalid email format."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678",
            "email": "invalid-email"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_create_client_normalizes_phone(self, test_client, async_session):
        """Should normalize phone number in response."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "54-9-11-1234-5678"  # Different format
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["phone_normalized"] == "+5491112345678"


@pytest.mark.asyncio
class TestGetClientEndpoint:
    """Test GET /api/v1/clients/{client_id} endpoint."""

    async def test_get_client_success(self, test_client, async_session):
        """Should return client data."""
        pharmacy_id = str(uuid4())

        # Create client first
        create_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678",
            "first_name": "Juan",
            "last_name": "Pérez"
        }
        create_response = await test_client.post("/api/v1/clients/", json=create_data)
        created_client = create_response.json()

        # Get client
        response = await test_client.get(f"/api/v1/clients/{created_client['id']}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_client["id"]
        assert data["first_name"] == "Juan"
        assert data["last_name"] == "Pérez"

    async def test_get_client_not_found_returns_404(self, test_client):
        """Should return 404 for non-existent client."""
        non_existent_id = str(uuid4())

        response = await test_client.get(f"/api/v1/clients/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_get_client_invalid_uuid_returns_422(self, test_client):
        """Should return 422 for invalid UUID format."""
        response = await test_client.get("/api/v1/clients/invalid-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestClientEndpointsIntegration:
    """Integration tests for multiple endpoint interactions."""

    async def test_create_and_retrieve_client(self, test_client, async_session):
        """Should create client and retrieve it."""
        pharmacy_id = str(uuid4())

        # Create
        create_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678",
            "first_name": "Integration",
            "last_name": "Test",
            "credit_limit": "10000.00"
        }
        create_response = await test_client.post("/api/v1/clients/", json=create_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        created = create_response.json()

        # Retrieve
        get_response = await test_client.get(f"/api/v1/clients/{created['id']}")
        assert get_response.status_code == status.HTTP_200_OK
        retrieved = get_response.json()

        # Verify data matches
        assert retrieved["id"] == created["id"]
        assert retrieved["first_name"] == "Integration"
        assert retrieved["last_name"] == "Test"
        assert Decimal(retrieved["credit_limit"]) == Decimal("10000.00")

    async def test_create_multiple_clients_same_pharmacy(self, test_client, async_session):
        """Should create multiple clients for same pharmacy."""
        pharmacy_id = str(uuid4())

        # Create first client
        data1 = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1111 1111",
            "first_name": "Client1"
        }
        response1 = await test_client.post("/api/v1/clients/", json=data1)
        assert response1.status_code == status.HTTP_201_CREATED

        # Create second client
        data2 = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 2222 2222",
            "first_name": "Client2"
        }
        response2 = await test_client.post("/api/v1/clients/", json=data2)
        assert response2.status_code == status.HTTP_201_CREATED

        # Both should have different IDs
        client1 = response1.json()
        client2 = response2.json()
        assert client1["id"] != client2["id"]

    async def test_create_clients_different_pharmacies_same_phone(self, test_client, async_session):
        """Should allow same phone for different pharmacies."""
        pharmacy_id_1 = str(uuid4())
        pharmacy_id_2 = str(uuid4())
        phone = "+54 9 11 1234 5678"

        # Create in pharmacy 1
        data1 = {
            "pharmacy_id": pharmacy_id_1,
            "phone": phone,
            "first_name": "Pharmacy1Client"
        }
        response1 = await test_client.post("/api/v1/clients/", json=data1)
        assert response1.status_code == status.HTTP_201_CREATED

        # Create in pharmacy 2 (should succeed)
        data2 = {
            "pharmacy_id": pharmacy_id_2,
            "phone": phone,
            "first_name": "Pharmacy2Client"
        }
        response2 = await test_client.post("/api/v1/clients/", json=data2)
        assert response2.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
class TestClientEndpointsValidation:
    """Test validation rules in endpoints."""

    async def test_credit_limit_must_be_non_negative(self, test_client, async_session):
        """Should reject negative credit limit."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678",
            "credit_limit": "-1000.00"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_whatsapp_opted_in_defaults_to_true(self, test_client, async_session):
        """Should default whatsapp_opted_in to True."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["whatsapp_opted_in"] is True

    async def test_country_defaults_to_ar(self, test_client, async_session):
        """Should default country to AR."""
        pharmacy_id = str(uuid4())

        request_data = {
            "pharmacy_id": pharmacy_id,
            "phone": "+54 9 11 1234 5678"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["country"] == "AR"
