from google import genai
import json
import os
import ast
from dotenv import load_dotenv

load_dotenv()

# --- NEW SETUP ---
# We initialize a Client instead of using global config
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


def call_gemini(prompt: str) -> dict:
    try:
        # New Syntax: client.models.generate_content
        response = client.models.generate_content(
            model="gemma-3-4b-it",  # Or "gemini-1.5-flash" if 2.0 isn't available to you yet
            contents=prompt,
            config={
                "temperature": 0
            }
        )

        text = response.text.strip()

        # 1. Clean Markdown (Standard fix)
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]

                    # 2. Extract JSON
        start_index = text.find("{")
        end_index = text.rfind("}")

        if start_index != -1 and end_index != -1:
            text = text[start_index: end_index + 1]

        # 3. Parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(text)
            except:
                pass
            print(f"\n[Raw Invalid Output]: {text}")
            raise

    except Exception as e:
        print(f"\n[AI Error]: {e}")
        return {}