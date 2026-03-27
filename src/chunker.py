# Text Chunking Module
# Split text but preserve context for better understanding by LLMs

from typing import List, Dict
import re
from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE, SECTION_MARKERS





class RuleChunker:
    def __init__(self):
        self.current_section = "unknown section"
        self.current_subsection = ""

    
    def chunk_pages(self, pages_data: List[Dict]) -> List[Dict]:
        chunks = []
        chunk_id = 0

        print(f"📝 Chunking {len(pages_data)} pages...")

        for page_data in pages_data:
            page_num = page_data['page_num']
            text = page_data['text']

            self._detect_sections(text)

            paragraphs = self._split_into_paragraphs(text)

            page_chunks = self._create_chunks(
                paragraphs,
                page_num,
                page_data['metadata']['source']
            )

            for chunk_text, metadata in page_chunks:
                chunks.append({
                    'id': f"chunk_{chunk_id: 04d}", # Unique 4 digit chunk ID
                    'text': chunk_text,
                    'metadata': metadata
                })
                chunk_id += 1
        print(f"✅ Created {len(chunks)} chunks.")
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        # Split text into paragraphs based on double newlines
       # paragraphs = re.split(r'\n\s*\n', text.strip()) - ask claude
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _create_chunks(self, paragraphs: List[str], page_num: int, source: str) -> List[tuple]:
        # Group paragraphs into size-appropriate chunks

        