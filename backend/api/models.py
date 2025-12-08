from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """Request para processar uma query do usuário."""
    query: str = Field(..., description="Pergunta do usuário")


class IntermediateStep(BaseModel):
    """Passo intermediário da execução do agente."""
    tool: str
    input: str
    output: str


class QueryResponse(BaseModel):
    """Response com o resultado do processamento."""
    success: bool
    query: str
    response: Optional[str] = None
    intermediate_steps: List[IntermediateStep] = []
    tools_used: List[str] = []
    error: Optional[str] = None
