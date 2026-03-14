"""Entry point for the PokerLab backend server."""

from dotenv import load_dotenv
load_dotenv()

import uvicorn

from backend.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
