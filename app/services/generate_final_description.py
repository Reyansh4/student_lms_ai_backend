import os
from typing import List
import aiofiles
from openai import AsyncOpenAI
from app.core.config import settings

# Path to the markdown template for prompting
TEMPLATE_PATH = "app/agent/templates/activity/final_description.md"

# Set OpenRouter API key and base URL for Claude
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

async def generate_final_description(activity_details: dict, clarification_qa: List[dict]) -> str:
    try:
        # Read the .md template asynchronously
        async with aiofiles.open(TEMPLATE_PATH, mode="r") as f:
            template = await f.read()

        # Format the clarification Q&A
        qa_block = "\n".join(
            [f"Q{i+1}: {pair['question']}\nA{i+1}: {pair['answer']}" for i, pair in enumerate(clarification_qa)]
        )

        # Format activity details in a clean, readable JSON-like format
        formatted_details = (
            f'{{\n'
            f'    "name": "{activity_details.get("name", "")}",\n'
            f'    "description": "{activity_details.get("description", "")}",\n'
            f'    "level": "{activity_details.get("level", "")}",\n'
            f'    "category_name": "{activity_details.get("category_name", "")}",\n'
            f'    "sub_category_name": "{activity_details.get("sub_category_name", "")}"\n'
            f'}}'
        )

        # Fill the prompt template
        prompt = template.format(
            activity_details=formatted_details,
            clarification_qa=qa_block
        )

        # Send the prompt to Claude 3 Haiku via OpenRouter
        response = await client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[
                {"role": "system", "content": "You are an expert educational activity designer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(f"Error generating final activity description: {str(e)}")
