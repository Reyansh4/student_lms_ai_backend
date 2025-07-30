#!/usr/bin/env python3
"""
Test script for the hierarchical memory system
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

async def test_hierarchical_memory():
    """Test the hierarchical memory system with various scenarios"""
    
    print("🧠 Testing Hierarchical Memory System")
    print("=" * 60)
    
    from app.memory.hierarchical_memory import HierarchicalMemory
    from app.memory.enhanced_store import enhanced_memory_store
    
    # Initialize hierarchical memory
    hierarchical_memory = HierarchicalMemory(window_size=3, k=3)
    
    print("\n📝 Test 1: Basic Memory Operations")
    print("-" * 40)
    
    # Test basic memory operations
    session_id = "test_session_1"
    
    # Add some messages
    test_messages = [
        ("Please remember my User ID is AX-7890.", "I'll remember your User ID as AX-7890."),
        ("Let's chat about the weather. It's very sunny today.", "Yes, it's a beautiful sunny day!"),
        ("I'm planning to go for a walk later.", "That sounds like a great plan for a sunny day!"),
        ("What's the capital of France?", "The capital of France is Paris."),
        ("Can you remind me of my User ID?", "Your User ID is AX-7890.")
    ]
    
    for i, (user_input, ai_response) in enumerate(test_messages, 1):
        print(f"\n📝 Message {i}:")
        print(f"User: {user_input}")
        print(f"Assistant: {ai_response}")
        
        hierarchical_memory.add_message(user_input, ai_response, session_id)
        
        # Get context after each message
        context = hierarchical_memory.get_context("What's my User ID?", session_id)
        print(f"\n🔍 Context after message {i}:")
        print(context[:200] + "..." if len(context) > 200 else context)
    
    print("\n📊 Memory Statistics:")
    stats = hierarchical_memory.get_memory_stats(session_id)
    print(f"Working Memory Messages: {stats['working_memory']['message_count']}")
    print(f"Long-term Memory Messages: {stats['long_term_memory']['message_count']}")
    print(f"Total Messages: {stats['total_messages']}")
    
    print("\n📝 Test 2: Enhanced Store Integration")
    print("-" * 40)
    
    # Test enhanced store
    session = enhanced_memory_store.get_or_create_session("test_user_123")
    
    # Add messages through enhanced store
    enhanced_messages = [
        ("Remember that I prefer dark mode for all applications.", "I'll remember your preference for dark mode."),
        ("What's 2+2?", "2+2 equals 4."),
        ("I'm allergic to peanuts.", "I'll remember that you're allergic to peanuts."),
        ("What's my preference for applications?", "You prefer dark mode for all applications.")
    ]
    
    for i, (user_input, ai_response) in enumerate(enhanced_messages, 1):
        print(f"\n📝 Enhanced Message {i}:")
        print(f"User: {user_input}")
        print(f"Assistant: {ai_response}")
        
        enhanced_memory_store.add_message(session.session_id, "user", user_input)
        enhanced_memory_store.add_message(session.session_id, "assistant", ai_response)
        
        # Get hierarchical context
        context = enhanced_memory_store.get_hierarchical_context("What are my preferences?", session.session_id)
        print(f"\n🔍 Enhanced Context after message {i}:")
        print(context[:300] + "..." if len(context) > 300 else context)
    
    print("\n📊 Enhanced Store Statistics:")
    enhanced_stats = enhanced_memory_store.get_memory_stats(session.session_id)
    print(f"Session Messages: {enhanced_stats['session']['session_messages']}")
    print(f"Hierarchical Working Memory: {enhanced_stats['hierarchical']['working_memory']['message_count']}")
    print(f"Hierarchical Long-term Memory: {enhanced_stats['hierarchical']['long_term_memory']['message_count']}")
    
    print("\n📝 Test 3: Promotion Keywords")
    print("-" * 40)
    
    # Test promotion keywords
    promotion_keywords = hierarchical_memory.get_promotion_keywords()
    print(f"Total promotion keywords: {len(promotion_keywords)}")
    print(f"Sample keywords: {promotion_keywords[:10]}")
    
    # Test adding new promotion keyword
    hierarchical_memory.add_promotion_keyword("custom_keyword")
    new_keywords = hierarchical_memory.get_promotion_keywords()
    print(f"Keywords after adding 'custom_keyword': {len(new_keywords)}")
    
    print("\n📝 Test 4: Memory Clear Operations")
    print("-" * 40)
    
    # Test clearing memory
    test_session = "clear_test_session"
    hierarchical_memory.add_message("This should be cleared.", "Response to be cleared.", test_session)
    
    print(f"Before clear - Working memory: {hierarchical_memory.working_memory.get_memory_stats(test_session)['message_count']}")
    print(f"Before clear - Long-term memory: {hierarchical_memory.long_term_memory.get_memory_stats(test_session)['message_count']}")
    
    hierarchical_memory.clear_memory(test_session)
    
    print(f"After clear - Working memory: {hierarchical_memory.working_memory.get_memory_stats(test_session)['message_count']}")
    print(f"After clear - Long-term memory: {hierarchical_memory.long_term_memory.get_memory_stats(test_session)['message_count']}")
    
    print("\n✅ All hierarchical memory tests completed!")

async def test_memory_integration():
    """Test memory integration with chat agent"""
    
    print("\n🤖 Testing Memory Integration with Chat Agent")
    print("=" * 60)
    
    from app.agents.chat_agent import run_agent
    
    # Test scenarios that should trigger memory promotion
    test_scenarios = [
        {
            "name": "User ID Memory",
            "input": {
                "prompt": "Please remember my User ID is AX-7890.",
                "details": {"token": "test_token"},
                "user_id": "memory_test_user",
                "db": None
            }
        },
        {
            "name": "Learning Preference",
            "input": {
                "prompt": "I prefer to learn through visual diagrams and examples.",
                "details": {"token": "test_token"},
                "user_id": "memory_test_user",
                "db": None
            }
        },
        {
            "name": "Allergy Information",
            "input": {
                "prompt": "I'm allergic to peanuts, please remember this.",
                "details": {"token": "test_token"},
                "user_id": "memory_test_user",
                "db": None
            }
        },
        {
            "name": "Memory Recall Test",
            "input": {
                "prompt": "What's my User ID?",
                "details": {"token": "test_token"},
                "user_id": "memory_test_user",
                "db": None
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Test {i}: {scenario['name']}")
        print(f"Input: {scenario['input']['prompt']}")
        
        try:
            result = await run_agent(scenario['input'])
            print(f"✅ Intent: {result.get('intent')}")
            print(f"✅ Session ID: {result.get('session_id')}")
            
            message = result.get('result', {}).get('message', '')
            preview = message[:150] + "..." if len(message) > 150 else message
            print(f"✅ Response: {preview}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Memory integration tests completed!")

async def main():
    """Main test function"""
    print("🚀 Starting Hierarchical Memory Tests")
    print("=" * 60)
    
    # Test hierarchical memory system
    await test_hierarchical_memory()
    
    # Test memory integration with chat agent
    await test_memory_integration()
    
    print("\n✅ All hierarchical memory tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 