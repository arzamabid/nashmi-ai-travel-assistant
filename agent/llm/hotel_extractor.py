
import json

from ollama import chat


MODEL = "qwen3:4b-instruct"


def extract_hotel_parameters(user_message: str) -> dict:
    prompt = f"""
Extract hotel search parameters from the user's request.

Return only a JSON object with these fields:
destination, check_in_date, check_out_date,
guests, rooms, stars, max_budget_sar.

Rules:
- Use YYYY-MM-DD for dates.
- Use null for information not provided.
- Do not invent missing information.
- Return JSON only.

User request:
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
