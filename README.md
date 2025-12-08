#  AI Assistant Vaga AI Engineer Júnior

Intelligent AI assistant that automatically identifies when to use external tools (calculator) versus the LLM’s built-in knowledge.

##  Objective

Create an assistant that:

Automatically identifies mathematical questions

Uses a calculator for precise calculations

Responds using the LLM’s base knowledge for other questions

Demonstrates integration between LLMs and external tools

##  Architecture

The architecture follows a modular and decoupled model:

1. Frontend (Streamlit — port 8501)

Interactive interface responsible for capturing inputs and displaying responses.

2. Backend (FastAPI — port 8000)

Communication gateway between the user and the agent.

3. MCP Server (FastMCP — port 8001)

Server exposing deterministic tools to the LLM agent:

Calculator: secure mathematical operations
Get_weather: real-time weather queries via OpenWeatherMap

 **General Flow:**

Streamlit (User Input) → FastAPI → **LangChain Agent** (decides whether tools are needed) → MCP Tools →
Response to the user

# Components

1. **MCP Server (FastMCP)**: Tool server
2. **FastAPI Backend**: REST API with LangChain agent
3. **Streamlit Frontend**: Web interface

# How to Run

Installation

1. **Clone the repository**

2. **Create a virtual environment and install dependencies**:

```bash
python3.12 -m venv venv
source ./venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

3. **Configure environment variables**:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys:

# Required: OpenAI API – you need an OPENAI API KEY with credits in your account
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# Weather API (to use the get_weather tool)
# Get it for free at: https://openweathermap.org/api
OPENWEATHER_API_KEY=your-openweather-key-here

## Run with Docker (Recommended)

The easiest way to start the application is using Docker Compose:

```bash
docker-compose up --build
```

This will:

1. Build Docker images
2. Start MCP Server (port 8001)
3. Start FastAPI Backend (port 8000)
4. Start Streamlit Frontend (port 8501)

**Access `http://localhost:8501` to use the full service**


**Stop the services:**
```bash
docker-compose down
```

Run each service **separately**

**Terminal 1 – FastAPI Backend**

```bash
python -m backend.main
```


Backend available at `http://localhost:8000`

**Terminal 2 – Streamlit Frontend**:

```bash
streamlit run frontend/app.py
```

Frontend available at `http://localhost:8501`

**Terminal 3 – MCP Servers**:

```bash
python mcp_server.server.py
```

**You can test the API without the frontend, but you must run both FastAPI Backend and the MCP Servers**:

```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Quanto é 25 * 37?"}'

```
### You can access interactive documentation at: `http://localhost:8000/docs`
```
/v1/query - Processes the user input query
/v1/health - API health check
/v1/metric - Returns system usage metrics
```


**API logs are available in the 'logs' folder**

## Implementation Logic

The logic used was to have an API created with FastAPI to host an LLM agent that decides which MCP tools to use based on user input. For that, I created an MCP Server containing two tools: calculator — a Python-based calculator, and get_weather — integration with an external API.

It was dockerized so it is always ready to be executed across different serverless environments.

The intention was to keep the application as modular as possible, like a microservice.

## 1. MCP Server with FastMCP

I implemented an MCP server using FastMCP that exposes 2 tools:

**Tool 1: Calculator**

- **Security**: Uses AST (Abstract Syntax Tree) for safe parsing.
- **Supported operations**: `+`, `-`, `*`, `/`, `**` (potencia), parentheses

**Tool 2: Weather (get_weather)**

- **API**: OpenWeatherMap (free, 60 calls/min)
- **Parameters**: city (string), country_code (default: "BR")
- **Returns**: temperature, description, humidity, wind speed

## 2. LangChain Agent

The agent uses OpenAI Functions to automatically decide when to use the calculator or weather tool:

- **System Prompt**: Clear instructions about when to use each tool
- **OpenAI Functions Agent**: LangChain’s native function-calling framework
- **MCP Integration**: Connects the agent to the MCP Server tools

## 3. FastAPI Backend

REST API exposing endpoint `/v1/query`:

- **POST /v1/query**: Processes the user question
- **GET /v1/health**: Health check
- **CORS enabled**: For communication with Streamlit frontend

## 4. Streamlit Frontend

Simple and intuitive web interface:

- Interactive chat
- Visualization of used tools
- Suggested example questions

## Technical Decisions

### Why FastMCP?

- **Simplicity**: Reduces boilerplate compared to manual implementation
- **Standardization**: Follows the Model Context Protocol for LLM connections
- **Easy integration**: Works natively with LangChain
- **Decoupling**: Can run in a separate container to serve multiple LLM agents

### Why LangChain?

- **Built-in agents**: Mature framework for tool-using agents
- **OpenAI Functions**: Native function-calling support

### Why FastAPI?

- **Native async**: Supports LangChain async operations
- **Type hints**: Automatic validation with Pydantic
- **Automatic documentation**: Swagger UI

### Why Streamlit?

- **Fast development**
- **Ideal for demos**

## Future Improvements

If I had more time, I would implement:

### Features

- **More tools**: Web search, other API integrations
- **RAG**: Knowledge base for semantic search
- **Streaming**: Real-time responses via WebSockets
- **History**: Long-term conversation persistence in a database
- **Multi-agent**: Coordination between specialized agents

### Infrastructure

- **Modularization**: Each MCP Server in its own container for reuse
- **Rate limiting**: Protection against abuse
- **Authentication**: JWT or API keys
- **Observability**: LangSmith for tracing and monitoring
- **Messaging**: RabbitMQ to manage communication between LLM <-> MCP Server

### Quality

- **CI/CD**: GitHub Actions for automatic testing and deployment
- **Linting**

## Tests
## Run all tests

Keep the MCP service running:

 ```bash
    cd mcp_server
    python ./server.py
  ```
```bash
pytest -v
```

## Project Structure
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── mcp_server/
│   └── server.py
│
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── routes.py
│   │   └── models.py
│   └── core/
│       ├── agent.py
│       └── prompts.py
│
└── frontend/
    └── app.py

## License

This project was developed as part of a technical challenge for the AI Engineer Junior position.