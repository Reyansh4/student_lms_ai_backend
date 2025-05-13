import os
from openai import AsyncOpenAI
import aiofiles  # For async file I/O

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TEMPLATE_PATH = "app/agent/templates/activity/final_description.md"

async def generate_final_description(activity_details: dict, clarification_qa: list[dict]) -> str:
    try:
        # Read the .md template
        async with aiofiles.open(TEMPLATE_PATH, mode="r") as f:
            template = await f.read()

        # Format the clarification Q&A
        qa_block = "\n".join(
            [f"Q{i+1}: {pair['question']}\nA{i+1}: {pair['answer']}" for i, pair in enumerate(clarification_qa)]
        )

        # Format the activity details as a JSON-like block
        formatted_details = (
            f'{{\n'
            f'    "name": "{activity_details.get("name", "")}",\n'
            f'    "description": "{activity_details.get("description", "")}",\n'
            f'    "level": "{activity_details.get("level", "")}",\n'
            f'    "category_name": "{activity_details.get("category_name", "")}",\n'
            f'    "sub_category_name": "{activity_details.get("sub_category_name", "")}"\n'
            f'}}'
        )

        # Fill the template with formatted input
        prompt = template.format(
            activity_details=formatted_details,
            clarification_qa=qa_block
        )

        # Send prompt to OpenAI
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert educational activity designer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(f"Error generating final activity description: {e}")
