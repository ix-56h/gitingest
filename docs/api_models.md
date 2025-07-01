# API Models Documentation

This document describes the Pydantic models used for the `/api/ingest` endpoint in the Gitingest API.

## Overview

The `/api/ingest` endpoint uses structured Pydantic models for both input validation and response formatting. This ensures type safety, automatic validation, and consistent API responses.

## Models

### PatternType Enum

```python
class PatternType(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
```

Defines the two types of file filtering patterns:
- `INCLUDE`: Only include files matching the pattern
- `EXCLUDE`: Exclude files matching the pattern

### IngestRequest

Input model for the `/api/ingest` endpoint.

```python
class IngestRequest(BaseModel):
    input_text: str = Field(..., description="Git repository URL or slug to ingest")
    max_file_size: int = Field(..., ge=0, le=500, description="File size slider position (0-500)")
    pattern_type: PatternType = Field(default=PatternType.EXCLUDE, description="Pattern type for file filtering")
    pattern: str = Field(default="", description="Glob/regex pattern for file filtering")
    token: str | None = Field(default=None, description="GitHub PAT for private repositories")
```

**Validation Rules:**
- `input_text`: Must not be empty (stripped of whitespace)
- `max_file_size`: Must be between 0 and 500 (inclusive)
- `pattern_type`: Defaults to "exclude"
- `pattern`: Stripped of whitespace, defaults to empty string
- `token`: Optional GitHub personal access token

**Example:**
```json
{
  "input_text": "https://github.com/cyclotruc/gitingest",
  "max_file_size": 243,
  "pattern_type": "exclude",
  "pattern": "*.md",
  "token": null
}
```

### IngestSuccessResponse

Response model for successful ingestion operations.

```python
class IngestSuccessResponse(BaseModel):
    result: Literal[True] = True
    repo_url: str = Field(..., description="Original repository URL")
    short_repo_url: str = Field(..., description="Short repository URL (user/repo)")
    summary: str = Field(..., description="Ingestion summary with token estimates")
    tree: str = Field(..., description="File tree structure")
    content: str = Field(..., description="Processed file content")
    ingest_id: str = Field(..., description="Unique ingestion identifier")
    default_file_size: int = Field(..., description="File size slider position used")
    pattern_type: str = Field(..., description="Pattern type used")
    pattern: str = Field(..., description="Pattern used")
    token: str | None = Field(None, description="Token used (if any)")
```

**Example:**
```json
{
  "result": true,
  "repo_url": "https://github.com/cyclotruc/gitingest",
  "short_repo_url": "cyclotruc/gitingest",
  "summary": "Processed 50 files, estimated tokens: 15,000",
  "tree": "gitingest/\n├── src/\n│   ├── server/\n│   └── gitingest/\n└── README.md",
  "content": "Repository content here...",
  "ingest_id": "abc123",
  "default_file_size": 243,
  "pattern_type": "exclude",
  "pattern": "*.md",
  "token": null
}
```

### IngestErrorResponse

Response model for failed ingestion operations.

```python
class IngestErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    repo_url: str = Field(..., description="Repository URL that failed")
    default_file_size: int = Field(..., description="File size slider position used")
    pattern_type: str = Field(..., description="Pattern type used")
    pattern: str = Field(..., description="Pattern used")
    token: str | None = Field(None, description="Token used (if any)")
```

**Example:**
```json
{
  "error": "Repository not found or is private",
  "repo_url": "https://github.com/private/repo",
  "default_file_size": 243,
  "pattern_type": "exclude",
  "pattern": "",
  "token": null
}
```

### IngestResponse

Union type for API responses.

```python
IngestResponse = Union[IngestSuccessResponse, IngestErrorResponse]
```

This allows the endpoint to return either a success or error response with proper typing.

## Usage in FastAPI

The models are used in the `/api/ingest` endpoint as follows:

```python
@router.post("/api/ingest", 
             response_model=IngestResponse,
             responses={
                 200: {"model": IngestSuccessResponse, "description": "Successful ingestion"},
                 400: {"model": IngestErrorResponse, "description": "Bad request or processing error"},
                 500: {"model": IngestErrorResponse, "description": "Internal server error"}
             })
async def api_ingest(
    request: Request,
    input_text: str = Form(...),
    max_file_size: int = Form(...),
    pattern_type: str = Form("exclude"),
    pattern: str = Form(""),
    token: Optional[str] = Form(None),
) -> IngestResponse:
    # Implementation...
```

## Benefits

1. **Type Safety**: All inputs and outputs are properly typed
2. **Automatic Validation**: Pydantic validates all inputs according to defined rules
3. **API Documentation**: FastAPI automatically generates OpenAPI documentation
4. **Consistent Responses**: Structured error and success responses
5. **IDE Support**: Better autocomplete and error detection in IDEs

## Error Handling

The models provide structured error handling:

- **Validation Errors**: Invalid input parameters are caught and returned as `IngestErrorResponse`
- **Processing Errors**: Repository processing failures return detailed error information
- **Unexpected Errors**: Internal server errors are caught and formatted consistently

## Migration from Previous Implementation

The previous implementation used raw dictionaries and manual JSON responses. The new models provide:

- Better type safety
- Automatic validation
- Consistent error handling
- Improved API documentation
- Better developer experience 