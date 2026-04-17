import uvicorn
from app.api import app
from app.config import get_settings

def run():
    settings = get_settings() 
    uvicorn.run("main:app", host=settings.host, reload=True) #port=settings.port

if __name__ == "__main__":
    run()
