import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from server.models import IngestRequest, IngestSuccessResponse, IngestErrorResponse, PatternType
from server.routers.ingest import api_ingest
from fastapi import Request
from fastapi.responses import JSONResponse


def test_ingest_request_model_validation():
    """Test that the IngestRequest model validates correctly."""
    # Test valid request
    valid_request = IngestRequest(
        input_text="https://github.com/cyclotruc/gitingest",
        max_file_size=243,
        pattern_type=PatternType.EXCLUDE,
        pattern="*.md",
        token=None
    )
    assert valid_request.input_text == "https://github.com/cyclotruc/gitingest"
    assert valid_request.max_file_size == 243
    assert valid_request.pattern_type == PatternType.EXCLUDE
    
    # Test validation error - empty input
    with pytest.raises(ValueError, match="input_text cannot be empty"):
        IngestRequest(
            input_text="",
            max_file_size=243
        )
    
    # Test validation error - out of range max_file_size
    with pytest.raises(ValueError, match="Input should be less than or equal to 500"):
        IngestRequest(
            input_text="https://github.com/cyclotruc/gitingest",
            max_file_size=600
        )


def test_ingest_response_models():
    """Test that the response models work correctly."""
    # Test success response
    success_response = IngestSuccessResponse(
        repo_url="https://github.com/cyclotruc/gitingest",
        short_repo_url="cyclotruc/gitingest",
        summary="Processed 50 files, estimated tokens: 15,000",
        tree="gitingest/\n├── src/\n│   ├── server/\n│   └── gitingest/\n└── README.md",
        content="Repository content here...",
        default_file_size=243,
        pattern_type="exclude",
        pattern="*.md",
        token=None
    )
    assert success_response.result is True
    assert success_response.repo_url == "https://github.com/cyclotruc/gitingest"
    assert success_response.short_repo_url == "cyclotruc/gitingest"
    
    # Test error response
    error_response = IngestErrorResponse(
        error="Error: Invalid repository URL 'cyclotruc/'",
        repo_url="cyclotruc/",
        default_file_size=243,
        pattern_type="exclude",
        pattern="",
        token=None
    )
    assert error_response.error == "Error: Invalid repository URL 'cyclotruc/'"
    assert error_response.repo_url == "cyclotruc/"


@pytest.mark.asyncio
async def test_api_ingest_success():
    """Test the api_ingest function with a successful response."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.query_params = {}
    
    # Mock process_query to return success
    mock_response = {
        "repo_url": "https://github.com/cyclotruc/gitingest",
        "short_repo_url": "cyclotruc/gitingest",
        "summary": "Processed 50 files, estimated tokens: 15,000",
        "tree": "gitingest/\n├── src/\n│   ├── server/\n│   └── gitingest/\n└── README.md",
        "content": "Repository content here...",
        "ingest_id": "abc123",
        "default_file_size": 243,
        "pattern_type": "exclude",
        "pattern": "*.md",
        "token": None,
    }
    
    with patch('server.query_processor.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = mock_response
        
        response = await api_ingest(
            request=mock_request,
            input_text="https://github.com/cyclotruc/gitingest",
            max_file_size=243,
            pattern_type="exclude",
            pattern="*.md",
            token=""
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        # Access the response content as bytes and decode
        body = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
        assert '"result":true' in body  # No space after colon in JSON
        assert '"repo_url":"https://github.com/cyclotruc/gitingest"' in body


@pytest.mark.asyncio
async def test_api_ingest_error():
    """Test the api_ingest function with an error response."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.query_params = {}
    
    # Mock process_query to return error
    mock_response = {
        "error": "Error: Invalid repository URL 'cyclotruc/'",
        "repo_url": "cyclotruc/",
        "default_file_size": 243,
        "pattern_type": "exclude",
        "pattern": "",
        "token": ""
    }
    
    with patch('server.query_processor.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = mock_response
        
        response = await api_ingest(
            request=mock_request,
            input_text="cyclotruc/",
            max_file_size=243,
            pattern_type="exclude",
            pattern="",
            token=""
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        # Access the response content as bytes and decode
        body = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
        assert '"error":' in body
        assert '"repo_url":"cyclotruc/"' in body  # No space after colon in JSON


@pytest.mark.asyncio
async def test_api_ingest_validation_error():
    """Test the api_ingest function with validation error."""
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.query_params = {}
    
    # Test with empty input_text (should trigger validation error)
    response = await api_ingest(
        request=mock_request,
        input_text="",  # Empty input
        max_file_size=243,
        pattern_type="exclude",
        pattern="",
        token=""
    )
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    # Access the response content as bytes and decode
    body = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
    assert '"error":' in body
    assert "Validation error" in body


def test_pattern_type_enum():
    """Test the PatternType enum."""
    assert PatternType.INCLUDE == "include"
    assert PatternType.EXCLUDE == "exclude"
    assert PatternType.INCLUDE.value == "include"
    assert PatternType.EXCLUDE.value == "exclude" 