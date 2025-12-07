from fastapi import APIRouter, HTTPException
from backend.api.models import QueryRequest, QueryResponse
from backend.core.agent import AIAssistant
from backend.utils.cache import cache

router = APIRouter(prefix="/v1")

_agent = None


async def get_agent() -> AIAssistant:
    """Retorna instância do agente"""
    global _agent
    if _agent is None:
        _agent = AIAssistant()
        await _agent.initialize()
    return _agent


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Processa uma query do usuário

    O agente decide automaticamente se deve usar o MCP da calculadora,do clima ou responder diretamente
    """
    try:
        agent = await get_agent()
        result = await agent.process_query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Assistant Backend"}


@router.get("/metrics")
async def get_metrics():
    """Retorna métricas de uso do sistema."""
    return {
        "cache": {
            "llm": {
                "hits": cache.get_metric("cache_hit_llm"),
                "misses": cache.get_metric("cache_miss_llm"),
            },
            "weather": {
                "hits": cache.get_metric("cache_hit_weather"),
                "misses": cache.get_metric("cache_miss_weather")
            }
        },

        "tools_usage": {
            "calculator": cache.get_metric("tool_usage:calculator"),
            "weather": cache.get_metric("tool_usage:get_weather")
        }
    }
