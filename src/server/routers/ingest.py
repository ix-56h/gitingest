"""Ingest endpoint for the API."""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse

from gitingest.config import TMP_BASE_PATH
from server.models import IngestErrorResponse, IngestRequest, IngestSuccessResponse
from server.query_processor import process_query
from server.server_config import MAX_DISPLAY_SIZE
from server.server_utils import limiter

router = APIRouter()


@router.post(
    "/api/ingest",
    responses={
        status.HTTP_200_OK: {"model": IngestSuccessResponse, "description": "Successful ingestion"},
        status.HTTP_400_BAD_REQUEST: {"model": IngestErrorResponse, "description": "Bad request or processing error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": IngestErrorResponse, "description": "Internal server error"},
    },
)
@limiter.limit("10/minute")
async def api_ingest(
    request: Request,  # noqa: ARG001
    ingest_request: IngestRequest,
) -> JSONResponse:
    """Ingest a Git repository and return processed content.

    **This endpoint processes a Git repository by cloning it, analyzing its structure,**
    and returning a summary with the repository's content. The response includes
    file tree structure, processed content, and metadata about the ingestion.

    **Parameters**

    - **ingest_request** (`IngestRequest`): Pydantic model containing ingestion parameters

    **Returns**

    - **JSONResponse**: Success response with ingestion results or error response with appropriate HTTP status code

    """  # pylint: disable=unused-argument
    try:
        result = await process_query(
            input_text=ingest_request.input_text,
            slider_position=ingest_request.max_file_size,
            pattern_type=ingest_request.pattern_type,
            pattern=ingest_request.pattern,
            token=ingest_request.token,
        )

        if isinstance(result, IngestErrorResponse):
            # Return structured error response with 400 status code
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result.model_dump(),
            )

        # Return structured success response with 200 status code
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except ValueError as ve:
        # Handle validation errors with 400 status code
        error_response = IngestErrorResponse(
            error=f"Validation error: {ve!s}",
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as exc:
        # Handle unexpected errors with 500 status code
        error_response = IngestErrorResponse(
            error=f"Internal server error: {exc!s}",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.get(
    "/api/{user}/{repository}",
    responses={
        status.HTTP_200_OK: {"model": IngestSuccessResponse, "description": "Successful ingestion"},
        status.HTTP_400_BAD_REQUEST: {"model": IngestErrorResponse, "description": "Bad request or processing error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": IngestErrorResponse, "description": "Internal server error"},
    },
)
@limiter.limit("10/minute")
async def api_ingest_get(
    request: Request,  # noqa: ARG001
    user: str,
    repository: str,
    max_file_size: int = MAX_DISPLAY_SIZE,
    pattern_type: str = "exclude",
    pattern: str = "",
    token: str = "",
) -> JSONResponse:
    """Ingest a GitHub repository via GET and return processed content.

    **This endpoint processes a GitHub repository by analyzing its structure and returning a summary**
    with the repository's content. The response includes file tree structure, processed content, and
    metadata about the ingestion. All ingestion parameters are optional and can be provided as query parameters.

    **Path Parameters**
    - **user** (`str`): GitHub username or organization
    - **repository** (`str`): GitHub repository name

    **Query Parameters**
    - **max_file_size** (`int`, optional): Maximum file size to include in the digest (default: 50 KB)
    - **pattern_type** (`str`, optional): Type of pattern to use ("include" or "exclude", default: "exclude")
    - **pattern** (`str`, optional): Pattern to include or exclude in the query (default: "")
    - **token** (`str`, optional): GitHub personal access token for private repositories (default: "")

    **Returns**
    - **JSONResponse**: Success response with ingestion results or error response with appropriate HTTP status code
    """  # pylint: disable=unused-argument
    try:
        effective_input_text = f"{user}/{repository}"
        result = await process_query(
            input_text=effective_input_text,
            slider_position=max_file_size,
            pattern_type=pattern_type,
            pattern=pattern,
            token=token or None,
        )

        if isinstance(result, IngestErrorResponse):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result.model_dump(),
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump(),
        )

    except ValueError as ve:
        error_response = IngestErrorResponse(
            error=f"Validation error: {ve!s}",
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as exc:
        error_response = IngestErrorResponse(
            error=f"Internal server error: {exc!s}",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.get("/api/download/file/{ingest_id}", response_class=FileResponse)
async def download_ingest(ingest_id: str) -> FileResponse:
    """Return the first ``*.txt`` file produced for ``ingest_id`` as a download.

    Parameters
    ----------
    ingest_id : str
        Identifier that the ingest step emitted (also the directory name that stores the artefacts).

    Returns
    -------
    FileResponse
        Streamed response with media type ``text/plain`` that prompts the browser to download the file.

    Raises
    ------
    HTTPException
        **404** - digest directory is missing or contains no ``*.txt`` file.
        **403** - the process lacks permission to read the directory or file.

    """
    directory = TMP_BASE_PATH / ingest_id

    if not directory.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Digest {ingest_id!r} not found")

    try:
        first_txt_file = next(directory.glob("*.txt"))
    except StopIteration as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No .txt file found for digest {ingest_id!r}",
        ) from exc

    try:
        return FileResponse(path=first_txt_file, media_type="text/plain", filename=first_txt_file.name)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied for {first_txt_file}",
        ) from exc
