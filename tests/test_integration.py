#!/usr/bin/env python3
"""
Integration test for the multi-agent system with existing chat agent
"""

import asyncio
import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

async def test_chat_agent_integration():
    """Test the chat agent with multi-agent capabilities"""
    
    print("🔗 Testing Chat Agent Integration with Multi-Agent System")
    print("=" * 60)
    
    # Import the chat agent
    from app.agents.chat_agent import run_agent
    
    # Test cases that should trigger multi-agent responses
    test_cases = [
        {
            "name": "Collaborative Learning Request",
            "input": {
                "prompt": "Help me understand calculus derivatives with examples and practice problems",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            },
            "expected_intent": "collaborative-learning"
        },
        {
            "name": "Single Agent Consultation",
            "input": {
                "prompt": "Ask the subject expert about quantum physics",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            },
            "expected_intent": "single-agent-consultation"
        },
        {
            "name": "Learning Support Request",
            "input": {
                "prompt": "I need help studying for my biology exam",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            },
            "expected_intent": "learning-support"
        },
        {
            "name": "Capabilities Request",
            "input": {
                "prompt": "What can you do?",
                "details": {"token": "test_token"},
                "user_id": "test_user_123",
                "db": None
            },
            "expected_intent": "capabilities"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Input: {test_case['input']['prompt']}")
        print(f"Expected Intent: {test_case['expected_intent']}")
        
        try:
            # Run the agent
            result = await run_agent(test_case['input'])
            
            print(f"✅ Actual Intent: {result.get('intent', 'unknown')}")
            print(f"✅ Session ID: {result.get('session_id', 'none')}")
            
            # Check if intent matches expectation
            if result.get('intent') == test_case['expected_intent']:
                print("✅ Intent classification successful!")
            else:
                print(f"⚠️  Intent mismatch: expected {test_case['expected_intent']}, got {result.get('intent')}")
            
            # Show response preview
            message = result.get('result', {}).get('message', 'No message')
            preview = message[:100] + "..." if len(message) > 100 else message
            print(f"📄 Response Preview: {preview}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)

async def test_multi_agent_direct():
    """Test the multi-agent system directly"""
    
    print("\n🤖 Testing Multi-Agent System Directly")
    print("=" * 50)
    
    from app.agents.multi_agent_system import multi_agent_system
    
    # Test collaborative learning
    print("\n📚 Testing Collaborative Learning")
    try:
        result = await multi_agent_system.collaborative_learning_session(
            "Explain photosynthesis with examples and a diagram"
        )
        print(f"✅ Collaborative learning successful")
        print(f"📊 Involved agents: {result.get('involved_agents', [])}")
        print(f"📄 Response length: {len(result.get('combined_response', ''))} characters")
    except Exception as e:
        print(f"❌ Collaborative learning failed: {e}")
    
    # Test single agent consultation
    print("\n🎯 Testing Single Agent Consultation")
    try:
        result = await multi_agent_system.single_agent_consultation(
            "subject_expert", 
            "What are the key principles of thermodynamics?"
        )
        print(f"✅ Single agent consultation successful")
        print(f"🤖 Agent: {result.get('agent', 'unknown')}")
        print(f"📄 Response length: {len(result.get('response', ''))} characters")
    except Exception as e:
        print(f"❌ Single agent consultation failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Integration Tests")
    print("=" * 60)
    
    # Test multi-agent system directly
    await test_multi_agent_direct()
    
    # Test chat agent integration
    await test_chat_agent_integration()
    
    print("\n✅ All integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 