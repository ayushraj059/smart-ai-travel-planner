"""
Start the server:
    python run.py
or:
    uvicorn app.main:app --reload --port 8000
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.ENV == "development",
        log_level="debug" if settings.DEBUG else "info",
    )
