import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("GROQ_MODEL")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

if not model_name:
    raise ValueError("GROQ_MODEL not found in .env file")

try:
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: Model is working!"
            }
        ],
        temperature=0
    )

    print("✅ API Connection Successful")
    print(f"✅ Model: {model_name}")
    print(f"✅ Response: {response.choices[0].message.content}")

except Exception as e:
    print("❌ Error connecting to Groq")
    print(f"Error: {str(e)}")