from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from server.query_processor import process_query
from server.server_utils import limiter
from server.models import IngestRequest, IngestSuccessResponse, IngestErrorResponse, IngestResponse, PatternType

router = APIRouter()

@router.post("/api/ingest", 
             responses={
                 200: {"model": IngestSuccessResponse, "description": "Successful ingestion"},
                 400: {"model": IngestErrorResponse, "description": "Bad request or processing error"},
                 500: {"model": IngestErrorResponse, "description": "Internal server error"}
             })
@limiter.limit("10/minute")
async def api_ingest(
    request: Request,
    input_text: str = Form(...),
    max_file_size: int = Form(...),
    pattern_type: str = Form("exclude"),
    pattern: str = Form(""),
    token: Optional[str] = Form(None),
):
    """Ingest a Git repository and return processed content.
    
    This endpoint processes a Git repository by cloning it, analyzing its structure,
    and returning a summary with the repository's content. The response includes
    file tree structure, processed content, and metadata about the ingestion.
    
    Parameters
    ----------
    input_text : str
        Git repository URL or slug to ingest
    max_file_size : int
        Maximum file size slider position (0-500) for filtering files
    pattern_type : str
        Type of pattern to use for file filtering ("include" or "exclude")
    pattern : str
        Glob/regex pattern string for file filtering
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories
        
    Returns
    -------
    JSONResponse
        Success response with ingestion results or error response with appropriate HTTP status code
        
    Raises
    ------
    HTTPException
        If validation fails or processing encounters an error
    """
    try:
        # Validate input using Pydantic model
        ingest_request = IngestRequest(
            input_text=input_text,
            max_file_size=max_file_size,
            pattern_type=PatternType(pattern_type),
            pattern=pattern,
            token=token
        )
        
        context = await process_query(
            request,
            input_text=ingest_request.input_text,
            slider_position=ingest_request.max_file_size,
            pattern_type=ingest_request.pattern_type.value,
            pattern=ingest_request.pattern,
            is_index=True,
            token=ingest_request.token,
        )
        
        if "error" in context:
            # Return structured error response with 400 status code
            error_response = IngestErrorResponse(
                error=context["error"],
                repo_url=context.get("repo_url", input_text),
                default_file_size=context.get("default_file_size", max_file_size),
                pattern_type=context.get("pattern_type", pattern_type),
                pattern=context.get("pattern", pattern),
                token=token
            )
            return JSONResponse(
                status_code=400,
                content=error_response.model_dump()
            )
        
        # Return structured success response with 200 status code
        success_response = IngestSuccessResponse(
            result=True,
            repo_url=context["repo_url"],
            short_repo_url=context["short_repo_url"],
            summary=context["summary"],
            tree=context["tree"],
            content=context["content"],
            default_file_size=context["default_file_size"],
            pattern_type=context["pattern_type"],
            pattern=context["pattern"],
            token=context.get("token")
        )
        return JSONResponse(
            status_code=200,
            content=success_response.model_dump()
        )
        
    except ValueError as ve:
        # Handle validation errors with 400 status code
        error_response = IngestErrorResponse(
            error=f"Validation error: {str(ve)}",
            repo_url=input_text,
            default_file_size=max_file_size,
            pattern_type=pattern_type,
            pattern=pattern,
            token=token
        )
        return JSONResponse(
            status_code=400,
            content=error_response.model_dump()
        )
        
    except Exception as exc:
        # Handle unexpected errors with 500 status code
        error_response = IngestErrorResponse(
            error=f"Internal server error: {str(exc)}",
            repo_url=input_text,
            default_file_size=max_file_size,
            pattern_type=pattern_type,
            pattern=pattern,
            token=token
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )