import os
from typing import List
import aiofiles
import json
from app.services.azure_chat import AzureChat

# Path to the markdown template for prompting
TEMPLATE_PATH = "app/agent/templates/activity/final_description.md"

async def generate_final_description(activity_details: dict, clarification_qa: List[dict]) -> str:
    """
    Generate a final description for an activity using Azure OpenAI based on activity details and clarification Q&A.
    
    Args:
        activity_details: Dictionary containing activity information
        clarification_qa: List of dictionaries containing question-answer pairs
        
    Returns:
        str: Generated final description
    """
    try:
        # Read the template file
        async with aiofiles.open(TEMPLATE_PATH, mode="r") as f:
            template = await f.read()

        # Format the clarification Q&A
        qa_block = "\n".join(
            [f"Q{i+1}: {pair['question']}\nA{i+1}: {pair['answer']}" for i, pair in enumerate(clarification_qa)]
        )

        # Format activity details using proper JSON handling
        formatted_details = json.dumps(activity_details, indent=4)

        # Fill the prompt template using string replacement
        filled_prompt = template.replace(
            "```\n   {\n       \"name\": \"[Activity Name]\",\n       \"description\": \"[Original Description]\",\n       \"level\": \"[Activity Level]\",\n       \"category_name\": \"[Category]\",\n       \"sub_category_name\": \"[Sub-category]\"\n   }\n   ```",
            f"```\n{formatted_details}\n```"
        ).replace(
            "```\n   Q1: [Question 1]\n   A1: [Answer 1]\n   \n   Q2: [Question 2]\n   A2: [Answer 2]\n   \n   [Additional Q&A pairs...]\n   ```",
            f"```\n{qa_block}\n```"
        )

        # Initialize AzureChat with a specific system message for activity design
        chat = AzureChat(
            temperature=0.7,
            max_tokens=2000,
            system_message="You are an expert educational activity designer. Your task is to create clear, engaging, and well-structured activity descriptions that help students understand and engage with the learning objectives."
        )

        # Generate the final description using Azure OpenAI
        final_description = await chat.achat(filled_prompt)
        return final_description.strip()

    except Exception as e:
        raise RuntimeError(f"Error generating final activity description: {str(e)}")
