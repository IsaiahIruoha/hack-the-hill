from fastapi import APIRouter, Depends
from app.ai_models.cohere import CohereClient
from pydantic import BaseModel

# Initialize the router
router = APIRouter()

# Pydantic model for input data (this can be the CV model output)
class CVModelOutput(BaseModel):
    class_name: str
    confidence: float
    coordinates: dict

# Initialize Cohere Client with API key (replace with your key)
cohere_client = CohereClient(api_key="your_cohere_api_key")

# Route to generate description using Cohere
@router.post("/generate-description")
async def generate_description(cv_output: CVModelOutput):
    # Create a prompt based on CV model output
    prompt = f"The computer vision model detected a '{cv_output.class_name}' with {cv_output.confidence:.2f} confidence. The object is located at coordinates {cv_output.coordinates}. Generate a brief description of this detection."

    # Use Cohere to generate the text
    generated_text = cohere_client.generate_text(prompt)

    # Return the generated description
    return {"description": generated_text}
