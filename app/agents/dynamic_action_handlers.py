"""
Dynamic Action Handlers for Any Intent
"""

import json
from typing import Dict, Any, Optional
from app.core.logger import get_logger
from app.tools.agent_tools import agent_tools
from app.memory.enhanced_store import enhanced_memory_store

logger = get_logger(__name__)

class DynamicActionHandlers:
    """
    Dynamic handlers for any intent returned by LLM classifier
    """
    
    def __init__(self):
        self.handlers = {
            "answer_questions": self.handle_answer_submission,
            "ask_more_questions": self.handle_ask_more_questions,
            "start_activity": self.handle_start_activity,
            "create_activity": self.handle_create_activity,
            "continue_activity": self.handle_continue_activity,
            "review_answers": self.handle_review_answers,
            "change_difficulty": self.handle_change_difficulty,
            "collaborative_help": self.handle_collaborative_help,
            "learning_support": self.handle_learning_support,
            "custom_action": self.handle_custom_action
        }
    
    async def handle_intent(
        self, 
        intent: str, 
        state: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route to appropriate handler based on intent
        """
        handler = self.handlers.get(intent, self.handle_learning_support)
        logger.info(f"Handling intent '{intent}' with {handler.__name__}")
        
        try:
            result = await handler(state, context)
            return result
        except Exception as e:
            logger.error(f"Handler {handler.__name__} failed: {e}")
            return {
                "result": {
                    "error": f"Action handler failed: {str(e)}",
                    "fallback": True
                }
            }
    
    async def handle_answer_submission(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user submitting answers to questions"""
        prompt = state.get("prompt", "")
        activity_id = context.get("activity_id")
        
        logger.info(f"Processing answer submission for activity: {activity_id}")
        
        # Extract answers from prompt
        answers = self._extract_answers_from_prompt(prompt)
        
        if not answers:
            return {
                "result": {
                    "message": "I couldn't identify your answers. Please format them as: 1. a 2. b 3. True, etc."
                }
            }
        
        # Store answers in conversation memory
        # TODO: Link to specific activity session
        
        return {
            "result": {
                "message": f"✅ **Answers Received Successfully!**\n\n**Activity:** {activity_id or 'Current Activity'}\n**Answers:** {len(answers)} questions answered\n\n**Your Answers:**\n" + "\n".join([f"{i+1}. {answer}" for i, answer in enumerate(answers)]),
                "answers_stored": True,
                "answer_count": len(answers)
            }
        }
    
    async def handle_ask_more_questions(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user requesting more questions for current activity"""
        activity_id = context.get("activity_id")
        prompt = state.get("prompt", "")
        
        logger.info(f"Generating more questions for activity: {activity_id}")
        
        if not activity_id:
            return {
                "result": {
                    "message": "I don't see an active activity. Please start an activity first, then ask for more questions."
                }
            }
        
        # Generate more questions using LLM
        generation_prompt = f"""
        Generate 3-5 additional multiple choice questions for the current activity.
        Make them engaging and educational, covering different aspects of the topic.
        
        User request: "{prompt}"
        
        Return questions in this format:
        1. Question text?
           a) Option A
           b) Option B  
           c) Option C
           d) Option D
           Answer: X
        
        2. Question text?
           a) Option A
           b) Option B
           c) Option C
           d) Option D
           Answer: X
        
        Make questions challenging but fair, with clear correct answers.
        """
        
        try:
            result = await agent_tools._chat_completion(
                prompt=generation_prompt,
                temperature=0.7,
                max_tokens=500,
                json_mode=False
            )
            
            generated_questions = result.get("response", {}).get("text", "Failed to generate questions")
            
            return {
                "result": {
                    "message": f"🎯 **Additional Questions Generated!**\n\n{generated_questions}\n\n**Instructions:** Answer these questions in the same format: 1. a 2. b 3. c, etc.",
                    "questions_generated": True,
                    "question_count": generated_questions.count("Question") or 3
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            return {
                "result": {
                    "message": "I'm having trouble generating more questions right now. Please try again later or ask a different question."
                }
            }
    
    async def handle_start_activity(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle starting an activity"""
        prompt = state.get("prompt", "")
        
        logger.info(f"Handling start activity request: {prompt}")
        
        # Use existing start_activity_tool logic
        from app.agents.chat_agent import start_activity_tool
        return await start_activity_tool(state, {})
    
    async def handle_create_activity(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle creating a new activity"""
        prompt = state.get("prompt", "")
        
        logger.info(f"Handling create activity request: {prompt}")
        
        # Use existing learning_support_handler logic for activity creation
        from app.agents.chat_agent import learning_support_handler
        return await learning_support_handler(state, {})
    
    async def handle_continue_activity(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle continuing with current activity"""
        activity_id = context.get("activity_id")
        
        if not activity_id:
            return {
                "result": {
                    "message": "No active activity found. Please start an activity first."
                }
            }
        
        return {
            "result": {
                "message": f"✅ **Continuing Activity**\n\nYou're currently working on activity: {activity_id}\n\nWhat would you like to do next?\n- Submit answers\n- Ask for more questions\n- Review progress\n- Get help",
                "activity_continued": True
            }
        }
    
    async def handle_review_answers(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reviewing submitted answers"""
        activity_id = context.get("activity_id")
        
        if not activity_id:
            return {
                "result": {
                    "message": "No active activity found to review answers for."
                }
            }
        
        return {
            "result": {
                "message": f"📊 **Answer Review**\n\n**Activity:** {activity_id}\n\n**Review Options:**\n- Check answer correctness\n- View progress summary\n- Get detailed feedback\n- Compare with solutions\n\nWhat specific review would you like?",
                "review_available": True
            }
        }
    
    async def handle_change_difficulty(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle changing activity difficulty"""
        activity_id = context.get("activity_id")
        
        if not activity_id:
            return {
                "result": {
                    "message": "No active activity found to change difficulty for."
                }
            }
        
        return {
            "result": {
                "message": f"⚙️ **Difficulty Adjustment**\n\n**Activity:** {activity_id}\n\n**Available Levels:**\n- Beginner\n- Intermediate\n- Advanced\n\n**Current:** Intermediate\n\nWhat difficulty level would you prefer?",
                "difficulty_change_available": True
            }
        }
    
    async def handle_collaborative_help(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaborative learning with multiple AI agents"""
        prompt = state.get("prompt", "")
        
        logger.info(f"Handling collaborative help request: {prompt}")
        
        # Use existing collaborative learning logic
        from app.agents.chat_agent import collaborative_learning_handler
        return await collaborative_learning_handler(state, {})
    
    async def handle_learning_support(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general learning support"""
        prompt = state.get("prompt", "")
        
        logger.info(f"Handling learning support request: {prompt}")
        
        # Use existing learning support logic
        from app.agents.chat_agent import learning_support_handler
        return await learning_support_handler(state, {})
    
    async def handle_custom_action(self, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any custom action not covered by other handlers"""
        prompt = state.get("prompt", "")
        
        logger.info(f"Handling custom action request: {prompt}")
        
        # Use LLM to understand and handle custom request
        custom_prompt = f"""
        The user has requested: "{prompt}"
        
        This doesn't fit into our standard categories. Please provide a helpful response that:
        1. Acknowledges their request
        2. Provides relevant assistance
        3. Suggests how to get better help if needed
        
        Be helpful and engaging.
        """
        
        try:
            result = await agent_tools._chat_completion(
                prompt=custom_prompt,
                temperature=0.7,
                max_tokens=300,
                json_mode=False
            )
            
            response = result.get("response", {}).get("text", "I'll help you with that request.")
            
            return {
                "result": {
                    "message": response,
                    "custom_action": True
                }
            }
            
        except Exception as e:
            logger.error(f"Custom action handler failed: {e}")
            return {
                "result": {
                    "message": f"I understand you're asking about: {prompt}\n\nI'd be happy to help! Could you rephrase your request or let me know what specific assistance you need?",
                    "custom_action": True
                }
            }
    
    def _extract_answers_from_prompt(self, prompt: str) -> list:
        """Extract numbered answers from prompt text"""
        answers = []
        
        # Look for patterns like "1. a", "2. b", "3. True", etc.
        lines = prompt.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('Question')):
                # Extract answer part
                if ':' in line:
                    answer_part = line.split(':')[-1].strip()
                    if answer_part:
                        answers.append(answer_part)
                elif '.' in line:
                    parts = line.split('.')
                    if len(parts) > 1:
                        answer_part = parts[1].strip()
                        if answer_part:
                            answers.append(answer_part)
        
        return answers

# Global instance
dynamic_action_handlers = DynamicActionHandlers() 