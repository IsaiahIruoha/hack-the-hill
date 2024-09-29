from fastapi import APIRouter, Depends
from app.ai_models.cohere_ai import CohereClient
from pydantic import BaseModel;

# Initialize the router
router = APIRouter()
class swingData(BaseModel):
    speed: float
    degrees: float

# Route to generate description using Cohere
@router.post("/generate-description")
async def generate_description(swing_data: swingData):
    # Initialize CohereClient with the API key
    cohere_client = CohereClient()

    # clean up the json 
    # pass the JSON then make that a string 
    # "Great shot! Your swing is consistent with a square clubface at impact. Keep practicing this form."

    # generated_text = cohere_client.generate_text(prompt=prompt)

    # Create a prompt based on CV model output
    # prompt = f"The computer vision model detected a '{swing_data.speed}' with {swing_data.degrees:.2f} confidence. Generate a brief description of this detection."
    prompt = f"Club head speed: '{swing_data.speed}', Launch angle: {swing_data.degrees:.2f}, Ball flight: slice, Impact point: toe. Use 2 sentences for advice."
    # Use Cohere to generate the text
    generated_text = cohere_client.generate_text(prompt)
    
    # Return the generated description
    return {"description": generated_text}