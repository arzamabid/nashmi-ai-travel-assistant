
import json

from datetime import date

from ollama import chat


MODEL = "qwen3:4b-instruct"


def extract_restaurant_parameters(user_message: str) -> dict:
    today = date.today().isoformat()

    prompt = f"""
Extract restaurant search parameters from the user's message.

Today is {today}.

Return only a JSON object with these exact fields:
city, cuisine, price_level, family_friendly,
date, time, party_size.

Rules:
- Use YYYY-MM-DD for dates.
- Convert relative dates such as "tomorrow" using today's date.
- Use HH:MM in 24-hour format for time.
- party_size must be an integer.
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
