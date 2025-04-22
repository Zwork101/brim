from quart.typing import TestAppProtocol, TestClientProtocol
from config import TestingConfig
from factory import create_app

import pytest

@pytest.fixture(scope="package")
def app() -> TestAppProtocol:
    return create_app(TestingConfig).test_app()


@pytest.fixture(scope="package")
def client() -> TestClientProtocol:
    return create_app(TestingConfig).test_client()
