from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from ..services.ai_service_v2 import AIServiceV2

router = APIRouter(prefix="/api", tags=["AI Assistant"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()


class QueryResponse(BaseModel):
    summary: str
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    chart_type: Optional[str] = None
    columns: Optional[List[str]] = None


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest
) -> QueryResponse:
    """
    Process a natural language query and return AI-generated insights.
    
    Args:
        request: The query request containing the natural language question
        
    Returns:
        QueryResponse with summary text and optional data/chart information
    """
    try:
        ai_service = AIServiceV2()
        result = await ai_service.process_query(request.query)
        
        return QueryResponse(
            summary=result["summary"],
            data=result.get("data"),
            chart_type=result.get("chart_type"),
            columns=result.get("columns")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")