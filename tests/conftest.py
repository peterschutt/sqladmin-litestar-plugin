import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> object:
    return "asyncio"
