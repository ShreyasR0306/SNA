import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Testing GPT-OSS 120B...")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Explain social network influencer detection in simple words."
        }
    ]
)

print("\nGPT-OSS 120B RESPONSE:")
print(response.choices[0].message.content)