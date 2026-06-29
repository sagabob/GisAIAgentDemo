import pytest

from api_client import GisApiClient
from tools import execute_tool


def test_unknown_tool_raises():
    client = GisApiClient(base_url="https://example.test")
    try:
        with pytest.raises(ValueError, match="Unknown tool"):
            execute_tool(client, "missing_tool", {})
    finally:
        client.close()
