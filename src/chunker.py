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

        chunks = [] # list of completed chunks
        current_chunk = [] # paragraphs in the current chunk
        current_length = 0 # character count of the current chunk

        for para in paragraphs:
            para_length = len(para)

            if current_length + para_length > CHUNK_SIZE and current_chunk: # Oversize!

                chunk_text = '\n\n'.join(current_chunk)
                metadata = self._build_metadata(chunk_text, page_num, source)
                chunks.append((chunk_text, metadata))
            # Start new chunk with overlap
            # Keep the last paragraph for context continuity 
                if current_chunk:
                    overlap_text = current_chunk[-1]
                    current_chunk = [overlap_text, para]
                    current_length = len(overlap_text) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
            else: # still room in current chunk
                current_chunk.append(para)
                current_length += para_length
        # process last chunk
        
        # Don't forget the last chunk!
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            
            if len(chunk_text) >= MIN_CHUNK_SIZE:
                # Big enough - save normally
                metadata = self._build_metadata(chunk_text, page_num, source)
                chunks.append((chunk_text, metadata))
            elif chunks:
                # Too small - append to previous chunk
                last_chunk_text, last_metadata = chunks[-1]
                combined_text = last_chunk_text + '\n\n' + chunk_text
                chunks[-1] = (combined_text, last_metadata)
                print(f"⚠️  Merged small final chunk ({len(chunk_text)} chars) into previous chunk")
            else:
                # First AND last chunk, but too small - save it anyway
                # (Better to have something than nothing)
                metadata = self._build_metadata(chunk_text, page_num, source)
                chunks.append((chunk_text, metadata))
                print(f"⚠️  Saved undersized chunk ({len(chunk_text)} chars) - only chunk on page") 
        return chunks


    def _detect_sections(self, text: str):
        # Update current section looking for headers
        # check claude - new plan here.         
