import os
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

def get_ai_response(user_query, context):
    api_key = os.getenv("AI_API_KEY")
    
    if not api_key or "your_key" in api_key:
        return "Mentor: API Key missing! Add it to your .env file to unlock my full brain. 🧠"

    try:
        # Using Groq's fast Llama-3 model
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a GenZ Study Mentor for a CGC Mohali student. Context: {context}. Use Hinglish (Hindi + English). Be bold, encouraging, and witty."
                },
                {"role": "user", "content": user_query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"System Glitch: {str(e)}. Keep grinding anyway! 🔥"