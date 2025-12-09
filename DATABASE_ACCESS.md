# Database Access Guide

This project uses two databases:

1. **SQLite Chat Database** - Stores conversation history
2. **ChromaDB Vector Database** - Stores medical knowledge embeddings

---

## 1. SQLite Chat Database (`chat_db/medigenius_chats.db`)

### Database Structure

**Tables:**
- `sessions` - Chat sessions
  - `session_id` (TEXT PRIMARY KEY)
  - `created_at` (TIMESTAMP)
  - `last_active` (TIMESTAMP)

- `messages` - Individual messages
  - `id` (INTEGER PRIMARY KEY)
  - `session_id` (TEXT, FOREIGN KEY)
  - `role` (TEXT) - 'user' or 'assistant'
  - `content` (TEXT) - Message content
  - `source` (TEXT) - Source of the response
  - `timestamp` (TIMESTAMP)

### Access Methods

#### Method 1: Using SQLite Command Line

```bash
cd /Users/majhar/medChat/MediGenius
sqlite3 chat_db/medigenius_chats.db
```

**Useful SQLite Commands:**
```sql
-- View all tables
.tables

-- View schema
.schema

-- View all sessions
SELECT * FROM sessions;

-- View all messages
SELECT * FROM messages;

-- View messages for a specific session
SELECT * FROM messages WHERE session_id = 'your-session-id';

-- Count messages per session
SELECT session_id, COUNT(*) as message_count 
FROM messages 
GROUP BY session_id;

-- View recent messages
SELECT * FROM messages 
ORDER BY timestamp DESC 
LIMIT 10;

-- Exit SQLite
.quit
```

#### Method 2: Using Python Script

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('chat_db/medigenius_chats.db')
cursor = conn.cursor()

# Get all sessions
cursor.execute("SELECT * FROM sessions")
sessions = cursor.fetchall()
print("Sessions:", sessions)

# Get all messages
cursor.execute("SELECT * FROM messages")
messages = cursor.fetchall()
print("Messages:", messages)

# Get messages for a specific session
session_id = "your-session-id"
cursor.execute("SELECT * FROM messages WHERE session_id = ?", (session_id,))
session_messages = cursor.fetchall()
print("Session messages:", session_messages)

# Close connection
conn.close()
```

#### Method 3: Using DB Browser for SQLite (GUI Tool)

1. Download DB Browser for SQLite: https://sqlitebrowser.org/
2. Open the application
3. Click "Open Database"
4. Navigate to: `/Users/majhar/medChat/MediGenius/chat_db/medigenius_chats.db`
5. Browse and query the database using the GUI

---

## 2. ChromaDB Vector Database (`medical_db/`)

### Database Structure

The ChromaDB stores:
- Medical document embeddings (from `data/medical_book.pdf`)
- Vector representations for semantic search
- Metadata about documents

### Access Methods

#### Method 1: Using Python Script

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load the vector database
vectorstore = Chroma(
    persist_directory="./medical_db/",
    embedding_function=embeddings
)

# Get collection info
collection = vectorstore._collection
print(f"Total documents: {collection.count()}")

# Search for similar documents
query = "What are the symptoms of diabetes?"
results = vectorstore.similarity_search(query, k=5)

# Print results
for i, doc in enumerate(results):
    print(f"\n--- Document {i+1} ---")
    print(f"Content: {doc.page_content[:200]}...")
    print(f"Metadata: {doc.metadata}")

# Get retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
docs = retriever.invoke(query)
print(f"\nRetrieved {len(docs)} documents")
```

#### Method 2: Using ChromaDB Client Directly

```python
import chromadb
from chromadb.config import Settings

# Connect to the persistent database
client = chromadb.PersistentClient(path="./medical_db/")

# List all collections
collections = client.list_collections()
print("Collections:", [c.name for c in collections])

# Get a collection (default collection name)
collection = client.get_collection(name="langchain")

# Query the collection
results = collection.query(
    query_texts=["What are diabetes symptoms?"],
    n_results=5
)

# Print results
for i, (id, doc, metadata) in enumerate(zip(
    results['ids'][0], 
    results['documents'][0], 
    results['metadatas'][0]
)):
    print(f"\n--- Result {i+1} ---")
    print(f"ID: {id}")
    print(f"Content: {doc[:200]}...")
    print(f"Metadata: {metadata}")

# Get collection count
print(f"\nTotal documents in collection: {collection.count()}")
```

#### Method 3: Access via SQLite (ChromaDB uses SQLite internally)

```bash
cd /Users/majhar/medChat/MediGenius
sqlite3 medical_db/chroma.sqlite3
```

**Note:** ChromaDB's internal SQLite structure is complex. It's better to use the ChromaDB API or Python scripts.

---

## Quick Access Scripts

### View Chat History Script

Create `view_chat_history.py`:

```python
import sqlite3
from datetime import datetime

def view_chat_history():
    conn = sqlite3.connect('chat_db/medigenius_chats.db')
    cursor = conn.cursor()
    
    # Get all sessions
    cursor.execute("""
        SELECT s.session_id, s.created_at, s.last_active,
               COUNT(m.id) as message_count
        FROM sessions s
        LEFT JOIN messages m ON s.session_id = m.session_id
        GROUP BY s.session_id
        ORDER BY s.last_active DESC
    """)
    
    sessions = cursor.fetchall()
    print(f"\n{'='*60}")
    print(f"Total Sessions: {len(sessions)}")
    print(f"{'='*60}\n")
    
    for session_id, created_at, last_active, msg_count in sessions:
        print(f"Session ID: {session_id}")
        print(f"Created: {created_at}")
        print(f"Last Active: {last_active}")
        print(f"Messages: {msg_count}")
        
        # Get messages for this session
        cursor.execute("""
            SELECT role, content, source, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        for role, content, source, timestamp in messages:
            print(f"  [{role.upper()}] ({timestamp}): {content[:100]}...")
            if source:
                print(f"    Source: {source}")
        print("-" * 60)
    
    conn.close()

if __name__ == "__main__":
    view_chat_history()
```

### Query Vector Database Script

Create `query_vector_db.py`:

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def query_medical_db(query, k=5):
    """Query the medical vector database"""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vectorstore = Chroma(
        persist_directory="./medical_db/",
        embedding_function=embeddings
    )
    
    collection = vectorstore._collection
    print(f"Total documents in database: {collection.count()}\n")
    
    # Search
    results = vectorstore.similarity_search(query, k=k)
    
    print(f"Query: {query}")
    print(f"Found {len(results)} results:\n")
    
    for i, doc in enumerate(results, 1):
        print(f"{'='*60}")
        print(f"Result {i}")
        print(f"{'='*60}")
        print(f"Content: {doc.page_content[:500]}...")
        if doc.metadata:
            print(f"Metadata: {doc.metadata}")
        print()
    
    return results

if __name__ == "__main__":
    query = input("Enter your medical query: ")
    query_medical_db(query)
```

---

## Database Locations

- **Chat Database:** `/Users/majhar/medChat/MediGenius/chat_db/medigenius_chats.db`
- **Vector Database:** `/Users/majhar/medChat/MediGenius/medical_db/`

---

## Backup Databases

### Backup Chat Database
```bash
cp chat_db/medigenius_chats.db chat_db/medigenius_chats.db.backup
```

### Backup Vector Database
```bash
cp -r medical_db/ medical_db_backup/
```

---

## Reset Databases

### Clear Chat History
```bash
rm chat_db/medigenius_chats.db
# The database will be recreated on next app startup
```

### Rebuild Vector Database
```bash
rm -r medical_db/
# The database will be recreated from data/medical_book.pdf on next app startup
```


