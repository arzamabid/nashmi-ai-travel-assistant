
import json

from datetime import date

from ollama import chat


MODEL = "qwen3:4b-instruct"


def extract_flight_parameters(user_message: str) -> dict:
    today = date.today().isoformat()

    prompt = f"""
Extract flight search parameters from the user's message.

Today is {today}.

Return only a JSON object with these exact fields:
origin, destination, departure_date, passengers,
cabin, direct_only.

Rules:
- origin is the departure city.
- destination is the arrival city.
- Use YYYY-MM-DD for departure_date.
- Convert relative dates such as "tomorrow" using today's date.
- passengers must be an integer.
- cabin must be "economy" or "business" when specified.
- direct_only must be true if the user explicitly requests
  direct or nonstop flights.
- direct_only must be false if the user explicitly allows
  connecting flights.
- Use null for information not provided.
- Do not invent missing information.
- Do not include explanations.
- Return JSON only.

User message:
{user_message}
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        format="json",
        options={"temperature": 0},
    )

    return json.loads(response.message.content)
