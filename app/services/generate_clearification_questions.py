import os
from typing import List
import aiofiles
import subprocess
import openai
from app.core.config import settings

# Path to the markdown template for prompting
TEMPLATE_PATH = "app/agent/templates/activity/clarification_questions.md"

# Set OpenRouter API key and base URL for Claude
openai.api_key = settings.OPENAI_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

def generate_clarification_questions(activity_details: dict) -> List[str]:
    try:
        # Read the .md prompt template
        with aiofiles.open(TEMPLATE_PATH, mode="r") as f:
            template = f.read()

        # Replace placeholder with actual activity details
        filled_prompt = template.replace("{activity_dictionary}", str(activity_details))

        # Use Claude 3 Haiku via OpenRouter
        response = openai.ChatCompletion.acreate(
            model="anthropic/claude-3-haiku",
            messages=[
                {"role": "system", "content": "You are an educational activity designer."},
                {"role": "user", "content": filled_prompt}
            ],
            temperature=0.7
        )
        content = response["choices"][0]["message"]["content"]

        # Extract questions formatted like: 1. What is...? 2. How does...?
        questions = [
            line.split(". ", 1)[1].strip()
            for line in content.splitlines()
            if line.strip().startswith(tuple(f"{i}." for i in range(1, 6)))
        ]

        if len(questions) < 5:
            raise ValueError("Fewer than 5 valid questions parsed.")

        return questions

    except Exception as e:
        raise RuntimeError(f"Error generating clarification questions: {str(e)}")
