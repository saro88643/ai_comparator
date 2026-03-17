from google import genai

API_KEY = "AIzaSyDk1ab8rjd_r-4CuveDRhJCCrShaLDXeFo"

client = genai.Client(api_key=API_KEY)

models = client.models.list()

for model in models:
    print(model.name)