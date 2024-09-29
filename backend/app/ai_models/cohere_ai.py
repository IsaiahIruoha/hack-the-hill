
import os
import cohere
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CohereClient:
    def __init__(self):
        # Initialize the Cohere client with the API key
        self.cohere_api = os.getenv("COHERE_API")
        self.cohere_model = os.getenv("COHERE_MODEL")
        self.co = cohere.Client(self.cohere_api)

    def generate_text(self, prompt: str):
        # Use the Cohere model to generate text
        response = self.co.chat(
            model=self.cohere_model,  # Specify the model, if required
            message=prompt
        )
        return response  # Get the generated text

# if __name__ == "__main__":
#     # Initialize CohereClient with the API key
#     cohere_client = CohereClient()

#     # Generate text based on a prompt
#     # prompt = "The computer vision model detected a 'cat' with 0.95 confidence. The object is located at coordinates {'x': 100, 'y': 200}. Generate a brief description of this detection."
#     prompt = "Your ball flight is straight and solid, but try adjusting your launch angle for more carry distance."
#     generated_text = cohere_client.generate_text(prompt)
    
#     # Print the result
#     print(generated_text.text)
