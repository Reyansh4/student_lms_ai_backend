import os
from typing import List
import openai
import aiofiles  # For async file I/O

openai.api_key = os.getenv("OPENAI_API_KEY")

TEMPLATE_PATH = "app/agent/templates/activity/clarification_questions.md"

async def generate_clarification_questions(activity_details: dict) -> List[str]:
    try:
        # Read the .md template
        async with aiofiles.open(TEMPLATE_PATH, mode='r') as f:
            template = await f.read()

        # Fill in the placeholder
        filled_prompt = template.replace("{activity_dictionary}", str(activity_details))

        # Send the prompt to the model
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational activity designer."},
                {"role": "user", "content": filled_prompt}
            ],
            temperature=0.7
        )

        content = response["choices"][0]["message"]["content"]

        # Extract the questions (simplified parsing)
        questions = [
            line.split(". ", 1)[1].strip()
            for line in content.splitlines()
            if line.strip().startswith(tuple(f"{i}." for i in range(1, 6)))
        ]

        if len(questions) < 5:
            raise ValueError("Fewer than 5 valid questions parsed.")

        return questions

    except Exception as e:
        raise RuntimeError(f"Error generating questions: {str(e)}")
