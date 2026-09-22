"""Import every model here so `Base.metadata` (and Alembic autogenerate) sees the full schema
from a single `import app.models`."""

from app.models.analysis import Analysis
from app.models.domain import Domain
from app.models.feedback import Feedback
from app.models.prediction import Prediction
from app.models.security_report import SecurityReport
from app.models.threat_intel import ThreatIntelLookup
from app.models.url import Url
from app.models.user import User

__all__ = [
    "Analysis",
    "Domain",
    "Feedback",
    "Prediction",
    "SecurityReport",
    "ThreatIntelLookup",
    "Url",
    "User",
]
