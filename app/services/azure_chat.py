from typing import List, Optional, Dict, Any
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import AzureChatOpenAI
import os
import json
from datetime import datetime
import sys
import traceback

from app.core.azure_config import load_azure_config

class AzureChat:
    def __init__(
        self,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: str = "You are a helpful AI assistant that provides clear and concise responses."
    ):
        """Initialize the chat using Azure OpenAI."""
        # Store system message
        self.system_message = system_message
        
        # Load Azure configuration
        try:
            self.azure_config = load_azure_config()
        except Exception as e:
            raise Exception(f"Failed to load Azure configuration: {str(e)}")

        # Initialize the Azure OpenAI client
        try:
            self.llm = AzureChatOpenAI(
                openai_api_version=self.azure_config.api_version,
                azure_deployment=self.azure_config.deployment,
                azure_endpoint=self.azure_config.endpoint,
                api_key=self.azure_config.api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Azure OpenAI client: {str(e)}")

        # Create a chat prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # Initialize chat history
        self.chat_history = ChatMessageHistory()

    def _process_response(self, response: str) -> str:
        """Process and clean the model's response."""
        if not response:
            return "I apologize, but I couldn't generate a proper response. Could you please rephrase your question?"

        try:
            # Clean up the response
            response = response.strip()
            
            if not response:
                return "I apologize, but I couldn't generate a proper response. Could you please rephrase your question?"
                
            return response

        except Exception as e:
            return "I apologize, but there was an error processing the response. Please try again."

    def chat(self, message: str) -> str:
        """Send a message to the chat model and get a response (synchronous version)."""
        if not message or message.isspace():
            return "Please provide a valid message."

        try:
            # Format the message
            formatted_message = message.strip()
            
            try:
                # Generate response using Azure OpenAI
                response = self.llm.invoke(
                    self.prompt.format_messages(
                        history=self.chat_history.messages,
                        input=formatted_message
                    )
                )
                
                if not response:
                    raise ValueError("Received empty response from model")
                
                # Add messages to chat history
                self.chat_history.add_user_message(formatted_message)
                self.chat_history.add_ai_message(response.content)
                
                # Process and clean the response
                return self._process_response(response.content)
                
            except Exception as api_error:
                error_msg = str(api_error)
                error_type = type(api_error).__name__
                
                if "401" in error_msg:
                    raise ValueError("Authentication failed. Please check your Azure OpenAI API key.")
                elif "403" in error_msg:
                    raise ValueError("Access denied. Please ensure you have access to the Azure OpenAI service.")
                elif "404" in error_msg:
                    raise ValueError(f"Deployment {self.azure_config.deployment} not found.")
                elif "429" in error_msg:
                    raise ValueError("Rate limit exceeded. Please try again later.")
                else:
                    raise ValueError(f"API call failed (type: {error_type}): {error_msg}")
            
        except Exception as e:
            return f"Error: {str(e)}"

    async def achat(self, message: str) -> str:
        """Send a message to the chat model and get a response (asynchronous version)."""
        if not message or message.isspace():
            return "Please provide a valid message."

        try:
            # Format the message
            formatted_message = message.strip()
            
            try:
                # Generate response using Azure OpenAI
                response = await self.llm.ainvoke(
                    self.prompt.format_messages(
                        history=self.chat_history.messages,
                        input=formatted_message
                    )
                )
                
                if not response:
                    raise ValueError("Received empty response from model")
                
                # Add messages to chat history
                self.chat_history.add_user_message(formatted_message)
                self.chat_history.add_ai_message(response.content)
                
                # Process and clean the response
                return self._process_response(response.content)
                
            except Exception as api_error:
                error_msg = str(api_error)
                error_type = type(api_error).__name__
                
                if "401" in error_msg:
                    raise ValueError("Authentication failed. Please check your Azure OpenAI API key.")
                elif "403" in error_msg:
                    raise ValueError("Access denied. Please ensure you have access to the Azure OpenAI service.")
                elif "404" in error_msg:
                    raise ValueError(f"Deployment {self.azure_config.deployment} not found.")
                elif "429" in error_msg:
                    raise ValueError("Rate limit exceeded. Please try again later.")
                else:
                    raise ValueError(f"API call failed (type: {error_type}): {error_msg}")
            
        except Exception as e:
            return f"Error: {str(e)}"

    def clear_memory(self):
        """Clear the conversation history."""
        self.chat_history.clear() 