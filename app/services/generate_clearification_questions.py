import os
from typing import List
import aiofiles
from app.core.azure_config import load_azure_config
from app.services.azure_chat import AzureChat

# Path to the markdown template for prompting
TEMPLATE_PATH = "app/agent/templates/activity/clarification_questions.md"

async def generate_clarification_questions(activity_details: dict) -> List[str]:
    try:
        # Read the template
        async with aiofiles.open(TEMPLATE_PATH, mode="r") as f:
            template = await f.read()

        # Replace placeholder with actual activity details
        filled_prompt = template.replace("{activity_dictionary}", str(activity_details))

        # Initialize Azure Chat with educational activity designer system message
        chat = AzureChat(
            system_message="You are an educational activity designer. Your task is to generate relevant clarification questions based on activity details. Focus on understanding requirements, identifying gaps, and ensuring clear expectations for implementation.",
            temperature=0.7
        )

        # Generate questions using Azure OpenAI (async version)
        response = await chat.achat(filled_prompt)

        # Extract questions formatted like: 1. What is...? 2. How does...?
        questions = [
            line.split(". ", 1)[1].strip()
            for line in response.splitlines()
            if line.strip().startswith(tuple(f"{i}." for i in range(1, 6)))
        ]

        if len(questions) < 5:
            raise ValueError("Fewer than 5 valid questions parsed.")

        return questions

    except Exception as e:
        raise RuntimeError(f"Error generating clarification questions: {str(e)}")
