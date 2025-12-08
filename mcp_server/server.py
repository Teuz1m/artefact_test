import ast
import math
import operator
import os
import sys
import httpx
from fastmcp import FastMCP

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


from backend.utils.cache import cache
mcp = FastMCP(
    name="AI Assistant Calculator",
    host="0.0.0.0",
    port=8001,
    streamable_http_path="/mcp",
    debug=False
)

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_ast_node(node):
    """Avalia um nó AST de forma segura (sem eval)."""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        op = OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(
                f"Operador não suportado: {type(node.op).__name__}")
        return op(_eval_ast_node(node.left), _eval_ast_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        op = OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(
                f"Operador unário não suportado: {type(node.op).__name__}")
        return op(_eval_ast_node(node.operand))
    else:
        raise ValueError(
            f"Tipo de expressão não suportado: {type(node).__name__}")


@mcp.tool()
def calculator(expression: str) -> dict:
    """
    Executa cálculos matemáticos de forma segura.

    Args:
        expression: Expressão matemática a ser calculada

    Returns:
        Dicionário com a expressão, resultado e formatação
    """
    MAX_EXPRESSION_LENGTH = 500
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return {
            "expression": expression,
            "error": (
                f"Expressão muito longa (máximo "
                f"{MAX_EXPRESSION_LENGTH} caracteres)"
            )
        }

    ALLOWED_CHARS = set("0123456789+-*/(). ^")
    if not all(c in ALLOWED_CHARS for c in expression.replace(" ", "")):
        return {
            "expression": expression,
            "error": "Expressão contém caracteres não permitidos"
        }

    try:
        expression = expression.strip().replace("^", "**")

        if not expression:
            raise ValueError("Expressão vazia")

        tree = ast.parse(expression, mode='eval')
        result = _eval_ast_node(tree.body)

        if math.isinf(result) or math.isnan(result):
            return {
                "expression": expression,
                "error": "Resultado inválido (infinito ou NaN)"
            }

        if abs(result) > sys.maxsize:
            return {
                "expression": expression,
                "error": "Resultado muito grande"
            }

        return {
            "expression": expression,
            "result": result,
            "formatted": f"{expression} = {result}"
        }
    except ZeroDivisionError:
        return {
            "expression": expression,
            "error": "Divisão por zero"
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Erro ao calcular: {str(e)}"
        }


@mcp.tool()
def get_weather(city: str, country_code: str = "BR") -> dict:
    """
    Consulta clima atual de uma cidade.

    Args:
        city: Nome da cidade 
        country_code: Código do país (default: "BR")

    Returns:
        Dict com: city, temperature, description, humidity, wind_speed
    """
    MAX_CITY_LENGTH = 100
    if not city or len(city) > MAX_CITY_LENGTH:
        return {"error": "Cidade inválida"}

    cache_key = cache._make_key("weather", f"{city},{country_code}")
    cached_weather = cache.get(cache_key)

    if cached_weather:
        cache.increment_metric("cache_hit_weather")
        return cached_weather

    cache.increment_metric("cache_miss_weather")

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "API key não configurada"}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{country_code}",
        "appid": api_key,
        "units": "metric",
        "lang": "pt_br"
    }

    try:
        response = httpx.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        data = response.json()

        result = {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "formatted": (
                f"{data['name']}: {data['main']['temp']}°C, "
                f"{data['weather'][0]['description']}"
            )
        }

        cache.set(cache_key, result, ttl=1800)

        return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Cidade '{city}' não encontrada"}
        return {"error": f"Erro HTTP {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": f"Erro ao consultar API: {str(e)}"}
    except (KeyError, IndexError) as e:
        return {"error": f"Resposta da API inválida: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
