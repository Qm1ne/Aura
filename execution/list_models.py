from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def list_live_models():
    client = genai.Client(api_key=API_KEY, http_options={"api_version": "v1beta"})
    print(f"{'Model ID':<55} {'Display Name'}")
    print("-" * 100)
    for model in client.models.list():
        # Filter to only show models that support bidiGenerateContent (Live API)
        if hasattr(model, 'supported_actions') and model.supported_actions:
            if 'bidiGenerateContent' in model.supported_actions:
                print(f"{model.name:<55} {model.display_name}")

if __name__ == "__main__":
    list_live_models()
