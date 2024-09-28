import cohere

class CohereClient:
    def __init__(self, api_key: str):
        # Initialize the Cohere client
        self.co = cohere.Client(api_key)

    def generate_text(self, prompt: str):
        response = self.co.generate(
            model='command-xlarge-nightly',
            prompt=prompt,
            max_tokens=100,
            temperature=0.7
        )
        return response.generations[0].text
