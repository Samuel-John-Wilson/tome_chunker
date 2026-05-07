
from src.embeddings import EmbeddingGenerator
import time

gen = EmbeddingGenerator('local')

# Create test data
texts = ["This is a test sentence."] * 100

# Time it
start = time.time()
embeddings = gen.embed_batch(texts)
elapsed = time.time() - start

print(f"Processed {len(texts)} texts in {elapsed:.2f}s")
print(f"Rate: {len(texts)/elapsed:.1f} texts/second")
print(f"Per text: {elapsed/len(texts)*1000:.1f}ms")


#Typical performance:**
#- CPU: 100-500 texts/second
#- GPU: 1000+ texts/second (if you have CUDA)
