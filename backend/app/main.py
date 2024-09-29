from app import app 
from app.routers.ai_router import router as ai_router


# Include the AI router
app.include_router(ai_router, prefix="/ai", tags=["ai"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

