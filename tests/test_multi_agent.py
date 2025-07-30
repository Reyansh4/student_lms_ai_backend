#!/usr/bin/env python3
"""
Test script for the multi-agent system
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.agents.multi_agent_system import multi_agent_system

async def test_multi_agent_system():
    """Test the multi-agent system with various scenarios"""
    
    print("🤖 Testing Multi-Agent Learning System")
    print("=" * 50)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Collaborative Learning - Math",
            "input": "Help me understand calculus derivatives with examples and practice problems",
            "type": "collaborative"
        },
        {
            "name": "Single Agent - Subject Expert",
            "input": "Ask the subject expert to explain quantum physics concepts",
            "type": "single_agent"
        },
        {
            "name": "Exercise Design",
            "input": "Create a practice quiz about photosynthesis for high school students",
            "type": "collaborative"
        },
        {
            "name": "Visual Learning",
            "input": "Show me a diagram of the water cycle with explanations",
            "type": "collaborative"
        },
        {
            "name": "Learning Coach",
            "input": "I'm struggling with motivation to study. Can the learning coach help me?",
            "type": "single_agent"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 30)
        print(f"Input: {test_case['input']}")
        print("\nProcessing...")
        
        try:
            if test_case['type'] == 'collaborative':
                result = await multi_agent_system.collaborative_learning_session(
                    test_case['input']
                )
                print(f"✅ Response:\n{result['combined_response']}")
            else:
                # For single agent, determine which agent to use
                if "subject expert" in test_case['input'].lower():
                    agent = "subject_expert"
                elif "learning coach" in test_case['input'].lower():
                    agent = "learning_coach"
                else:
                    agent = "tutor"
                
                result = await multi_agent_system.single_agent_consultation(
                    agent, test_case['input']
                )
                print(f"✅ Response from {agent}:\n{result['response']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)

async def test_agent_specific_functions():
    """Test individual agent capabilities"""
    
    print("\n🔬 Testing Individual Agent Capabilities")
    print("=" * 50)
    
    agents_to_test = [
        ("tutor", "Explain the concept of machine learning in simple terms"),
        ("subject_expert", "What are the key principles of thermodynamics?"),
        ("exercise_designer", "Design a practice exercise for learning Python loops"),
        ("evaluator", "How would you assess a student's understanding of algebra?"),
        ("learning_coach", "What study strategies work best for memorizing vocabulary?"),
        ("visual_learning_specialist", "Create a flowchart showing the scientific method")
    ]
    
    for agent_name, prompt in agents_to_test:
        print(f"\n🧠 Testing {agent_name.replace('_', ' ').title()}")
        print("-" * 30)
        print(f"Prompt: {prompt}")
        
        try:
            response = await multi_agent_system.get_agent_response(agent_name, prompt)
            print(f"✅ Response:\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "-" * 30)

async def main():
    """Main test function"""
    print("🚀 Starting Multi-Agent System Tests")
    print("=" * 60)
    
    # Test collaborative learning
    await test_multi_agent_system()
    
    # Test individual agents
    await test_agent_specific_functions()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 