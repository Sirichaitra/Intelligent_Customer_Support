
from google import genai

from app.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

print("Models available for your API key:\n")

for model in client.models.list():
    name = getattr(model, "name", None)
    supported_methods = getattr(
        model, "supported_actions", []
    )

    if name and "generateContent" in supported_methods:
        print(name)
