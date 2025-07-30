"""
Restructured multi-agent system using centralized tools and configuration
"""

import asyncio
from typing import Dict, Any, List
from app.core.logger import get_logger
from app.tools.agent_tools import agent_tools
from app.config.agent_config import get_multi_agent_config, get_response_template
from app.prompts.agent_prompts import COLLABORATIVE_LEARNING_CONTEXT

logger = get_logger(__name__)

class MultiAgentSystem:
    """Restructured multi-agent system for collaborative learning tasks"""
    
    def __init__(self):
        """Initialize the multi-agent system"""
        self.config = get_multi_agent_config()
        logger.info("Multi-agent system initialized")
    
    async def collaborative_learning_session(self, user_input: str, learning_context: str = "") -> Dict[str, Any]:
        """Run a collaborative learning session with multiple agents"""
        logger.info(f"Starting collaborative learning session for: {user_input}")
        
        try:
            # Determine which agents to involve
            involved_agents = agent_tools.determine_involved_agents(user_input)
            logger.debug(f"Involved agents: {involved_agents}")
            
            # Create collaborative context
            collaborative_context = COLLABORATIVE_LEARNING_CONTEXT.format(
                learning_context=learning_context,
                user_input=user_input
            )
            
            # Get responses from involved agents concurrently
            responses = {}
            tasks = []
            
            for agent_name in involved_agents:
                task = self._get_agent_response_async(agent_name, user_input, collaborative_context)
                tasks.append((agent_name, task))
            
            # Execute all agent requests concurrently
            for agent_name, task in tasks:
                try:
                    response = await task
                    responses[agent_name] = response
                    logger.debug(f"Got response from {agent_name}")
                except Exception as e:
                    logger.error(f"Error getting response from {agent_name}: {e}")
                    responses[agent_name] = get_response_template("agent_error", agent_name=agent_name)
            
            # Combine responses into a comprehensive answer
            combined_response = agent_tools.combine_agent_responses(responses, user_input)
            
            return {
                "original_input": user_input,
                "involved_agents": involved_agents,
                "individual_responses": responses,
                "combined_response": combined_response,
                "session_type": "collaborative_learning"
            }
            
        except Exception as e:
            logger.error(f"Collaborative learning session failed: {e}")
            return {
                "original_input": user_input,
                "involved_agents": [],
                "individual_responses": {},
                "combined_response": get_response_template("error"),
                "session_type": "collaborative_learning",
                "error": str(e)
            }
    
    async def single_agent_consultation(self, agent_name: str, user_input: str) -> Dict[str, Any]:
        """Get a response from a single specific agent"""
        logger.info(f"Single agent consultation: {agent_name} for input: {user_input}")
        
        try:
            response = await agent_tools.get_agent_response(agent_name, user_input)
            
            return {
                "agent": agent_name,
                "input": user_input,
                "response": response,
                "session_type": "single_agent"
            }
            
        except Exception as e:
            logger.error(f"Single agent consultation failed: {e}")
            return {
                "agent": agent_name,
                "input": user_input,
                "response": get_response_template("agent_error", agent_name=agent_name),
                "session_type": "single_agent",
                "error": str(e)
            }
    
    async def _get_agent_response_async(self, agent_name: str, message: str, context: str) -> str:
        """Get agent response asynchronously with timeout"""
        try:
            timeout = self.config.get("response_timeout", 30)
            response = await asyncio.wait_for(
                agent_tools.get_agent_response(agent_name, message, context),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting response from {agent_name}")
            return get_response_template("agent_error", agent_name=agent_name)
        except Exception as e:
            logger.error(f"Error getting response from {agent_name}: {e}")
            return get_response_template("agent_error", agent_name=agent_name)
    
    async def process_learning_request(self, user_input: str, learning_context: str = "") -> Dict[str, Any]:
        """Process a learning request with intelligent agent selection"""
        logger.info(f"Processing learning request: {user_input}")
        
        try:
            # For general learning support, use collaborative learning
            if learning_context:
                return await self.collaborative_learning_session(user_input, learning_context)
            else:
                # Default to collaborative learning with focused context
                focused_context = "General learning support request - provide comprehensive educational guidance"
                return await self.collaborative_learning_session(user_input, focused_context)
                
        except Exception as e:
            logger.error(f"Learning request processing failed: {e}")
            return {
                "original_input": user_input,
                "combined_response": get_response_template("error"),
                "session_type": "learning_support",
                "error": str(e)
            }

# Global instance for easy access
multi_agent_system = MultiAgentSystem() 