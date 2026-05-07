
from src.pdf_extractor import PDFExtractor
from src.toc_parser import parse_table_of_contents
from src.chunker import RuleChunker

# Extract PDF
extractor = PDFExtractor('data/ACKSII_Revised_Rulebook.pdf')
pages = extractor.extract(start_page=1, end_page=50)  # Test first 50 pages

# Parse ToC
toc_mapping = parse_table_of_contents(pages[:10])

# Chunk with ToC
chunker = RuleChunker(toc_mapping=toc_mapping)
chunks = chunker.chunk_pages(pages)

all_paragraphs = []
for page in pages:
    paragraphs = chunker._split_into_paragraphs(page['text'])
    all_paragraphs.extend(paragraphs)

para_sizes = [len(p) for p in all_paragraphs]
print(f"\nParagraph Analysis:")
print(f"  Count: {len(para_sizes)}")
print(f"  Average: {sum(para_sizes)/len(para_sizes):.0f} chars")
print(f"  Median: {sorted(para_sizes)[len(para_sizes)//2]}")
print(f"  Max: {max(para_sizes)}")
print(f"  Over 1000 chars: {sum(1 for s in para_sizes if s > 1000)}")

# Analyze results
print(f"\n{'='*60}")
print("Chunking Analysis:")
print('='*60)
print(f"Total chunks: {len(chunks)}")
print(f"Average chunk size: {sum(c['metadata']['char_count'] for c in chunks) / len(chunks):.0f} chars")

# Show section distribution
from collections import Counter
sections = Counter(c['metadata']['section'] for c in chunks)
print(f"\nChunks per section:")
for section, count in sections.most_common():
    print(f"  {section}: {count}")

# Show type distribution
types = Counter(c['metadata']['type'] for c in chunks)
print(f"\nChunks per type:")
for chunk_type, count in types.most_common():
    print(f"  {chunk_type}: {count}")

# Show sample chunk
print(f"\n{'='*60}")
print("Sample Chunk:")
print('='*60)
sample = chunks[10]
print(f"ID: {sample['id']}")
print(f"Page: {sample['metadata']['page']}")
print(f"Section: {sample['metadata']['section']}")
print(f"Type: {sample['metadata']['type']}")
print(f"\nText:\n{sample['text'][:300]}...")
