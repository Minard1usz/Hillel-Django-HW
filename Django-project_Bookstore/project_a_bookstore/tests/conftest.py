import pytest
from unittest.mock import MagicMock
from django.db import connection


@pytest.fixture(autouse=True)
def mock_stripe(monkeypatch):
    mock_session = MagicMock()
    mock_session.id = "cs_test_12345"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_12345"

    try:
        import stripe

        monkeypatch.setattr(
            stripe.checkout.Session, "create", MagicMock(return_value=mock_session)
        )
    except ImportError:
        pass

    return mock_session


@pytest.fixture(autouse=True)
def close_db_connections():
    yield
    connection.close()
