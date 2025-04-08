import genai

try:
    model = genai.GenerativeModel(model_name="gemini-2.0-pro-latest", api_key="YOUR_API_KEY_PLACEHOLDER") # Replace placeholder if needed for test
    print("Successfully accessed genai.GenerativeModel")
except AttributeError as e:
    print(f"AttributeError: {e}")
except Exception as e:
    print(f"Other Error: {e}")