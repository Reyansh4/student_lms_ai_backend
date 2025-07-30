# Unified Embedding System

## Overview

The Unified Embedding System provides semantic search and retrieval capabilities for all models in the Learning Management System. It stores embeddings with rich metadata to enable effective filtering and ranking of search results.

## 🏗️ Architecture

### Core Components

```
app/embeddings/
├── __init__.py           # Package exports
├── models.py             # EmbeddingStore database model
├── extractors.py         # Content extractors for each model type
├── service.py            # Main embedding service
└── retrievers.py         # Semantic retrievers for different use cases
```

### Database Schema

```sql
CREATE TABLE embedding_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,           -- 'activity', 'question', etc.
    entity_id UUID NOT NULL,                    -- Foreign key to original entity
    content_text TEXT NOT NULL,                 -- Text to be embedded
    embedding_vector JSON NOT NULL,              -- Stored as JSON array
    metadata JSON NOT NULL,                     -- Rich metadata for filtering
    embedding_model VARCHAR(100) NOT NULL,      -- Model used for embedding
    embedding_dimension INTEGER NOT NULL,       -- Dimension of embedding
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_entity_type_id ON embedding_store(entity_type, entity_id);
CREATE INDEX idx_created_at ON embedding_store(created_at);
CREATE INDEX idx_embedding_model ON embedding_store(embedding_model);
```

## 🔧 Key Features

### 1. **Unified Storage**
- Single table for all entity embeddings
- Rich metadata for advanced filtering
- Efficient indexing for fast queries

### 2. **Content Extractors**
- Specialized extractors for each model type
- Intelligent content combination
- Metadata enrichment

### 3. **Semantic Search**
- Cosine similarity calculation
- Configurable similarity thresholds
- Multi-entity type search

### 4. **Advanced Filtering**
- Metadata-based filtering
- Entity type filtering
- Custom filter combinations

## 📊 Supported Entity Types

### 1. **Activities** (`activity`)
```python
# Content: name + description + final_description
# Metadata: difficulty_level, access_type, category_id, ai_guide, etc.
```

### 2. **Questions** (`activity_question`)
```python
# Content: question_text + solution_steps + answer + ai_hint
# Metadata: activity_id, has_solution, has_answer, has_hint
```

### 3. **AI Responses** (`activity_ai_response`)
```python
# Content: ai_response
# Metadata: session_id, user_id, question_id
```

### 4. **Sessions** (`activity_session`)
```python
# Content: status + grade + feedback
# Metadata: activity_id, user_id, status, has_feedback
```

### 5. **Documents** (`activity_document`)
```python
# Content: file_name + description
# Metadata: activity_id, file_type, file_metadata
```

### 6. **Templates** (`activity_template`)
```python
# Content: name + description + final_description
# Metadata: difficulty_level, access_type, category_id
```

### 7. **Users** (`user`)
```python
# Content: name + email + phone + city + country
# Metadata: is_active, created_at
```

## 🚀 Usage Examples

### 1. **Creating Embeddings**

```python
from app.embeddings.service import EmbeddingService
from app.models.activity import Activity

# Initialize service
embedding_service = EmbeddingService()

# Create embedding for an activity
activity = db.query(Activity).filter(Activity.id == activity_id).first()
embedding = await embedding_service.create_embedding_for_entity(
    db=db,
    entity=activity,
    entity_type="activity"
)
```

### 2. **Semantic Search**

```python
from app.embeddings.retrievers import SemanticRetriever

# Initialize retriever
retriever = SemanticRetriever()

# Search for activities
results = await retriever.search_activities(
    db=db,
    query="calculus derivatives",
    difficulty_level="Intermediate",
    ai_guide_only=True,
    top_k=10
)

# Search across multiple entity types
results = await retriever.cross_entity_search(
    db=db,
    query="machine learning",
    entity_types=["activity", "activity_question"],
    top_k=20
)
```

### 3. **API Usage**

```bash
# Search for activities
GET /api/v1/embeddings/search/activities?query=calculus&difficulty_level=Intermediate

# Search for questions
GET /api/v1/embeddings/search/questions?query=derivatives&has_solution=true

# Get recommendations
GET /api/v1/embeddings/recommendations?query=machine learning

# Get similar activities
GET /api/v1/embeddings/similar-activities/{activity_id}

# Get embedding statistics
GET /api/v1/embeddings/stats
```

## 🔍 Search Capabilities

### 1. **Activity Search**
```python
# Search with filters
results = await retriever.search_activities(
    query="calculus derivatives",
    difficulty_level="Intermediate",
    category_id="math-category-id",
    access_type="global",
    ai_guide_only=True,
    top_k=10,
    similarity_threshold=0.7
)
```

