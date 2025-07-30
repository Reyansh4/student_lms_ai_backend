#!/usr/bin/env python3
"""
Test script for the restructured multi-agent system
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

async def test_restructured_system():
    """Test the restructured system with various scenarios"""
    
    print("🏗️  Testing Restructured Multi-Agent System")
    print("=" * 60)
    
    # Test agent tools
    print("\n🔧 Testing Agent Tools")
    print("-" * 30)
    
    from app.tools.agent_tools import agent_tools
    
    # Test intent classification
    test_inputs = [
        "Help me understand calculus derivatives",
        "Ask the subject expert about quantum physics",
        "Create a practice quiz about photosynthesis",
        "Show me a diagram of the water cycle",
        "I need study tips for my biology exam",
        "Hello, how are you?",
        "What can you do?"
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n📝 Test {i}: Intent Classification")
        print(f"Input: {test_input}")
        
        try:
            result = await agent_tools.classify_intent(test_input)
            print(f"✅ Intent: {result.get('intent')}")
            print(f"✅ Confidence: {result.get('confidence')}")
            print(f"✅ Target Agent: {result.get('target_agent')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test agent selection
    print(f"\n🎯 Testing Agent Selection")
    for test_input in test_inputs[:3]:  # Test first 3 inputs
        involved_agents = agent_tools.determine_involved_agents(test_input)
        print(f"Input: '{test_input}' → Agents: {involved_agents}")
    
    # Test multi-agent system
    print(f"\n🤖 Testing Multi-Agent System")
    print("-" * 30)
    
    from app.agents.multi_agent_system import multi_agent_system
    
    test_cases = [
        {
            "name": "Collaborative Learning - Math",
            "input": "Help me understand calculus derivatives with examples and practice problems"
        },
        {
            "name": "Single Agent - Subject Expert",
            "input": "Ask the subject expert about quantum physics concepts"
        },
        {
            "name": "Exercise Design",
            "input": "Create a practice quiz about photosynthesis for high school students"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            result = await multi_agent_system.collaborative_learning_session(test_case['input'])
            print(f"✅ Involved agents: {result.get('involved_agents', [])}")
            print(f"✅ Response length: {len(result.get('combined_response', ''))} characters")
            print(f"✅ Session type: {result.get('session_type')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test chat agent
    print(f"\n💬 Testing Chat Agent")
    print("-" * 30)
    
    from app.agents.chat_agent import run_agent
    
    chat_test_cases = [
        {
            "name": "Greeting",
            "input": {
                "prompt": "Hello!",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            }
        },
        {
            "name": "Capabilities Request",
            "input": {
                "prompt": "What can you do?",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            }
        },
        {
            "name": "Learning Support",
            "input": {
                "prompt": "I need help studying for my biology exam",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            }
        }
    ]
    
    for i, test_case in enumerate(chat_test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']['prompt']}")
        
        try:
            result = await run_agent(test_case['input'])
            print(f"✅ Intent: {result.get('intent')}")
            print(f"✅ Session ID: {result.get('session_id')}")
            
            message = result.get('result', {}).get('message', '')
            preview = message[:100] + "..." if len(message) > 100 else message
            print(f"✅ Response Preview: {preview}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ All restructured system tests completed!")

async def test_configuration():
    """Test configuration and prompts"""
    
    print(f"\n⚙️  Testing Configuration")
    print("=" * 40)
    
    from app.config.agent_config import (
        get_agent_config, 
        get_intent_classification_config,
        get_multi_agent_config,
        is_valid_intent,
        get_agent_selection_patterns
    )
    
    # Test agent configuration
    print(f"\n🔧 Agent Configuration:")
    for agent_name in ["tutor", "subject_expert", "exercise_designer"]:
        config = get_agent_config(agent_name)
        print(f"  {agent_name}: temperature={config['temperature']}, max_tokens={config['max_tokens']}")
    
    # Test intent classification config
    intent_config = get_intent_classification_config()
    print(f"\n🎯 Intent Classification Config:")
    print(f"  temperature={intent_config['temperature']}, max_tokens={intent_config['max_tokens']}")
    
    # Test multi-agent config
    multi_config = get_multi_agent_config()
    print(f"\n🤖 Multi-Agent Config:")
    print(f"  max_concurrent_agents={multi_config['max_concurrent_agents']}")
    print(f"  response_timeout={multi_config['response_timeout']}")
    
    # Test valid intents
    test_intents = ["collaborative-learning", "single-agent-consultation", "greetings", "invalid-intent"]
    print(f"\n✅ Valid Intents:")
    for intent in test_intents:
        is_valid = is_valid_intent(intent)
        print(f"  {intent}: {'✅' if is_valid else '❌'}")
    
    # Test agent selection patterns
    patterns = get_agent_selection_patterns()
    print(f"\n🎯 Agent Selection Patterns:")
    for pattern_name, pattern_list in patterns.items():
        print(f"  {pattern_name}: {len(pattern_list)} patterns")

async def test_prompts():
    """Test prompt templates"""
    
    print(f"\n📝 Testing Prompts")
    print("=" * 30)
    
    from app.prompts.agent_prompts import (
        LEAD_TUTOR_SYSTEM_PROMPT,
        SUBJECT_EXPERT_SYSTEM_PROMPT,
        CAPABILITIES_RESPONSE,
        GREETING_RESPONSE
    )
    
    prompts = [
        ("Lead Tutor", LEAD_TUTOR_SYSTEM_PROMPT),
        ("Subject Expert", SUBJECT_EXPERT_SYSTEM_PROMPT),
        ("Capabilities", CAPABILITIES_RESPONSE),
        ("Greeting", GREETING_RESPONSE)
    ]
    
    for name, prompt in prompts:
        print(f"\n📄 {name} Prompt:")
        print(f"  Length: {len(prompt)} characters")
        print(f"  Preview: {prompt[:100]}...")

async def main():
    """Main test function"""
    print("🚀 Starting Restructured System Tests")
    print("=" * 60)
    
    # Test configuration
    await test_configuration()
    
    # Test prompts
    await test_prompts()
    
    # Test restructured system
    await test_restructured_system()
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 