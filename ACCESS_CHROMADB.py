#!/usr/bin/env python3
"""
Quick script to access and query ChromaDB (Vector Database)
Usage: python ACCESS_CHROMADB.py
"""

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

def access_chromadb():
    """Access and explore the ChromaDB vector database"""
    
    print("=" * 60)
    print("ChromaDB Vector Database Access")
    print("=" * 60)
    
    # Initialize embeddings
    print("\n1. Initializing embeddings model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("   ✓ Embeddings model loaded")
    
    # Load the vector database
    persist_dir = './medical_db/'
    if not os.path.exists(persist_dir):
        print(f"\n❌ Error: Database directory not found at {persist_dir}")
        return
    
    print(f"\n2. Loading ChromaDB from {persist_dir}...")
    try:
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
        print("   ✓ Vector database loaded")
    except Exception as e:
        print(f"   ❌ Error loading database: {e}")
        return
    
    # Get collection info
    collection = vectorstore._collection
    doc_count = collection.count()
    print(f"\n3. Database Statistics:")
    print(f"   Total documents: {doc_count}")
    
    if doc_count == 0:
        print("\n⚠️  Database is empty. Run the app to populate it from the PDF.")
        return
    
    # Interactive query
    print("\n" + "=" * 60)
    print("Interactive Query Mode")
    print("=" * 60)
    print("Enter medical queries to search the database.")
    print("Type 'exit' to quit, 'stats' for database info\n")
    
    while True:
        query = input("Enter your query: ").strip()
        
        if query.lower() == 'exit':
            print("\nGoodbye!")
            break
        elif query.lower() == 'stats':
            print(f"\nDatabase Statistics:")
            print(f"  Total documents: {doc_count}")
            print(f"  Database location: {os.path.abspath(persist_dir)}")
            continue
        elif not query:
            continue
        
        # Search
        print(f"\n🔍 Searching for: '{query}'...")
        try:
            results = vectorstore.similarity_search(query, k=5)
            
            if results:
                print(f"\n✓ Found {len(results)} results:\n")
                for i, doc in enumerate(results, 1):
                    print(f"{'─' * 60}")
                    print(f"Result {i}:")
                    print(f"{'─' * 60}")
                    # Show first 300 characters
                    content = doc.page_content[:300]
                    print(f"Content: {content}...")
                    if len(doc.page_content) > 300:
                        print(f"        ... (truncated, total length: {len(doc.page_content)} chars)")
                    
                    if doc.metadata:
                        print(f"Metadata: {doc.metadata}")
                    print()
            else:
                print("No results found.")
        except Exception as e:
            print(f"❌ Error during search: {e}")

def view_all_documents():
    """View all documents in the database (first 10)"""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vectorstore = Chroma(
        persist_directory='./medical_db/',
        embedding_function=embeddings
    )
    
    collection = vectorstore._collection
    doc_count = collection.count()
    
    print(f"\nTotal documents: {doc_count}")
    print("\nFetching first 10 documents...\n")
    
    # Get all documents (limited to 10 for display)
    try:
        results = collection.get(limit=10)
        
        if results and results.get('documents'):
            for i, doc in enumerate(results['documents'][:10], 1):
                print(f"{'=' * 60}")
                print(f"Document {i}")
                print(f"{'=' * 60}")
                print(f"Content: {doc[:500]}...")
                if results.get('metadatas') and results['metadatas'][i-1]:
                    print(f"Metadata: {results['metadatas'][i-1]}")
                print()
        else:
            print("No documents found in database.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--view-all':
        view_all_documents()
    else:
        access_chromadb()


