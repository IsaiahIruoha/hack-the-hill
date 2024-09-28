import cohere

co = cohere.Client(api_key='trnpajuLJZRKpozqUJXDa3wfVEsFwCnk1dx0giKQ') # This is your trial API key
response = co.chat(
  model='70265fec-f205-4a64-a372-43674a3a33b4-ft',
  message="The computer vision model detected a 'cat' with 0.95 confidence. The object is located at coordinates {'x': 100, 'y': 200}. Generate a brief description of this detection."
)
print(response)