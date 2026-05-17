from fastapi import FastAPI
from source.config import get_settings

app = FastAPI(title="HR-TA",
              description="A chatbot for HR",
              version="0.1.0"
              )

@app.get('/health')
def health():
    settings = get_settings()
    return {"status": "ok",
            "env": settings.app_env
    }



