# test_vector_db_full.py
from src.pdf_extractor import PDFExtractor
from src.toc_parser import parse_table_of_contents
from src.chunker import RuleChunker
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase

print("="*60)
print("FULL PIPELINE TEST")
print("="*60)

# Extract
print("\n1. Extracting PDF...")
extractor = PDFExtractor('data/ACKSII_Revised_Rulebook.pdf')
pages = extractor.extract(start_page=1, end_page=50)

# Parse ToC
print("\n2. Parsing ToC...")
toc = parse_table_of_contents(pages[:10])

# Chunk
print("\n3. Chunking...")
chunker = RuleChunker(toc_mapping=toc)
chunks = chunker.chunk_pages(pages)

# Embed
print("\n4. Generating embeddings...")
embedder = EmbeddingGenerator('local')
texts = [chunk['text'] for chunk in chunks]
embeddings = embedder.embed_batch(texts)

# Store
print("\n5. Storing in database...")
db = VectorDatabase()
db.create_collection(reset=True)
db.add_chunks(chunks, embeddings)

# Query
print("\n6. Testing query...")
print("   (Note: ChromaDB will auto-embed the query)")

results = db.query("What is a level 1 Fighter's attack throw?", n_results=3)

print(f"\n{'='*60}")
print("Query Results:")
print('='*60)

for i, (doc, meta, dist) in enumerate(zip(
    results['documents'],
    results['metadatas'],
    results['distances']
), 1):
    print(f"\n[Result {i}] Distance: {dist:.3f}")
    print(f"Section: {meta['section']}, Page: {meta['page']}")
    print(f"Type: {meta['type']}")
    print(f"\n{doc[:200]}...")
    print("-"*60)

print("\n✅ Full pipeline working!")