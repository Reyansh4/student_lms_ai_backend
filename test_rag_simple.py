#!/usr/bin/env python3
"""
Simple RAG System Test Script
This script demonstrates how to test the RAG functionality step by step.
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_rag_workflow():
    """Test the complete RAG workflow"""
    
    print("🚀 Testing RAG System Workflow")
    print("=" * 50)
    
    # Step 1: Login (you'll need to create this user first)
    print("\n1️⃣ Login")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print("Please create a test user first using the registration endpoint")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Create an activity
    print("\n2️⃣ Create Activity")
    activity_data = {
        "name": "Physics Study Session",
        "description": "Study session for physics concepts",
        "category_id": "550e8400-e29b-41d4-a716-446655440000",  # You'll need to use a real category ID
        "sub_category_id": "550e8400-e29b-41d4-a716-446655440001",  # You'll need to use a real subcategory ID
        "difficulty_level": "intermediate",
        "access_type": "global",
        "ai_guide": True,
        "final_description": "Physics study materials"
    }
    
    try:
        response = requests.post(f"{BASE_URL}{API_PREFIX}/activities/", json=activity_data, headers=headers)
        if response.status_code == 201:
            activity = response.json()
            activity_id = activity["id"]
            print(f"✅ Activity created: {activity['name']} (ID: {activity_id})")
        else:
            print(f"❌ Activity creation failed: {response.status_code}")
            print(f"Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Activity creation error: {e}")
        return
    
    # Step 3: Upload a document
    print("\n3️⃣ Upload Document")
    
    # Create a test document
    test_content = """
    Physics Fundamentals
    
    Newton's Laws of Motion:
    1. First Law (Inertia): An object at rest stays at rest unless acted upon by an external force.
    2. Second Law (F=ma): Force equals mass times acceleration.
    3. Third Law (Action-Reaction): For every action, there is an equal and opposite reaction.
    
    Energy and Work:
    - Kinetic Energy: KE = 1/2 * m * v^2
    - Potential Energy: PE = m * g * h
    - Work: W = F * d * cos(θ)
    
    Wave Properties:
    - Frequency: f = 1/T
    - Wavelength: λ = v/f
    - Speed of light: c = 3 × 10^8 m/s
    """
    
    # Save to temporary file
    with open("temp_physics.txt", "w") as f:
        f.write(test_content)
    
    try:
        with open("temp_physics.txt", "rb") as f:
            files = {"file": ("physics_notes.txt", f, "text/plain")}
            data = {
                "description": "Physics fundamentals document",
                "tags": json.dumps(["physics", "newton", "energy"])
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/activities/{activity_id}/documents/upload",
                files=files,
                data=data,
                headers=headers
            )
            
        if response.status_code == 200:
            result = response.json()
            document_id = result["document_id"]
            print(f"✅ Document uploaded: {result['message']}")
            print(f"   Document ID: {document_id}")
            print(f"   Processing status: {result['processing_status']}")
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Document upload error: {e}")
        return
    finally:
        # Clean up temporary file
        if os.path.exists("temp_physics.txt"):
            os.remove("temp_physics.txt")
    
    # Step 4: Wait for processing and get stats
    print("\n4️⃣ Get Document Statistics")
    import time
    time.sleep(3)  # Wait for processing
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/activities/{activity_id}/documents/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Document Stats:")
            print(f"   Total documents: {stats['total_documents']}")
            print(f"   Processed documents: {stats['processed_documents']}")
            print(f"   Total chunks: {stats['total_chunks']}")
        else:
            print(f"❌ Stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    # Step 5: Chat with activity documents
    print("\n5️⃣ Chat with Activity Documents")
    
    chat_questions = [
        "What are Newton's three laws of motion?",
        "How do you calculate kinetic energy?",
        "What is the relationship between frequency and wavelength?"
    ]
    
    for question in chat_questions:
        print(f"\n   Q: {question}")
        
        chat_data = {
            "message": question,
            "session_id": None
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/activities/{activity_id}/documents/chat",
                json=chat_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   A: {result['message'][:100]}...")
                if result.get('sources'):
                    print(f"   Sources: {len(result['sources'])} documents referenced")
            else:
                print(f"   ❌ Chat failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Chat error: {e}")
    
    # Step 6: Chat with specific document
    print(f"\n6️⃣ Chat with Specific Document")
    
    specific_question = "Explain the first law of motion in detail"
    print(f"   Q: {specific_question}")
    
    chat_data = {
        "message": specific_question,
        "session_id": None
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/activities/{activity_id}/documents/{document_id}/chat",
            json=chat_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   A: {result['message'][:100]}...")
            if result.get('sources'):
                print(f"   Sources: {len(result['sources'])} chunks referenced")
        else:
            print(f"   ❌ Chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Chat error: {e}")
    
    print("\n✅ RAG System Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_rag_workflow() 