import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
else:
    try:
        import google.auth
        _, project_id = google.auth.default()
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id or "")
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    except Exception:
        pass

@dataclass
class ExpenseAgentConfig:
    """Agent configuration with sensible defaults."""
    model: str = "gemini-3.1-flash-lite"
    review_threshold: float = 100.0

config = ExpenseAgentConfig()
