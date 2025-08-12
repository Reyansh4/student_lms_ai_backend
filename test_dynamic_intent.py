#!/usr/bin/env python3
"""
Test script for Dynamic Intent Detection System
"""

import asyncio
import json
from app.agents.dynamic_intent_classifier import dynamic_intent_classifier
from app.agents.dynamic_action_handlers import dynamic_action_handlers

async def test_dynamic_intent_classification():
    """Test the dynamic intent classifier"""
    
    print("🧠 Testing Dynamic Intent Classification System")
    print("=" * 50)
    
    # Test cases with different contexts
    test_cases = [
        {
            "prompt": "Ask more questions about this activity in MCQ",
            "context": "User has Human Body quiz active",
            "expected_intent": "ask_more_questions"
        },
        {
            "prompt": "1. b) Skin 2. b) Cerebellum",
            "context": "User in Human Body quiz session",
            "expected_intent": "answer_questions"
        },
        {
            "prompt": "Start a new chemistry quiz",
            "context": "No current activity",
            "expected_intent": "create_activity"
        },
        {
            "prompt": "How did I do on the quiz?",
            "context": "User completed quiz",
            "expected_intent": "review_answers"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['context']}")
        print(f"Prompt: '{test_case['prompt']}'")
        print(f"Expected: {test_case['expected_intent']}")
        
        try:
            # Mock conversation history
            conversation_history = [
                {"role": "user", "content": "Start the Human Body quiz"},
                {"role": "assistant", "content": "Activity started! Activity ID: 123"}
            ]
            
            # Mock current activity
            current_activity = {
                "id": "123",
                "name": "Human Body Quiz",
                "category": {"name": "Biology"},
                "sub_category": {"name": "Anatomy"}
            }
            
            # Classify intent
            result = await dynamic_intent_classifier.classify_intent_with_context(
                prompt=test_case["prompt"],
                conversation_history=conversation_history,
                current_activity=current_activity,
                user_id="test_user"
            )
            
            actual_intent = result.get("intent")
            confidence = result.get("confidence")
            context_used = result.get("context_used")
            
            print(f"✅ Actual: {actual_intent}")
            print(f"🎯 Confidence: {confidence}")
            print(f"🧠 Context: {context_used}")
            
            # Check if intent matches expectation
            if actual_intent == test_case["expected_intent"]:
                print("✅ PASS - Intent matched expectation!")
            else:
                print(f"❌ FAIL - Expected {test_case['expected_intent']}, got {actual_intent}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 40)

async def test_dynamic_action_handlers():
    """Test the dynamic action handlers"""
    
    print("\n🚀 Testing Dynamic Action Handlers")
    print("=" * 50)
    
    # Test state
    test_state = {
        "prompt": "Ask more questions about this activity in MCQ",
        "details": {"additionalProp1": {}},
        "db": None,
        "messages": [],
        "user_id": "test_user"
    }
    
    # Test context
    test_context = {
        "activity_id": "123",
        "context_used": "User has active Human Body quiz",
        "additional_context": {}
    }
    
    # Test different intents
    test_intents = ["ask_more_questions", "answer_questions", "continue_activity"]
    
    for intent in test_intents:
        print(f"\n🎯 Testing Intent: {intent}")
        
        try:
            result = await dynamic_action_handlers.handle_intent(
                intent=intent,
                state=test_state,
                context=test_context
            )
            
            message = result.get("result", {}).get("message", "No message")
            print(f"✅ Response: {message[:100]}...")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)

async def main():
    """Main test function"""
    print("🚀 Starting Dynamic Intent Detection System Tests")
    print("=" * 60)
    
    try:
        # Test intent classification
        await test_dynamic_intent_classification()
        
        # Test action handlers
        await test_dynamic_action_handlers()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 