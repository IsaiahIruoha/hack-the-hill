from fastapi import FastAPI
from app.routers.ai_router import router as ai_router

app = FastAPI()

# Include the AI router
app.include_router(ai_router, prefix="/ai", tags=["ai"])

@app.get("/")
async def root():
    return {"message": "Hello World"}



@app.get("/fetch-data/")
async def fetch_data():
    async with httpx.AsyncClient() as client:
        # Send a non-blocking request to an external API
        response = await client.get('https://api.example.com/data')

        if response.status_code == 200:
            return response.json()
        else:   
            return {"error": f"Failed with status code: {response.status_code}"}


