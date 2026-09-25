import json
import os

from dotenv import load_dotenv
from google import genai

from schemas import EmailJobExtraction

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def extract_job_details(email_text: str) -> EmailJobExtraction:
    prompt = f"""
You are a job application email parser.

Read the email below and extract:

- company
- role
- status
- confidence

confidence must be a number between 0 and 1.

Return ONLY JSON.

Email:
{email_text}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )

    raw_response = response.text.strip()

    if raw_response.startswith("```json"):
     raw_response = raw_response[7:]

    if raw_response.endswith("```"):
     raw_response = raw_response[:-3]

    data = json.loads(raw_response.strip())

    return EmailJobExtraction.model_validate(data)