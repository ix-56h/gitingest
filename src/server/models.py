"""Pydantic models for the query form."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field, field_validator

# needed for type checking (pydantic)
from server.form_types import IntForm, OptStrForm, StrForm  # noqa: TC001 (typing-only-first-party-import)


class PatternType(str, Enum):
    """Enumeration for pattern types used in file filtering."""
    
    INCLUDE = "include"
    EXCLUDE = "exclude"


class IngestRequest(BaseModel):
    """Request model for the /api/ingest endpoint.
    
    Attributes
    ----------
    input_text : str
        The Git repository URL or slug to ingest.
    max_file_size : int
        Maximum file size slider position (0-500) for filtering files.
    pattern_type : PatternType
        Type of pattern to use for file filtering (include or exclude).
    pattern : str
        Glob/regex pattern string for file filtering.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.
    """
    
    input_text: str = Field(..., description="Git repository URL or slug to ingest")
    max_file_size: int = Field(..., ge=0, le=500, description="File size slider position (0-500)")
    pattern_type: PatternType = Field(default=PatternType.EXCLUDE, description="Pattern type for file filtering")
    pattern: str = Field(default="", description="Glob/regex pattern for file filtering")
    token: str | None = Field(default=None, description="GitHub PAT for private repositories")
    
    @field_validator('input_text')
    @classmethod
    def validate_input_text(cls, v):
        """Validate that input_text is not empty."""
        if not v.strip():
            raise ValueError('input_text cannot be empty')
        return v.strip()
    
    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v):
        """Validate pattern field."""
        return v.strip() if v else ""


class IngestSuccessResponse(BaseModel):
    """Success response model for the /api/ingest endpoint.
    
    Attributes
    ----------
    result : Literal[True]
        Always True for successful responses.
    repo_url : str
        The original repository URL that was processed.
    short_repo_url : str
        Short form of repository URL (user/repo).
    summary : str
        Summary of the ingestion process including token estimates.
    tree : str
        File tree structure of the repository.
    content : str
        Processed content from the repository files.
    default_file_size : int
        The file size slider position used.
    pattern_type : str
        The pattern type used for filtering.
    pattern : str
        The pattern used for filtering.
    token : str | None
        The token used (if any).
    """
    
    result: Literal[True] = True
    repo_url: str = Field(..., description="Original repository URL")
    short_repo_url: str = Field(..., description="Short repository URL (user/repo)")
    summary: str = Field(..., description="Ingestion summary with token estimates")
    tree: str = Field(..., description="File tree structure")
    content: str = Field(..., description="Processed file content")
    default_file_size: int = Field(..., description="File size slider position used")
    pattern_type: str = Field(..., description="Pattern type used")
    pattern: str = Field(..., description="Pattern used")
    token: str | None = Field(None, description="Token used (if any)")


class IngestErrorResponse(BaseModel):
    """Error response model for the /api/ingest endpoint.
    
    Attributes
    ----------
    error : str
        Error message describing what went wrong.
    repo_url : str
        The repository URL that failed to process.
    default_file_size : int
        The file size slider position that was used.
    pattern_type : str
        The pattern type that was used.
    pattern : str
        The pattern that was used.
    token : str | None
        The token that was used (if any).
    """
    
    error: str = Field(..., description="Error message")
    repo_url: str = Field(..., description="Repository URL that failed")
    default_file_size: int = Field(..., description="File size slider position used")
    pattern_type: str = Field(..., description="Pattern type used")
    pattern: str = Field(..., description="Pattern used")
    token: str | None = Field(None, description="Token used (if any)")


# Union type for API responses
IngestResponse = Union[IngestSuccessResponse, IngestErrorResponse]


class QueryForm(BaseModel):
    """Form data for the query.

    Attributes
    ----------
    input_text : str
        Text or URL supplied in the form.
    max_file_size : int
        The maximum allowed file size for the input, specified by the user.
    pattern_type : str
        The type of pattern used for the query (``include`` or ``exclude``).
    pattern : str
        Glob/regex pattern string.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    """

    input_text: str
    max_file_size: int
    pattern_type: str
    pattern: str
    token: str | None = None

    @classmethod
    def as_form(
        cls,
        input_text: StrForm,
        max_file_size: IntForm,
        pattern_type: StrForm,
        pattern: StrForm,
        token: OptStrForm,
    ) -> QueryForm:
        """Create a QueryForm from FastAPI form parameters.

        Parameters
        ----------
        input_text : StrForm
            The input text provided by the user.
        max_file_size : IntForm
            The maximum allowed file size for the input.
        pattern_type : StrForm
            The type of pattern used for the query (``include`` or ``exclude``).
        pattern : StrForm
            Glob/regex pattern string.
        token : OptStrForm
            GitHub personal access token (PAT) for accessing private repositories.

        Returns
        -------
        QueryForm
            The QueryForm instance.

        """
        return cls(
            input_text=input_text,
            max_file_size=max_file_size,
            pattern_type=pattern_type,
            pattern=pattern,
            token=token,
        )
