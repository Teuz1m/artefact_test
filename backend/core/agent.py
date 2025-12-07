import os
from typing import Dict, Any, List

from fastmcp import Client
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

from backend.core.prompts import SYSTEM_PROMPT
from backend.utils.logger import setup_logger
from backend.utils.cache import cache


class AIAssistant:
    """Agente principal que decide quando usar ferramentas via MCP."""

    def __init__(self):
        self._mcp_client = Client("http://127.0.0.1:8001/mcp")

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_model_temperature = float(
            os.getenv("OPENAI_MODEL_TEMPERATURE", "0")
        )

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY não configurada no .env")

        os.environ["OPENAI_API_KEY"] = self.openai_api_key

        self.debug = os.getenv("DEBUG", "false").lower() in (
            "true", "1", "yes"
        )
        self.logger = setup_logger(__name__, debug=self.debug)

        self.tools: List[Tool] = []
        self.agent = None

    async def initialize(self):
        """
        Inicializa agente LangGraph conectando ao MCP Server.
        Carrega ferramentas disponíveis
        """
        try:
            self.logger.info("Inicializando agente LangGraph + MCP Server")

            self.llm = ChatOpenAI(
                model=self.openai_model_name,
                temperature=self.openai_model_temperature,
            )

            async with self._mcp_client:
                tools = await self._mcp_client.list_tools()
                self.logger.info(
                    f"Conectado ao MCP Server. Tools disponíveis: "
                    f"{len(tools)}"
                )

                for mcp_tool in tools:
                    self.logger.debug(f"Tool carregada: {mcp_tool.name}")
                    langchain_tool = self._create_langchain_tool(mcp_tool)
                    self.tools.append(langchain_tool)

            if not self.tools:
                raise RuntimeError("Nenhuma tool disponível no MCP Server!")

            self.agent = create_react_agent(self.llm, self.tools)

            self.logger.info("Agente LangGraph inicializado com sucesso")

        except Exception as e:
            self.logger.error(
                f"Erro ao inicializar agente: {str(e)}",
                exc_info=True
            )
            raise

    def _create_langchain_tool(self, mcp_tool) -> Tool:
        """
        Converte ferramenta MCP para LangChain Tool.
        Args:
            mcp_tool: Ferramenta obtida do MCP Server
        """
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description or f"Ferramenta {tool_name}"

        async def tool_func(expression: str) -> str:
            try:
                self.logger.debug(
                    f"Executando MCP Tool '{tool_name}' com argumento: "
                    f"{expression}"
                )

                if tool_name == "calculator":
                    arguments = {"expression": expression}
                elif tool_name == "get_weather":
                    if "," in expression:
                        city, country = expression.split(",", 1)
                        arguments = {"city": city.strip(
                        ), "country_code": country.strip()}
                    else:
                        arguments = {"city": expression.strip(),
                                     "country_code": "BR"}
                else:
                    arguments = {"expression": expression}

                async with self._mcp_client:
                    result = await self._mcp_client.call_tool(
                        tool_name,
                        arguments=arguments
                    )

                self.logger.debug(
                    f"Resultado MCP ({tool_name}): {result}"
                )

                if isinstance(result, dict):
                    if "formatted" in result:
                        return result["formatted"]
                    if "result" in result:
                        return f"{expression} = {result['result']}"
                    if "error" in result:
                        return f"Erro: {result['error']}"
                    return str(result)

                return str(result)

            except Exception as e:
                error_msg = f"Erro ao executar tool {tool_name}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return error_msg

        return Tool(
            name=tool_name,
            description=tool_description,
            func=tool_func,
            coroutine=tool_func
        )

    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processa query do usuário.
        Reinicializa agente se necessário.
        Args:
            query: Pergunta do usuário

        """
        try:
            if not self.agent:
                await self.initialize()

            cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", 600))
            cache_key = cache._make_key("llm_query", query)
            cached_response = cache.get(cache_key)

            if cached_response:
                self.logger.info("Resposta retornada do cache")
                cache.increment_metric("cache_hit_llm")
                return cached_response

            cache.increment_metric("cache_miss_llm")

            self.logger.info(f"Processando query do usuário: {query}")

            result = await self.agent.ainvoke(
                {
                    "messages": [
                        ("system", SYSTEM_PROMPT),
                        ("user", query)
                    ]
                }
            )

            tools_used = []

            if "messages" in result:
                tool_calls = [
                    msg for msg in result["messages"]
                    if hasattr(msg, 'tool_calls') and msg.tool_calls
                ]

                if tool_calls:
                    tools_used = []
                    for msg in tool_calls:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                if isinstance(tc, dict):
                                    tool_name = tc.get('name', 'unknown')
                                else:
                                    tool_name = getattr(tc, 'name', str(tc))
                                tools_used.append(tool_name)

                    if tools_used:
                        self.logger.info(
                            f"Tools utilizadas: {', '.join(tools_used)}"
                        )
                        for tool_name in tools_used:
                            cache.increment_metric(f"tool_usage:{tool_name}")
                else:
                    self.logger.info(
                        "Nenhuma tool utilizada (resposta direta do LLM)"
                    )

            self.logger.info("Resposta gerada com sucesso")

            response = result.get("output") or result.get("messages")[
                -1].content

            response_data = {
                "success": True,
                "query": query,
                "response": response,
                "tools_used": tools_used,
                "intermediate_steps": []
            }

            cache.set(cache_key, response_data, ttl=cache_ttl)

            return response_data

        except Exception as e:
            self.logger.error(
                f"Erro ao processar query: {str(e)}",
                exc_info=True
            )

            return {
                "success": False,
                "query": query,
                "response": None,
                "error": str(e),
            }