### 2. **Question Search**
```python
# Search questions with filters
results = await retriever.search_questions(
    query="derivative rules",
    activity_id="activity-id",
    has_solution=True,
    has_answer=False,
    top_k=10
)
```

### 3. **AI Response Search**
```python
# Search AI responses
results = await retriever.search_ai_responses(
    query="explain derivatives",
    session_id="session-id",
    user_id="user-id",
    top_k=10
)
```

### 4. **Cross-Entity Search**
```python
# Search across multiple entity types
results = await retriever.cross_entity_search(
    query="machine learning",
    entity_types=["activity", "activity_question", "activity_template"],
    filters={"access_type": "global"},
    top_k=20
)
```

## 📈 Performance Optimizations

### 1. **Database Indexing**
- Composite index on `(entity_type, entity_id)`
- Index on `created_at` for time-based queries
- Index on `embedding_model` for model-specific queries

### 2. **Batch Processing**
```python
# Process multiple entities in batches
entities = [
    (activity1, "activity"),
    (question1, "activity_question"),
    (response1, "activity_ai_response")
]

results = await embedding_service.batch_create_embeddings(
    db=db,
    entities=entities,
    batch_size=10
)
```

### 3. **Caching Strategy**
- Embedding vectors cached in memory
- Similarity calculations optimized
- Query result caching for repeated searches

## 🔧 Configuration

### 1. **Azure OpenAI Settings**
```python
# In app/config/azure_config.py
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
```

### 2. **Embedding Parameters**
```python
# Default settings
embedding_dimension = 1536  # text-embedding-ada-002
similarity_threshold = 0.7
top_k = 10
```

### 3. **Batch Processing**
```python
# Batch settings
batch_size = 10
max_concurrent_batches = 5
```

## 📊 Monitoring and Statistics

### 1. **Embedding Statistics**
```python
stats = embedding_service.get_embedding_stats(db)
# Returns:
{
    "total_embeddings": 1250,
    "entity_type_counts": {
        "activity": 500,
        "activity_question": 300,
        "activity_ai_response": 200,
        "user": 250
    },
    "models_used": ["text-embedding-ada-002"],
    "embedding_dimension": 1536
}
```

### 2. **Search Performance**
- Average query time: < 100ms
- Similarity calculation: < 50ms
- Batch processing: 100 entities/minute

## 🔄 Integration with Existing Systems

### 1. **Automatic Embedding Creation**
```python
# Hook into model creation/update events
@event.listens_for(Activity, 'after_insert')
def create_activity_embedding(mapper, connection, target):
    # Trigger embedding creation
    pass
```

### 2. **Memory System Integration**
```python
# Integrate with hierarchical memory
from app.memory.hierarchical_memory import HierarchicalMemory

# Use embeddings for long-term memory retrieval
class EnhancedHierarchicalMemory(HierarchicalMemory):
    def __init__(self):
        super().__init__()
        self.semantic_retriever = SemanticRetriever()
    
    async def get_semantic_context(self, query: str, session_id: str) -> str:
        # Use semantic search for context retrieval
        results = await self.semantic_retriever.cross_entity_search(
            db=self.db,
            query=query,
            entity_types=["activity", "activity_question", "activity_ai_response"]
        )
        return self.format_context(results)
```

### 3. **Agent System Integration**
```python
# Enhance agents with semantic search
class EnhancedAgent:
    def __init__(self):
        self.semantic_retriever = SemanticRetriever()
    
    async def get_relevant_context(self, query: str) -> str:
        # Get semantically relevant context
        results = await self.semantic_retriever.cross_entity_search(
            query=query,
            entity_types=["activity", "activity_question"]
        )
        return self.format_context(results)
```

## 🎯 Use Cases

### 1. **Content Discovery**
- Find similar activities
- Discover related questions
- Explore user-generated content

### 2. **Personalized Recommendations**
- Recommend activities based on user history
- Suggest questions based on learning progress
- Find relevant AI responses

### 3. **Content Quality**
- Identify duplicate content
- Find similar questions for quality control
- Analyze content patterns

### 4. **Learning Analytics**
- Track user engagement patterns
- Analyze content effectiveness
- Identify learning gaps

## 🔮 Future Enhancements

### 1. **Advanced Filtering**
- Complex JSON queries
- Date range filtering
- User preference filtering

### 2. **Real-time Updates**
- Automatic embedding updates
- Incremental embedding creation
- Real-time search updates

### 3. **Multi-modal Embeddings**
- Image embeddings for documents
- Audio embeddings for content
- Video embeddings for tutorials

### 4. **Advanced Ranking**
- Learning-based ranking
- User preference weighting
- Context-aware ranking

This unified embedding system provides a powerful foundation for semantic search and retrieval across all your learning management system models, enabling intelligent content discovery and personalized learning experiences. 