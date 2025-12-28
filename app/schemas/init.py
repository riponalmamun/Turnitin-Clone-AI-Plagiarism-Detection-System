from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.document import DocumentUpload, DocumentResponse
from app.schemas.plagiarism import (
    PlagiarismCheckRequest,
    PlagiarismCheckResponse,
    SubmissionStatus,
    MatchResponse
)
from app.schemas.report import ReportResponse

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "Token",
    "DocumentUpload", "DocumentResponse",
    "PlagiarismCheckRequest", "PlagiarismCheckResponse",
    "SubmissionStatus", "MatchResponse", "ReportResponse"
]