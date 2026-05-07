from src.pdf_extractor import PDFExtractor
from src.toc_parser import parse_table_of_contents
from src.chunker import RuleChunker
from src.embeddings import EmbeddingGenerator

# Extract and chunk
extractor = PDFExtractor('data/ACKSII_Revised_Rulebook.pdf')
pages = extractor.extract(start_page=1, end_page=20)

toc = parse_table_of_contents(pages[:10])
chunker = RuleChunker(toc_mapping=toc)
chunks = chunker.chunk_pages(pages)

# Generate embeddings
gen = EmbeddingGenerator('local')
texts = [chunk['text'] for chunk in chunks]

print(f"Generating embeddings for {len(texts)} chunks...")
embeddings = gen.embed_batch(texts)

print(f"\n✅ Generated {len(embeddings)} embeddings")
print(f"   Total size: {len(embeddings) * len(embeddings[0]) * 4 / 1024 / 1024:.1f} MB")
# Each float = 4 bytes