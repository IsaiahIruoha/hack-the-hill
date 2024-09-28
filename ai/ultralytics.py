from inference_sdk import InferenceHTTPClient

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="oIHfAk7TnTpKzXx6bald"
)

result = CLIENT.infer(your_image.jpg, model_id="clubs-heads/1")