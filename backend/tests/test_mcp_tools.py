import pytest
from mcp_server.server import calculator, get_weather
from unittest.mock import patch, Mock


class TestCalculator:
    def test_calculator_valid_expression(self):
        result = calculator("2 + 2")
        assert result["result"] == 4
        assert result["expression"] == "2 + 2"

    def test_calculator_multiplication(self):
        result = calculator("128 * 46")
        assert result["result"] == 5888

    def test_calculator_power(self):
        result = calculator("2 ** 10")
        assert result["result"] == 1024

    def test_calculator_complex_expression(self):
        result = calculator("(15 + 30) / 3")
        assert result["result"] == 15.0

    def test_calculator_invalid_expression(self):
        result = calculator("abc")
        assert "error" in result

    def test_calculator_division_by_zero(self):
        result = calculator("10 / 0")
        assert "error" in result
        assert "Divisão por zero" in result["error"]

    def test_calculator_too_long(self):
        result = calculator("1" * 501)
        assert "error" in result
        assert "muito longa" in result["error"]

    def test_calculator_invalid_characters(self):
        result = calculator("import os")
        assert "error" in result


class TestWeather:
    @patch('httpx.get')
    def test_weather_valid_city(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "São Paulo",
            "main": {"temp": 25, "humidity": 60},
            "weather": [{"description": "céu limpo"}],
            "wind": {"speed": 3.5}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_weather("São Paulo")
        assert result["city"] == "São Paulo"
        assert result["temperature"] == 25
        assert result["humidity"] == 60
        assert "formatted" in result

    @patch.dict('os.environ', {}, clear=True)
    def test_weather_no_api_key(self):
        result = get_weather("São Paulo")
        assert "error" in result
        assert "API key não configurada" in result["error"]

    def test_weather_empty_city(self):
        result = get_weather("")
        assert "error" in result
        assert "Cidade inválida" in result["error"]

    def test_weather_city_too_long(self):
        result = get_weather("A" * 101)
        assert "error" in result
        assert "Cidade inválida" in result["error"]

    @patch('httpx.get')
    def test_weather_city_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = __import__(
            'httpx').HTTPStatusError(
            "Not found",
            request=Mock(),
            response=mock_response
        )

        result = get_weather("CidadeInexistente")
        assert "error" in result
