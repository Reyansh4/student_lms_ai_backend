"""
Dynamic Intent Classifier using LLM + Context Awareness
"""

import json
from typing import Dict, Any, List, Optional
from app.core.logger import get_logger
from app.tools.agent_tools import agent_tools
from app.memory.enhanced_store import enhanced_memory_store

logger = get_logger(__name__)

class DynamicIntentClassifier:
    """
    Dynamic intent classification using LLM with conversation context
    """
    
    def __init__(self):
        self.available_actions = [
            "answer_questions",
            "ask_more_questions", 
            "start_activity",
            "create_activity",
            "continue_activity",
            "review_answers",
            "change_difficulty",
            "collaborative_help",
            "learning_support",
            "custom_action"
        ]
    
    async def classify_intent_with_context(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]], 
        current_activity: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent using LLM with full conversation context
        """
        try:
            # Build context-aware prompt for LLM
            context_prompt = self._build_context_prompt(
                prompt, conversation_history, current_activity
            )
            
            logger.info(f"Classifying intent with context for prompt: {prompt[:100]}...")
            
            # Call LLM for dynamic classification
            result = await agent_tools._chat_completion(
                prompt=context_prompt,
                temperature=0.1,
                max_tokens=300,
                json_mode=True
            )
            
            # Parse LLM response
            classification = self._parse_llm_response(result)
            
            # Validate and enhance classification
            enhanced_classification = self._enhance_classification(
                classification, prompt, current_activity
            )
            
            logger.info(f"Intent classified as: {enhanced_classification['intent']} "
                       f"(confidence: {enhanced_classification['confidence']})")
            
            return enhanced_classification
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "learning_support",
                "confidence": 0.0,
                "context_used": f"Fallback due to error: {str(e)}",
                "fallback": True
            }
    
    def _build_context_prompt(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]], 
        current_activity: Optional[Dict[str, Any]]
    ) -> str:
        """Build context-aware prompt for LLM"""
        
        # Extract recent conversation context
        recent_context = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            recent_context = "\n".join([
                f"- {msg['role']}: {msg['content'][:100]}..."
                for msg in recent_messages
            ])
        
        # Build current activity context
        activity_context = "No specific activity"
        if current_activity:
            activity_context = f"""
            - Activity: {current_activity.get('name', 'Unknown')}
            - Category: {current_activity.get('category', {}).get('name', 'Unknown')}
            - Type: {current_activity.get('sub_category', {}).get('name', 'Unknown')}
            - Status: Active
            """
        
        context_prompt = f"""
        Analyze this user request in the context of their conversation history and current activity.
        
        **Current Context:**
        {activity_context}
        
        **Recent Conversation:**
        {recent_context if recent_context else 'No recent conversation'}
        
        **User Request:** "{prompt}"
        
        **Available Actions:**
        1. answer_questions - User is submitting answers to existing questions (e.g., "1. b 2. c 3. True")
        2. ask_more_questions - User wants more questions for current activity (e.g., "ask more questions", "give me more MCQs")
        3. start_activity - User wants to begin a new or existing activity (e.g., "start the quiz", "begin activity")
        4. create_activity - User wants to create a completely new activity (e.g., "create a new quiz", "make an activity")
        5. continue_activity - Continue with current activity progress (e.g., "next question", "continue")
        6. review_answers - Review or get feedback on submitted answers (e.g., "how did I do?", "check my answers")
        7. change_difficulty - Modify current activity difficulty (e.g., "make it harder", "change difficulty")
        8. collaborative_help - Get help from other AI agents (e.g., "get help from tutor", "ask expert")
        9. learning_support - General learning help or explanation (e.g., "explain this", "help me understand")
        10. custom_action - Any other specific action needed
        
        **Context Analysis Guidelines:**
        - If user says "this activity" or "current activity", refer to the active activity above
        - If user is submitting numbered answers (1. a 2. b), classify as answer_questions
        - If user wants "more questions" and has an active activity, classify as ask_more_questions
        - If user explicitly mentions "new", "create", "make", classify as create_activity
        - If user mentions "start" with existing activity name, classify as start_activity
        - Consider conversation flow and user's current state
        
        **Examples:**
        - "1. b 2. c 3. True" → answer_questions
        - "Ask more questions about this activity" → ask_more_questions (if activity active)
        - "Start the Human Body quiz" → start_activity
        - "Create a new chemistry quiz" → create_activity
        - "How did I do on the quiz?" → review_answers
        - "Explain photosynthesis" → learning_support
        
        Return a JSON object with:
        {{
            "intent": "action_name",
            "confidence": 0.95,
            "context_used": "Brief explanation of context analysis",
            "activity_id": "uuid_if_relevant",
            "additional_context": {{"key": "value"}}
        }}
        
        **Important:** Base your classification on the user's request AND the conversation context. Don't just look at keywords in isolation.
        """
        
        return context_prompt
    
    def _parse_llm_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response and extract classification"""
        try:
            if "response" in result and "text" in result["response"]:
                text = result["response"]["text"]
                return json.loads(text)
            elif "response" in result:
                return result["response"]
            else:
                logger.error(f"Unexpected LLM response format: {result}")
                return {"intent": "learning_support", "confidence": 0.0}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {"intent": "learning_support", "confidence": 0.0}
    
    def _enhance_classification(
        self, 
        classification: Dict[str, Any], 
        prompt: str, 
        current_activity: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhance classification with additional context and validation"""
        
        intent = classification.get("intent", "learning_support")
        confidence = classification.get("confidence", 0.0)
        
        # Validate intent is in our allowed list
        if intent not in self.available_actions:
            logger.warning(f"LLM returned unknown intent: {intent}, falling back to learning_support")
            intent = "learning_support"
            confidence = 0.5
        
        # Add activity context if relevant
        activity_id = None
        if current_activity and intent in ["answer_questions", "ask_more_questions", "continue_activity", "review_answers"]:
            activity_id = current_activity.get("id")
        
        # Enhance with additional context
        enhanced = {
            "intent": intent,
            "confidence": confidence,
            "context_used": classification.get("context_used", "Context analysis completed"),
            "activity_id": activity_id,
            "additional_context": classification.get("additional_context", {}),
            "prompt_analyzed": prompt[:100] + "..." if len(prompt) > 100 else prompt
        }
        
        return enhanced

# Global instance
dynamic_intent_classifier = DynamicIntentClassifier() 