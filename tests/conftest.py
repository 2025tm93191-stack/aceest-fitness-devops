import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def member(client):
    """A saved client used by the progress / workout / membership tests."""
    client.post("/api/clients", json={"name": "Arjun", "weight": 80, "program": "FL"})
    return "Arjun"
