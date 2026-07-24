import uvicorn

from backend.app.core.settings import settings


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=False,
    )
