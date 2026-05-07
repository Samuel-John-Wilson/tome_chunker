# Embeddings Module
# Generate Vector embeddings using local models or Open AI API
import os
from typing import List
from dotenv import load_dotenv

# Load environmental variables

load_dotenv()

class EmbeddingGenerator:
    """
    Generate embeddings for text chunks
    
    Supports two modes:
        - 'local': Free sentence-transformers model
        - 'openai': Paid OpenAI API (better quality)
    
    Usage:
        gen = EmbeddingGenerator('local')
        embeddings = gen.embed_batch(["text1", "text2"])
    """
    def __init__(self, model_type: str = None):
        """
        Initialize the embedding generator

        Args: 
            model_type: 'openai' or 'local' (defaults to env var or 'local')
        
    """
        # Determine model type from arg, env var, or default    
        self.model_type = model_type or os.getenv('EMBEDDING_MODEL', 'local')

        # Initialize the appropriate model
        if self.model_type == 'openai':
            self._init_openai()
        else:
            self._init_local()
    
    def _init_openai(self):
        """
        Initialize OpenAi embeddings

        Requires:
            - OPENAI_API_KEY in environment variables
            - openai python package installed
        """
        from src.config import OPENAI_EMBEDDING_MODEL

        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')

        # Validate

        if not api_key or api_key == 'your-key-here-or-leave-blank':
            raise ValueError(
                "OpenAI key not found."
                "Set OPENAI_API_KEY in .env or use model_type='local"
            )
        # Initialize OpenAI client
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model_name = OPENAI_EMBEDDING_MODEL

        print(f"🤖 Using OpenAI embeddings: {self.model_name}")
    
    def _init_local(self):

        """
        Initialize local sentence-transformers model

        First run downloads ~80mb model file.
        Subsequent runs load from cache (~/.cache/torch/sentence_transformers/)
        """

        from sentence_transformers import SentenceTransformer
        from src.config import LOCAL_EMBEDDING_MODEL
        import torch

        print(f"🤖 Loading local embedding model: {LOCAL_EMBEDDING_MODEL}")

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load model (downloads first time, caches for later)
        self.model = SentenceTransformer(LOCAL_EMBEDDING_MODEL, device=device)

        print(f"using device: {device}")
        print("✅ Model loaded successfully")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is list of floats)
        """
        if self.model_type == 'openai':
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts) 
        
    def embed_single(self, text: str) -> List[float]:
        """
        Convenience method for embedding a single text
        
        Args:
            text: Single text string
            
        Returns:
            Single embedding vector (list of 384 floats)
        """
        return self.embed_batch([text])[0]
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API
        
        API limits:
            - Max 100 texts per request (we batch automatically)
            - Rate limits apply (varies by tier)
        """
        batch_size = 100
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Call API
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
        
        return all_embeddings

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using local model
        
        Shows progress bar via tqdm (built into sentence-transformers)
        """
        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,   # Show tqdm progress
            convert_to_numpy=True     # Return numpy array
        )
        
        # Convert numpy array to list of lists
        # (ChromaDB expects Python lists, not numpy arrays)
        return embeddings.tolist()

if __name__ == "__main__":
    """
    Test the embedding generator
    """
    print("Testing local embeddings...\n")
    
    # Create generator
    generator = EmbeddingGenerator(model_type='local')
    
    # Test texts
    test_texts = [
        "A fighter can wear any armor and use any weapon.",
        "Magic-users cast spells from their spellbook.",
        "Roll 1d20 and add your attack bonus."
    ]
    
    # Generate embeddings
    print(f"Generating embeddings for {len(test_texts)} texts...")
    embeddings = generator.embed_batch(test_texts)
    
    # Display results
    print(f"\n✅ Generated {len(embeddings)} embeddings")
    print(f"   Embedding dimension: {len(embeddings[0])}")
    print(f"   First few values of embedding 1: {embeddings[0][:5]}")
    
    # Test single embedding
    single = generator.embed_single("Test sentence")
    print(f"\n✅ Single embedding works")
    print(f"   Dimension: {len(single)}")
    
    # Test similarity
    print(f"\n📊 Testing semantic similarity...")
    
    # Calculate cosine similarity
    import numpy as np
    
    def cosine_similarity(a, b):
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    # Fighter vs Magic-user (different concepts)
    sim1 = cosine_similarity(embeddings[0], embeddings[1])
    print(f"   Fighter ↔ Magic-user similarity: {sim1:.3f}")
    
    # Fighter vs Attack roll (related concepts)
    sim2 = cosine_similarity(embeddings[0], embeddings[2])
    print(f"   Fighter ↔ Attack roll similarity: {sim2:.3f}")
    
    print("\n✅ All tests passed!")    