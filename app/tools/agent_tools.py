"""
Functional tools for agent operations
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import load_azure_config
from app.core.logger import get_logger
from app.prompts.agent_prompts import *
from app.config.agent_config import *

logger = get_logger(__name__)

class AgentTools:
    """Functional tools for agent operations"""
    
    def __init__(self):
        """Initialize agent tools with Azure configuration"""
        self.azure_config = load_azure_config()
        self.client = self._create_azure_client()
    
    def _create_azure_client(self) -> AzureChatOpenAI:
        """Create Azure OpenAI client"""
        return AzureChatOpenAI(
            openai_api_version=self.azure_config.api_version,
            azure_deployment=self.azure_config.deployment,
            azure_endpoint=self.azure_config.endpoint,
            api_key=self.azure_config.api_key
        )
    
    async def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """Classify user intent using AI"""
        try:
            config = get_intent_classification_config()
            prompt = INTENT_CLASSIFICATION_PROMPT.format(user_input=user_input)
            
            logger.debug(f"Classifying intent for: '{user_input}'")
            
            response = await self._chat_completion(
                prompt=prompt,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                json_mode=config["json_mode"]
            )
            
            result = response.get("response", {})
            logger.debug(f"AI classification response: {result}")
            
            # Fallback classification
            if "text" in result:
                text = result["text"].lower()
                intent = "unknown"
                logger.debug(f"Using fallback classification for text: '{text}'")
                
                # Check for activity management keywords first
                activity_keywords = ["activities", "activity"]
                list_keywords = ["list", "show", "find", "get", "display", "see"]
                
                if any(list_word in text for list_word in list_keywords) and any(activity_word in text for activity_word in activity_keywords):
                    intent = "list-activities"
                    logger.debug("Detected list-activities intent in fallback")
                elif any(w in text for w in ["create", "make", "new"]) and any(w in text for w in ["activities", "activity"]): 
                    intent = "create-activity"
                elif any(w in text for w in ["edit", "update", "modify"]) and any(w in text for w in ["activities", "activity"]): 
                    intent = "edit-activity"
                elif any(w in text for w in ["delete", "remove"]) and any(w in text for w in ["activities", "activity"]): 
                    intent = "delete-activity"
                elif "start" in text: 
                    intent = "start-activity"
                elif any(w in text for w in ["hello","hi","hey"]): 
                    intent = "greetings"
                elif "what can you do" in text: 
                    intent = "capabilities"
                elif any(w in text for w in ["help me learn", "teach me", "explain", "how to", "study", "practice"]): 
                    intent = "learning-support"
                elif any(w in text for w in ["tutor", "expert", "designer", "evaluator", "coach", "visual"]): 
                    intent = "single-agent-consultation"
                elif any(w in text for w in ["generate", "create", "make"]) and any(w in text for w in ["quiz", "lesson", "assignment", "exercise"]): 
                    intent = "generate-activity"
                elif any(w in text for w in ["collaborative", "multiple", "together", "team"]): 
                    intent = "collaborative-learning"
                
                logger.debug(f"Fallback intent: {intent}")
                result = {"intent": intent, "confidence": 0.5}
            
            intent = result.get("intent", "unknown").lower()
            logger.debug(f"Final intent before validation: {intent}")
            
            if not is_valid_intent(intent):
                logger.debug(f"Intent '{intent}' is not valid, setting to unknown")
                intent = "unknown"
            
            confidence = result.get("confidence", 0.0)
            target_agent = result.get("target_agent", None)
            
            # Infer target agent if not specified
            if intent == "single-agent-consultation" and not target_agent:
                target_agent = self._infer_target_agent(user_input)
            
            final_result = {
                "intent": intent,
                "confidence": confidence,
                "target_agent": target_agent
            }
            logger.debug(f"Final classification result: {final_result}")
            return final_result
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {"intent": "unknown", "confidence": 0.0, "target_agent": None}
    
    def _infer_target_agent(self, user_input: str) -> str:
        """Infer target agent from user input"""
        input_lower = user_input.lower()
        patterns = get_agent_selection_patterns()
        
        if any(word in input_lower for word in patterns["subject_specific"]):
            return "subject_expert"
        elif any(word in input_lower for word in patterns["exercise_requests"]):
            return "exercise_designer"
        elif any(word in input_lower for word in patterns["evaluation_requests"]):
            return "evaluator"
        elif any(word in input_lower for word in patterns["learning_strategy"]):
            return "learning_coach"
        elif any(word in input_lower for word in patterns["visual_requests"]):
            return "visual_learning_specialist"
        else:
            return "tutor"
    
    async def extract_activity_details(self, user_input: str) -> Dict[str, Optional[str]]:
        """Extract activity details from user input"""
        try:
            config = get_activity_extraction_config()
            prompt = ACTIVITY_EXTRACTION_PROMPT.format(user_input=user_input)
            
            response = await self._chat_completion(
                prompt=prompt,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                json_mode=config["json_mode"]
            )
            
            result = response.get("response", {})
            
            if "text" in result:
                # Fallback extraction
                return {
                    "activity_name": user_input,
                    "category_name": None,
                    "subcategory_name": None,
                    "additional_details": {}
                }
            
            return {
                "activity_name": result.get("activity_name"),
                "category_name": result.get("category_name"),
                "subcategory_name": result.get("subcategory_name"),
                "additional_details": result.get("additional_details", {})
            }
            
        except Exception as e:
            logger.error(f"Activity extraction failed: {e}")
            return {
                "activity_name": user_input,
                "category_name": None,
                "subcategory_name": None,
                "additional_details": {}
            }
    
    async def get_agent_response(self, agent_name: str, message: str, context: str = "") -> str:
        """Get response from a specific agent"""
        try:
            config = get_agent_config(agent_name)
            system_prompt = self._get_agent_system_prompt(agent_name)
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{context}\n\nUser message: {message}")
            ])
            
            response = await self.client.ainvoke(
                prompt_template.format_messages(
                    context=context,
                    message=message
                )
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting response from {agent_name}: {e}")
            return get_response_template("agent_error", agent_name=agent_name)
    
    def _get_agent_system_prompt(self, agent_name: str) -> str:
        """Get system prompt for specific agent"""
        prompt_map = {
            "tutor": LEAD_TUTOR_SYSTEM_PROMPT,
            "subject_expert": SUBJECT_EXPERT_SYSTEM_PROMPT,
            "exercise_designer": EXERCISE_DESIGNER_SYSTEM_PROMPT,
            "evaluator": LEARNING_EVALUATOR_SYSTEM_PROMPT,
            "learning_coach": LEARNING_COACH_SYSTEM_PROMPT,
            "visual_learning_specialist": VISUAL_LEARNING_SPECIALIST_SYSTEM_PROMPT
        }
        return prompt_map.get(agent_name, LEAD_TUTOR_SYSTEM_PROMPT)
    
    async def _chat_completion(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 512, 
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Generic chat completion function"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            if json_mode:
                system_msg = {"role": "system", "content": "You MUST respond with valid JSON ONLY."}
                messages = [system_msg] + messages
            
            logger.debug(f"Sending messages to AI: {messages}")
            response = await self.client.ainvoke(messages)
            content = response.content.strip()
            logger.debug(f"AI response content: {content}")
            
            try:
                result = {"response": json.loads(content)}
                logger.debug(f"Successfully parsed JSON response: {result}")
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON, using text fallback: {e}")
                result = {"response": {"text": content}}
            
            return result
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    def determine_involved_agents(self, user_input: str) -> List[str]:
        """Determine which agents should be involved based on user input"""
        input_lower = user_input.lower()
        involved_agents = ["tutor"]  # Lead tutor is always involved
        patterns = get_agent_selection_patterns()
        
        # Subject-specific learning
        if any(word in input_lower for word in patterns["subject_specific"]):
            involved_agents.append("subject_expert")
        
        # Exercise or practice requests
        if any(word in input_lower for word in patterns["exercise_requests"]):
            involved_agents.append("exercise_designer")
        
        # Evaluation or feedback requests
        if any(word in input_lower for word in patterns["evaluation_requests"]):
            involved_agents.append("evaluator")
        
        # Learning strategy requests
        if any(word in input_lower for word in patterns["learning_strategy"]):
            involved_agents.append("learning_coach")
        
        # Visual learning requests
        if any(word in input_lower for word in patterns["visual_requests"]):
            involved_agents.append("visual_learning_specialist")
        
        # Complex learning requests
        if len(input_lower.split()) > 10 or any(word in input_lower for word in patterns["complex_requests"]):
            involved_agents.extend(["subject_expert", "learning_coach"])
        
        return list(set(involved_agents))  # Remove duplicates
    
    def combine_agent_responses(self, responses: Dict[str, str], original_input: str) -> str:
        """Combine individual agent responses into a comprehensive answer"""
        if not responses:
            return get_response_template("no_response")
        
        # If only the tutor responded, return their response
        if len(responses) == 1 and "tutor" in responses:
            return responses["tutor"]
        
        # Create comprehensive response
        lead_tutor_guidance = ""
        other_contributions = []
        
        for agent_name, response in responses.items():
            if agent_name == "tutor":
                lead_tutor_guidance = f"**Lead Tutor's Guidance:**\n{response}\n\n"
            else:
                agent_display_name = agent_name.replace("_", " ").title()
                other_contributions.append(f"**{agent_display_name}:**\n{response}\n\n")
        
        other_agent_contributions = "".join(other_contributions)
        
        return COLLABORATIVE_RESPONSE_TEMPLATE.format(
            lead_tutor_guidance=lead_tutor_guidance,
            other_agent_contributions=other_agent_contributions
        )

# Global instance for easy access
agent_tools = AgentTools() 