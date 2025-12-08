#  AI Assistant Vaga AI Engineer Júnior

Assistente de IA inteligente que identifica automaticamente quando usar ferramentas externas (calculadora) versus conhecimento base do LLM.

##  Objetivo

Criar um assistente que:
- Identifica perguntas matemáticas automaticamente
- Usa calculadora para cálculos precisos
- Responde com conhecimento base do LLM para outras perguntas
- Demonstra integração de LLMs com ferramentas externas

##  Arquitetura

A arquitetura segue um modelo modular e desacoplado:

1. Frontend (Streamlit — porta 8501)

Interface interativa responsável por capturar inputs e exibir as respostas.

2. Backend (FastAPI — porta 8000)

Gateway de comunicação entre o usuário e o agente.

3. MCP Server (FastMCP — porta 8001)

Servidor que expõe ferramentas determinísticas ao agente LLM:

Calculator: operações matemáticas seguras

Get_weather: consulta de clima em tempo real via OpenWeatherMap

 **Fluxo Geral:**

  Streamlit (Input do Usuário) → FastAPI → **LangChain Agent** (decide se precisa de ferramentas) → MCP Tools →
  Resposta ao usuário

# Componentes

1. **MCP Server (FastMCP)**: Servidor de ferramentas
2. **Backend FastAPI**: API REST com agente LangChain
3. **Frontend Streamlit**: Interface web

##Como Executar


### Instalação

1. **Clone o repositório**

2. **Crie ambiente virtual e instale dependências**:

```bash
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione suas chaves de API:

```env
# Obrigatório: OpenAI API - necessita de uma API KEY da OPENAI com Creditos na conta
OPENAI_API_KEY=sk-sua-chave-aqui
OPENAI_MODEL=gpt-4

#Weather API (para usar a tool get_weather)
# Obtenha grátis em: https://openweathermap.org/api
OPENWEATHER_API_KEY=sua-chave-openweather-aqui
```

###  Executar com Docker (Recomendado)

A forma mais fácil de subir a aplicação é usando Docker Compose:

```bash
docker-compose up --build
```

Isso irá:
1. Construir as imagens Docker
2. Iniciar MCP Server (porta 8001)
3. Iniciar Backend FastAPI (porta 8000)
4. Iniciar Frontend Streamlit (porta 8501)

**Acesse `http://localhost:8501` para usar o serviço por Completo**

**Parar os serviços:**
```bash
docker-compose down
```



Executar cada serviço **separadamente**

**Terminal 1 - Backend FastAPI**:
```bash
python -m backend.main
```

O backend estará disponível em `http://localhost:8000`

**Terminal 2 - Frontend Streamlit**:
```bash
streamlit run frontend/app.py
```

O frontend estará disponível em `http://localhost:8501`

**Terminal 3 - Servidores MCP**:
```bash
python mcp_server.server.py
```

**Você pode testar a API sem o frontend, mas tem de executar Backend Fast API e Servidores MCP**:

```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Quanto é 25 * 37?"}'

```
### Você pode acessar documentação interativa: `http://localhost:8000/docs`
```
/v1/query - Processa query de entrada do usuário
/v1/health - Health check da API
/v1/metric - Retorna métricas de uso do sistema
```

**Os logs da API estão disponiveis na pasta 'logs'**


##  Lógica de Implementação
A lógica utilizada foi ter uma API criada com FastAPI para ter um agente LLM que decidisse qual tools MCP usar baseada na entrada do usuário, para isso criei um MCP Server que contém duas ferramentas : calculator - uma calculado em python e get_wheater - conexao com uma API externa.

Foi dockerizado para estar sempre pronto para ser executado em diferentes servless.

A intenção era deixar a aplicação o mais modular possivel, como um microsserviço.

### 1. MCP Server com FastMCP

Implementei um servidor MCP usando FastMCP que expõe 2 ferramentas:

**Tool 1: Calculator**
- **Segurança**: Usa AST (Abstract Syntax Tree) para parse seguro.
- **Operações suportadas**: `+`, `-`, `*`, `/`, `**` (potência), parênteses


**Tool 2: Weather (get_weather)**
- **API**: OpenWeatherMap (gratuita, 60 calls/min)
- **Parâmetros**: city (string), country_code (default: "BR")
- **Retorna**: Temperatura, descrição, umidade, velocidade do vento


### 2. LangChain Agent

O agente usa OpenAI Functions para decidir automaticamente quando usar a calculadora ou a consulta do clima:

- **System Prompt**: Instruções claras sobre quando usar cada ferramenta
- **OpenAI Functions Agent**: Framework nativo do LangChain para function calling
- **Integração com MCP**: Conecta o agente às ferramentas do MCP Server


### 3. Backend FastAPI

API REST que expõe endpoint `/v1/query`:

- **POST /v1/query**: Processa pergunta do usuário
- **GET /v1/health**: Health check
- **CORS habilitado**: Para comunicação com frontend Streamlit

### 4. Frontend Streamlit

Interface web simples e intuitiva:

- Chat interativo
- Visualização de tools usadas
- Exemplos sugeridos de perguntas

##  Decisões Técnicas

### Por que FastMCP?

- **Simplicidade**: Reduz boilerplate comparado com implementação manual
- **Padronização**: Segue o Model Context Protocol para conexões com LLM
- **Integração fácil**: Funciona nativamente com LangChain
- **Desacoplamento**: Pode ser usado em um conteiner separadamente para ser usado por outros agentes LLM

### Por que LangChain?

- **Agents prontos**: Framework maduro para agentes com ferramentas
- **OpenAI Functions**: Suporte nativo a function calling

### Por que FastAPI?

- **Async nativo**: Suporta operações assíncronas do LangChain
- **Type hints**: Validação automática com Pydantic
- **Documentação automática**: Swagger UI

### Por que Streamlit?

- **Desenvolvimento rápido**
- **Ideal para demonstrações**

##  Melhorias Futuras

Se tivesse mais tempo, implementaria:

### Funcionalidades

- **Mais ferramentas**: Busca web, consulta a outras APIs
- **RAG**: Base de conhecimento para busca semântica
- **Streaming**: Respostas em tempo real via WebSockets, permitindo menor latência
- **Histórico**: Persistência de conversas a longo prazo em banco de dados
- **Multi-agente**: Coordenação entre múltiplos agentes especializados

### Infraestrutura
- **Modularização**: Cada MCP Server com seu própio conteiner, permitindo ser usado por outros Agentes LLM
- **Rate Limiting**: Proteção contra abuso
- **Autenticação**: JWT ou API Keys
- **Observabilidade**: LangSmith para tracing de monitoramento
- **Mensageria**: Usar RabbitMQ para ter um sistema de Filas na conexao LLM <-> MCP Server 

### Qualidade

- **CI/CD**: GitHub Actions para testes e deploy automáticos
- **Linting**


##  Testes


### Rodar todos os testes

Deixa o serviço MCP online :
  ```bash
    cd mcp_server
    python ./server.py
  ```

```bash
pytest -v
```

## Estrutura do Projeto

```
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
```
##  Licença

Este projeto foi desenvolvido como parte de um desafio técnico para vaga de AI Engineer Júnior.

---
