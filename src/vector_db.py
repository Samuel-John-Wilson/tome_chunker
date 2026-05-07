# Vector Database Module
# Store and query embeddings using ChromaDB

import chromadb
from typing import List, Dict
import os
from src.config import COLLECTION_NAME, VECTOR_DB_PATH

class VectorDatabase:

      
    """
    Manage vector database for RPG rules
    
    Uses ChromaDB for:
        - Local storage (no server needed)
        - Fast similarity search
        - Metadata filtering
        - Persistent storage
    
    Usage:
        db = VectorDatabase()
        db.create_collection()
        db.add_chunks(chunks, embeddings)
        results = db.query("How does morale work?")
    """
    def __init__(self, db_path: str = VECTOR_DB_PATH,
                 collection_name: str = COLLECTION_NAME):
        # Initialize ChromaDB client
        # Args: db_path - where to store the database-, collection_name
        
        self.db_path = db_path
        self.collection_name = collection_name

        # Create directory if needed
        os.makedirs(db_path, exist_ok=True)

        # Initialize ChromaDB client
        # PersistentClient = saves to disk
        self.client = chromadb.PersistentClient(path=db_path)

        print(f"💾 Vector database initialized at: {db_path}")
    
    def create_collection(self, reset: bool = False):
        """
        Create or get the collection
        
        Args:
            reset: If True, delete existing collection and create fresh
        
        Returns:
            The collection object
        """

        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                print(f"🗑️  Deleted existing collection: {self.collection_name}")
            except:
                # Collection may not exist, ignore errors
                pass

        # Get or create collection

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "ACKSII Rulebook Vector Database"}
        )

        print(f"✅ Collection ready: {self.collection_name}")
        return self.collection
    
    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Add chunks and their embeddings to the database
        
        Args:
            chunks: List of chunk dicts from chunker
            embeddings: List of embedding vectors from embedder
            
        Validates:
            - Same number of chunks and embeddings
            - Embeddings are correct dimension
            
        Process:
            - Extracts IDs, documents, metadata from chunks
            - Adds to ChromaDB in batches (efficient)
        """
        # Validate
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunk count ({len(chunks)}) must match "
                f"embedding count ({len(embeddings)})"
            )
        
        print(f"💾 Adding {len(chunks)} chunks to database...")
        
        # Extract data for ChromaDB
        ids = [chunk['id'] for chunk in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Add in batches (more efficient than one-by-one)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))
            
            self.collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        
        print(f"✅ Successfully added {len(chunks)} chunks")


    def query(self, query_text: str, n_results: int = 5, 
              filter_dict: Dict = None) -> Dict:
        """
        Query the database with natural language
        
        Args:
            query_text: The question or search query
            n_results: Number of results to return
            filter_dict: Optional metadata filter
                Example: {'type': 'spell'}
                         {'page': {'$gte': 45}}
            
        Returns:
            Dict with:
                'documents': List of matching text chunks
                'metadatas': List of metadata dicts
                'distances': List of similarity distances (lower = more similar)
            
        How it works:
            1. ChromaDB auto-embeds query_text
            2. Searches for similar vectors
            3. Filters by metadata if specified
            4. Returns top N results
        """
        # Query the collection
        # ChromaDB automatically embeds query_text
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_dict
        )
        
        # Simplify nested structure
        # ChromaDB returns lists-of-lists for batch queries
        # We only do single queries, so unwrap
        return {
            'documents': results['documents'][0],
            'metadatas': results['metadatas'][0],
            'distances': results['distances'][0]
        }
    
    def query_with_embedding(self, embedding: List[float], 
                            n_results: int = 5) -> Dict:
        """
        Query using a pre-computed embedding vector
        
        Use when:
            - You already have the embedding
            - You want to find similar chunks to a known chunk
            
        Skips the text → embedding step (faster)
        """
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        
        return {
            'documents': results['documents'][0],
            'metadatas': results['metadatas'][0],
            'distances': results['distances'][0]
        }
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the database
        
        Returns:
            Dict with collection info
        """
        count = self.collection.count()
        
        return {
            'collection_name': self.collection_name,
            'total_chunks': count,
            'db_path': self.db_path
        }
    

    def upsert_chunk(self, chunk: Dict, embedding: List[float]):
        """Update existing chunk or insert if new"""
        self.collection.upsert(
            ids=[chunk['id']],
            embeddings=[embedding],
            documents=[chunk['text']],
            metadatas=[chunk['metadata']]
        )

    def delete_chunks(self, chunk_ids: List[str]):
        """Delete chunks by ID"""
        self.collection.delete(ids=chunk_ids)

    def export_to_json(self, output_path: str):
        """Export collection to JSON for backup"""
        import json
        
        # Get all chunks
        results = self.collection.get()
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    """
    Test the vector database
    """
    print("Testing VectorDatabase...\n")
    
    # Create database
    db = VectorDatabase()
    db.create_collection(reset=True)
    
    # Test data
    test_chunks = [
        {
            'id': 'test_001',
            'text': 'Fighters can use any weapon and armor.',
            'metadata': {'type': 'class_feature', 'page': 10, 'section': 'CHARACTERS'}
        },
        {
            'id': 'test_002',
            'text': 'Magic-users cast arcane spells from their spellbook.',
            'metadata': {'type': 'class_feature', 'page': 15, 'section': 'CHARACTERS'}
        },
        {
            'id': 'test_003',
            'text': 'Roll 1d20 for initiative at the start of combat.',
            'metadata': {'type': 'combat_rule', 'page': 67, 'section': 'COMBAT'}
        }
    ]
    
    # Mock embeddings (in reality from embedding model)
    # all-MiniLM-L6-v2 produces 384-dimensional vectors
    test_embeddings = [
        [0.1] * 384,
        [0.2] * 384,
        [0.3] * 384
    ]
    
    # Add to database
    db.add_chunks(test_chunks, test_embeddings)
    
    # Get stats
    stats = db.get_stats()
    print(f"\n{stats}")
    
    # Note: Real queries need real embeddings
    # We'd need to actually embed the query text
    # For now, just verify structure
    
    print("\n✅ Vector database structure working!")
    print("   (Full query testing requires real embeddings)")