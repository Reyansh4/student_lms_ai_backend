# RAG System Quick Start Guide

## Summary of Changes Made

✅ **Fixed Response Format**: Removed nested `result` objects from all agent functions
✅ **Added Activity ID**: All responses now include an `activity_id` field (empty string if not applicable)
✅ **Clean Response Structure**: Now returns `{"message": "...", "activity_id": "..."}` instead of `{"result": {"result": {...}}}`

## How to Test the RAG System

### Prerequisites

1. **Start your server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Install dependencies**:
   ```bash
   pip install requests
   ```

3. **Create a test user** (if you don't have one):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User",
       "email": "test@example.com",
       "password": "testpassword123",
       "phone": "1234567890",
       "city": "Test City",
       "country": "Test Country"
     }'
   ```

### Method 1: Use the Test Script

Run the simple test script:
```bash
python test_rag_simple.py
```

This will:
1. ✅ Login with test credentials
2. ✅ Create a test activity
3. ✅ Upload a physics document
4. ✅ Test RAG chat functionality
5. ✅ Show document statistics

### Method 2: Manual Testing with curl

#### Step 1: Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response.

#### Step 2: Create Activity
```bash
curl -X POST "http://localhost:8000/api/v1/activities/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Physics Study Session",
    "description": "Study session for physics concepts",
    "category_id": "YOUR_CATEGORY_ID",
    "sub_category_id": "YOUR_SUBCATEGORY_ID",
    "difficulty_level": "intermediate",
    "access_type": "global",
    "ai_guide": true,
    "final_description": "Physics study materials"
  }'
```

Save the `id` from the response as `ACTIVITY_ID`.

#### Step 3: Upload Document
Create a file `test_physics.txt`:
```
Physics Fundamentals

Newton's Laws:
1. First Law: An object at rest stays at rest unless acted upon by an external force.
2. Second Law: Force equals mass times acceleration (F=ma).
3. Third Law: For every action, there is an equal and opposite reaction.

Energy:
- Kinetic Energy: KE = 1/2 * m * v^2
- Potential Energy: PE = m * g * h
```

Upload it:
```bash
curl -X POST "http://localhost:8000/api/v1/activities/ACTIVITY_ID/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_physics.txt" \
  -F "description=Physics fundamentals document" \
  -F "tags=[\"physics\", \"newton\", \"energy\"]"
```

#### Step 4: Chat with Documents
```bash
curl -X POST "http://localhost:8000/api/v1/activities/ACTIVITY_ID/documents/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "What are Newton\'s three laws of motion?",
    "session_id": null
  }'
```

### Method 3: Test via Agent Chat

You can also test through the agent chat endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "prompt": "Create an art activity",
    "user_id": "YOUR_USER_ID",
    "details": {}
  }'
```

## Expected Response Format

### Before (Problematic):
```json
{
  "intent": "create-activity",
  "result": {
    "result": {
      "message": "✅ Activity created successfully!...",
      "activity_id": "uuid-here"
    }
  }
}
```

### After (Fixed):
```json
{
  "intent": "create-activity",
  "result": {
    "message": "✅ Activity created successfully!...",
    "activity_id": "uuid-here"
  }
}
```

## RAG System Features

### Document Management
- ✅ Upload documents to activities
- ✅ Process and chunk documents
- ✅ Store in vector database
- ✅ Support for PDF, TXT, CSV, JSON

### Chat Functionality
- ✅ Chat with all documents in an activity
- ✅ Chat with specific documents
- ✅ History-aware conversations
- ✅ Source attribution

### API Endpoints
- `POST /{activity_id}/documents/upload` - Upload document
- `GET /{activity_id}/documents` - List documents
- `POST /{activity_id}/documents/chat` - Chat with all documents
- `POST /{activity_id}/documents/{document_id}/chat` - Chat with specific document
- `GET /{activity_id}/documents/stats` - Get statistics

## Troubleshooting

### Common Issues

1. **"No users found in database"**
   - Create a test user using the registration endpoint

2. **"Category not found"**
   - Create categories first or use existing category IDs

3. **"Document upload failed"**
   - Check file format (supported: PDF, TXT, CSV, JSON)
   - Ensure file size is reasonable

4. **"Chat not working"**
   - Wait for document processing to complete
   - Check if documents are marked as `is_processed: true`

### Debug Commands

Check database tables:
```sql
SELECT * FROM documents LIMIT 1;
SELECT * FROM document_chat_sessions LIMIT 1;
```

Check vector store:
```bash
ls -la vector_store/
```

Check uploads:
```bash
ls -la uploads/
```

## Next Steps

After successful testing:

1. **Frontend Integration**: Connect to your frontend application
2. **Production Setup**: Configure production database and Azure OpenAI
3. **Advanced Features**: Add document search, versioning, sharing
4. **Performance Optimization**: Monitor and optimize for large document sets 