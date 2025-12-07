import os
import pytest
import tempfile
import shutil


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Configura ambiente para testes.
    """
    test_log_dir = tempfile.mkdtemp(prefix="test_logs_")

    os.environ["LOG_DIR"] = test_log_dir
    os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-not-real"
    os.environ["REDIS_ENABLED"] = "false"
    os.environ["DEBUG"] = "false"

    print(f"\n[Setup] Logs de teste em: {test_log_dir}")

    yield

    if os.path.exists(test_log_dir):
        shutil.rmtree(test_log_dir)
        print(f"[Cleanup] Removido: {test_log_dir}")


@pytest.fixture(scope="function")
def clean_metrics():
    """
    Limpa métricas Redis.
    """
    from backend.utils.cache import cache

    yield


from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_agent():
    """
    Mock do AIAssistant para testes unitários
    """
    async def mock_process_query(query: str):
        return {
            "success": True,
            "query": query,
            "response": "Brasília é a capital do Brasil.",
            "tools_used": [],
            "intermediate_steps": []
        }

    mock_agent_instance = AsyncMock()
    mock_agent_instance.process_query = mock_process_query
    mock_agent_instance.initialize = AsyncMock()

    with patch('backend.api.routes.get_agent') as mock_get_agent:
        mock_get_agent.return_value = mock_agent_instance
        yield mock_agent_instance
