from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    response: str
    current_flow: Optional[str] = None
    rag_chunks: Optional[List[Dict[str, Any]]] = None 