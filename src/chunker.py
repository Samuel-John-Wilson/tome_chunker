# Text Chunking Module
# Split text but preserve context for better understanding by LLMs

from typing import List, Dict, Tuple
import re
from src.config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE, SECTION_MARKERS





class RuleChunker:
    """
    Chunk text for semantic search
    
    Key features:
        - Preserves complete paragraphs (natural boundaries)
        - Tracks section context via ToC mapping
        - Overlaps chunks to prevent rule splitting
        - Classifies chunk types (spell, combat, etc.)
    
    Usage:
        chunker = RuleChunker(toc_mapping={15: "CHARACTERS", ...})
        chunks = chunker.chunk_pages(pages_data)
    """
    
    def __init__(self, toc_mapping: Dict[int, str] = None):
        """
        Initialize the chunker
        
        Args:
            toc_mapping: Optional dict from ToC parser mapping page→section
                        If None, will use text-based section detection
        """
        self.current_section = "Unknown Section"
        self.toc_mapping = toc_mapping or {}
        
        # Build sorted list of section start pages (for inheritance)
        self.section_pages = sorted(self.toc_mapping.keys()) if self.toc_mapping else []
    
    def chunk_pages(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Convert pages into semantically meaningful chunks
        
        Args:
            pages_data: List of page dicts from PDFExtractor
            
        Returns:
            List of chunk dictionaries:
            [
                {
                    'id': 'chunk_0000',
                    'text': 'The rule text...',
                    'metadata': {
                        'source': 'file.pdf',
                        'page': 15,
                        'section': 'CHARACTERS',
                        'preview': 'First 100 chars...',
                        'char_count': 987,
                        'type': 'class_feature'
                    }
                },
                ...
            ]
        """
        chunks = []
        chunk_id = 0
        
        print(f"📝 Chunking {len(pages_data)} pages...")
        if self.toc_mapping:
            print(f"   Using ToC with {len(self.toc_mapping)} sections")
        
        for page_data in pages_data:
            page_num = page_data['page_num']
            text = page_data['text']
            source = page_data['metadata']['source']
            
            # Update section context
            self._update_section(text, page_num)
            
            # Split into paragraphs
            paragraphs = self._split_into_paragraphs(text)
            
            # Create chunks from paragraphs
            page_chunks = self._create_chunks(paragraphs, page_num, source)
            
            # Add to results with IDs
            for chunk_text, metadata in page_chunks:
                chunks.append({
                    'id': f"chunk_{chunk_id:04d}",
                    'text': chunk_text,
                    'metadata': metadata
                })
                chunk_id += 1
        
        print(f"✅ Created {len(chunks)} chunks")
        return chunks
    
    def _update_section(self, text: str, page_num: int):
        """
        Update current section using ToC mapping or text detection
        
        Args:
            text: Page text
            page_num: Current page number
            
        Modifies:
            self.current_section
            
        Strategy:
            1. Check ToC mapping first (most reliable)
            2. Inherit from previous ToC entry
            3. Fall back to text-based detection
        """
        # Priority 1: Direct ToC mapping
        if page_num in self.toc_mapping:
            self.current_section = self.toc_mapping[page_num]
            return
        
        # Priority 2: Inherit from last ToC section
        if self.section_pages:
            section = self._get_section_for_page(page_num)
            if section != "Unknown Section":
                self.current_section = section
                return
        
        # Priority 3: Text-based detection (fallback)
        self._detect_sections_from_text(text)
    
    def _get_section_for_page(self, page_num: int) -> str:
        """
        Get section for a page using ToC inheritance
        
        Example:
            ToC says: page 15="CHARACTERS", page 45="PROFICIENCIES"
            Page 30 inherits "CHARACTERS" (last section before it)
            Page 50 inherits "PROFICIENCIES"
        
        Args:
            page_num: Page to look up
            
        Returns:
            Section name or "Unknown Section"
        """
        # Find the last section that started at or before this page
        for section_page in reversed(self.section_pages):
            if page_num >= section_page:
                return self.toc_mapping[section_page]
        
        return "Unknown Section"
    
    def _detect_sections_from_text(self, text: str):
        """
        Fallback: Detect section from text patterns
        
        Used when ToC parsing fails or page is before ToC
        
        Args:
            text: Page text
            
        Looks for:
            - Known section markers (CHARACTERS, COMBAT, etc.)
            - ALL CAPS lines (likely headers)
        """
        lines = text.split('\n')
        
        # Check first 20 lines (headers usually at top)
        for line in lines[:20]:
            line = line.strip()
            
            if not line:
                continue
            
            # Check known section markers
            if line in SECTION_MARKERS:
                self.current_section = line
                return
            
            # Check for all-caps headers (8-50 characters)
            if (line.isupper() and 
                8 <= len(line) <= 50 and
                any(c.isalpha() for c in line)):
                # Exclude common false positives
                if not any(word in line for word in ['PAGE', 'ACKS', 'AUTARCH', 'PATREON']):
                    self.current_section = line
                    return
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into manageable chunks
        
        ACKS II has very long paragraphs (tables, lists).
        Strategy:
        1. Split on double newlines (paragraphs)
        2. If paragraph > CHUNK_SIZE, split on single newlines
        3. If still too large, split on sentences
        4. If STILL too large, hard-split at CHUNK_SIZE
        """
        from src.config import CHUNK_SIZE
        
        # Step 1: Split on paragraph boundaries
        raw_paragraphs = re.split(r'\n\n+', text)
        raw_paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
        
        final_chunks = []
        
        for para in raw_paragraphs:
            if len(para) <= CHUNK_SIZE:
                # Small enough - keep as-is
                final_chunks.append(para)
                
            elif '\n' in para and len(para) > CHUNK_SIZE:
                # Large paragraph with line breaks - split on single newlines
                lines = para.split('\n')
                lines = [l.strip() for l in lines if l.strip()]
                
                # Group lines to stay under CHUNK_SIZE
                current_group = []
                current_length = 0
                
                for line in lines:
                    line_len = len(line)
                    
                    if current_length + line_len > CHUNK_SIZE and current_group:
                        # Save current group
                        final_chunks.append('\n'.join(current_group))
                        current_group = [line]
                        current_length = line_len
                    else:
                        current_group.append(line)
                        current_length += line_len + 1  # +1 for newline
                
                if current_group:
                    final_chunks.append('\n'.join(current_group))
            
            else:
                # Large block of text - split on sentences
                sentences = self._split_into_sentences(para)
                
                current_group = []
                current_length = 0
                
                for sentence in sentences:
                    sent_len = len(sentence)
                    
                    if current_length + sent_len > CHUNK_SIZE and current_group:
                        final_chunks.append(' '.join(current_group))
                        current_group = [sentence]
                        current_length = sent_len
                    else:
                        current_group.append(sentence)
                        current_length += sent_len
                
                if current_group:
                    final_chunks.append(' '.join(current_group))
        
        # Final safety check - hard-split anything still too large
        verified_chunks = []
        for chunk in final_chunks:
            if len(chunk) <= CHUNK_SIZE * 1.5:  # Allow 50% overage
                verified_chunks.append(chunk)
            else:
                # Hard split at CHUNK_SIZE boundaries
                for i in range(0, len(chunk), CHUNK_SIZE):
                    verified_chunks.append(chunk[i:i + CHUNK_SIZE])
        
        return verified_chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Handles:
        - Regular sentences (. ! ?)
        - Abbreviations (Dr., vs., e.g.)
        - Numbers (3.5, 1.2)
        """
        # Replace abbreviations temporarily
        text = text.replace('Dr.', 'Dr')
        text = text.replace('Mr.', 'Mr')
        text = text.replace('Mrs.', 'Mrs')
        text = text.replace('vs.', 'vs')
        text = text.replace('e.g.', 'eg')
        text = text.replace('i.e.', 'ie')
        text = text.replace('etc.', 'etc')
        
        # Split on sentence boundaries
        # Pattern: period/!/?  followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Also split on semicolons (common in rules)
        expanded_sentences = []
        for sent in sentences:
            if ';' in sent and len(sent) > CHUNK_SIZE:
                parts = sent.split(';')
                expanded_sentences.extend([p.strip() + ';' for p in parts[:-1]])
                expanded_sentences.append(parts[-1].strip())
            else:
                expanded_sentences.append(sent)
        
        return [s.strip() for s in expanded_sentences if s.strip()]

    def _create_chunks(
            self, 
            paragraphs: List[str], 
            page_num: int, 
            source: str
        ) -> List[Tuple[str, Dict]]:
            """
            Group paragraphs into size-appropriate chunks with overlap
            
            This is the core chunking algorithm.
            
            Args:
                paragraphs: List of paragraph strings
                page_num: Current page number
                source: Source file path
                
            Returns:
                List of (chunk_text, metadata) tuples
                
            Algorithm:
                current_chunk = []
                current_length = 0
                
                for each paragraph:
                    if adding it would exceed CHUNK_SIZE:
                        save current_chunk
                        start new chunk with last paragraph (overlap)
                    else:
                        add paragraph to current_chunk
                
                save final chunk (with special handling if too small)
            """
            chunks = []
            current_chunk = []
            current_length = 0
            
            for para in paragraphs:
                para_length = len(para)
                
                # Check if adding this paragraph exceeds target size
                if current_length + para_length > CHUNK_SIZE and current_chunk:
                    # Over limit - save current chunk
                    chunk_text = '\n\n'.join(current_chunk)
                    metadata = self._build_metadata(chunk_text, page_num, source)
                    chunks.append((chunk_text, metadata))
                    
                    # Start new chunk with overlap
                    # Keep last paragraph for context continuity
                    overlap_text = current_chunk[-1]
                    current_chunk = [overlap_text, para]
                    current_length = len(overlap_text) + para_length
                else:
                    # Still room - add to current chunk
                    current_chunk.append(para)
                    current_length += para_length  # Note: += not =
            
            # Handle final chunk
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                
                if len(chunk_text) >= MIN_CHUNK_SIZE:
                    # Big enough - save normally
                    metadata = self._build_metadata(chunk_text, page_num, source)
                    chunks.append((chunk_text, metadata))
                elif chunks:
                    # Too small - merge into previous chunk
                    last_chunk_text, last_metadata = chunks[-1]
                    combined_text = last_chunk_text + '\n\n' + chunk_text
                    chunks[-1] = (combined_text, last_metadata)
                else:
                    # First AND last chunk, but small - save anyway
                    # (Better to have something than nothing)
                    metadata = self._build_metadata(chunk_text, page_num, source)
                    chunks.append((chunk_text, metadata))
            
            return chunks
        
    def _build_metadata(self, chunk_text: str, page_num: int, source: str) -> Dict:
            """
            Build rich metadata for each chunk
            
            Args:
                chunk_text: The chunk text
                page_num: Page number
                source: Source file
                
            Returns:
                Metadata dictionary with all context
                
            Metadata enables:
                - Filtered searches ("show only spells")
                - Context display ("from page 45, COMBAT section")
                - Analytics (chunk size distribution, etc.)
            """
            # Extract preview (first line, truncated)
            first_line = chunk_text.split('\n')[0].strip()
            preview = first_line[:100]
            
            return {
                'source': source,
                'page': page_num,
                'section': self.current_section,
                'preview': preview,
                'char_count': len(chunk_text),
                'type': self._classify_chunk(chunk_text)
            }
        
    def _classify_chunk(self, text: str) -> str:
            """
            Classify chunk type for filtered searching
            
            Args:
                text: Chunk text
                
            Returns:
                Classification string
                
            Types:
                - index: Index pages
                - credits: Backer credits, copyright
                - table_or_mechanic: Tables, dice rolls
                - spell: Magic, spells
                - class_feature: Class abilities
                - combat_rule: Combat mechanics
                - general_rule: Everything else
            """
            text_lower = text.lower()
            
            # Check in order from most to least specific
            
            # Indexes
            if 'index' in text_lower and any(w in text_lower for w in 
                ['general', 'spell', 'monster', 'table']):
                return 'index'
            
            # Credits
            if any(w in text_lower for w in ['patreon', 'backer', 'copyright', 'credits']):
                return 'credits'
            
            # Tables and mechanics (look for dice notation and dots)
            if any(indicator in text for indicator in 
                ['...', 'd20', 'd6', 'd100', 'roll']):
                return 'table_or_mechanic'
            
            # Spells
            if any(w in text_lower for w in ['spell', 'magic', 'cast', 'arcane', 'divine']):
                return 'spell'
            
            # Class features
            if any(w in text_lower for w in ['class', 'level', 'proficiency', 'fighter', 'mage']):
                return 'class_feature'
            
            # Combat rules
            if any(w in text_lower for w in 
                ['combat', 'attack', 'damage', 'initiative', 'morale', 'hp']):
                return 'combat_rule'
            
            # Default
            return 'general_rule'


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    """
    Test the chunker with sample data
    """
    # Sample page data
    test_text = """
CHARACTERS

Creating a character in ACKS II involves several steps. First, you roll 
your ability scores using 3d6 in order.

Strength represents physical power and melee combat ability. A high 
Strength allows you to hit more often and deal more damage in combat.

Dexterity represents agility, reflexes, and ranged combat ability. A 
high Dexterity helps you avoid attacks and improves ranged accuracy.

Intelligence represents reasoning, memory, and learning ability. High 
Intelligence allows spellcasters to learn more spells.
    """
    
    test_pages = [{
        'page_num': 15,
        'text': test_text,
        'metadata': {'source': 'test.pdf'}
    }]
    
    # Test with ToC mapping
    toc_mapping = {15: "CHARACTERS"}
    
    chunker = RuleChunker(toc_mapping=toc_mapping)
    chunks = chunker.chunk_pages(test_pages)
    
    print(f"\nCreated {len(chunks)} chunks from test data:\n")
    for chunk in chunks:
        print(f"{chunk['id']}:")
        print(f"  Section: {chunk['metadata']['section']}")
        print(f"  Type: {chunk['metadata']['type']}")
        print(f"  Length: {chunk['metadata']['char_count']} chars")
        print(f"  Preview: {chunk['metadata']['preview']}")
        print(f"  Text: {chunk['text'][:100]}...\n")
