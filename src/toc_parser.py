# table of contents parser
# Extracts section names and page numbers from the table of contents page(s) of a PDF

import re
from typing import List, Dict, Tuple

def parse_table_of_contents(pages: List[Dict]) -> Dict[int, str]:
    # Parse ToC to map page numbers to section names
    page_to_section = {}
    toc_entries = []

    print("📋 Searching for Table of Contents...")

    for page in pages[:10]: # Check first 10 pages for ToC
        text = page['text']
        page_num = page['page_num']

        if 'TABLE OF CONTENTS' in text.upper() or 'CONTENTS' in text[:200].upper():
            print(f"Found ToC on page {page_num}")

            # Extract entries from page

            entries = _extract_toc_entries(text)
            toc_entries.extend(entries)

            # Toc might span multiple pages, so keep looking
            continue
        if toc_entries and not _looks_like_toc(text):
            break

    for entry_name, entry_page in toc_entries:
        page_to_section[entry_page] = entry_name

    if page_to_section:
        print(f"✅ Parsed {len(page_to_section)} sections from ToC")
    else:
        print("⚠️  No ToC found - will use text-based section detection")
    
    return page_to_section

def _extract_toc_entries(text: str) -> List[Tuple[str, int]]:
    """
    Extract ToC entries from run-together text
    
    ACKS II format: "Credits 2Introduction 7About the Game 7..."
    Numbers ARE the delimiters between entries!
    """
    entries = []
    
    # Remove watermark junk first
    text = text.replace('Sam Wilson (Order #45732978)', '')
    text = text.replace('TABLE OF CONTENTS', '')
    
    # Strategy: Split on pattern "Number followed by Capital Letter"
    # This marks the boundary: "Credits 2Introduction" 
    #                                    ^ split here
    
    # Find all positions where a number is followed by a capital letter
    # Pattern: digit(s) + optional space + capital letter
    split_pattern = r'(\d+)(?=\s*[A-Z])'
    
    # Split but keep the numbers
    parts = re.split(split_pattern, text)
    
    # parts will be: ['...junk...', '2', 'Introduction', '7', 'About the Game', '7', ...]
    # Pattern: [junk, number, text, number, text, number, text, ...]
    
    # Process in pairs: (text, number)
    i = 0
    while i < len(parts) - 1:
        # Skip until we find a number
        if not parts[i].strip().isdigit():
            i += 1
            continue
        
        page_num_str = parts[i].strip()
        
        # Next part should be the section name
        if i + 1 < len(parts):
            section_text = parts[i + 1]
            
            # Clean up section name
            section_name = section_text.strip()
            
            # Remove any trailing numbers or junk
            # Section name should be mostly letters
            section_name = re.sub(r'\d+$', '', section_name).strip()
            section_name = re.sub(r'[^\w\s:,\-\'()?&]', ' ', section_name)
            section_name = ' '.join(section_name.split())
            
            # Validate
            if section_name and len(section_name) > 2 and len(section_name) < 60:
                try:
                    page_num = int(page_num_str)
                    if page_num > 0 and page_num < 600:  # Reasonable page range
                        if _is_valid_section_name(section_name):
                            entries.append((section_name, page_num))
                except ValueError:
                    pass
        
        i += 2  # Move to next number
    
    return entries

def _try_parse_line(line: str) -> List[Tuple[str, int]]:
    """
    Try to parse a single line for ToC entry
    Returns list (might be empty, might have one entry)
    """
    results = []
    
    # Skip short lines
    if len(line.strip()) < 5:
        return results
    
    # Pattern 1: Name [dots/blocks] Number
    match = re.search(
        r'^([A-Za-z\s:,\-\'()?]+?)\s*[\.…\-\u2500-\u259F█�]{2,}\s*(\d+)\s*$',
        line
    )
    if match:
        section_name = match.group(1).strip()
        page_num = int(match.group(2))
        if _is_valid_section_name(section_name):
            results.append((section_name, page_num))
            return results
    
    # Pattern 2: Name [spaces] Number
    match = re.search(
        r'^([A-Za-z\s:,\-\'()?]+?)\s{3,}(\d+)\s*$',
        line
    )
    if match:
        section_name = match.group(1).strip()
        page_num = int(match.group(2))
        if _is_valid_section_name(section_name):
            results.append((section_name, page_num))
    
    return results

def _is_valid_section_name(name: str) -> bool:
    """Filter out false positive ToC entries"""
    
    # Must contain at least one letter
    if not any(c.isalpha() for c in name):
        return False
    
    # Length check
    if len(name) < 3 or len(name) > 60:
        return False
    
    # Must start with letter or number
    if name and not (name[0].isalpha() or name[0].isdigit()):
        return False
    
    # Skip entries that are mostly numbers
    if len(name) > 0:
        letter_count = sum(c.isalpha() for c in name)
        if letter_count < 3:  # Need at least 3 letters
            return False
    
    # Common junk
    junk_words = ['TABLE OF CONTENTS', 'ACKS', 'AUTARCH', 'COPYRIGHT']
    name_upper = name.upper()
    for junk in junk_words:
        if junk in name_upper:
            return False
    
    return True

def _looks_like_toc(text: str) -> bool:
    # Check if page looks like it's part of the ToC

     # Count lines with dots and numbers (ToC pattern)
    lines = text.split('\n')
    toc_pattern_count = 0
    
    for line in lines:
        # Contains dots and ends with number
        if '.' in line and re.search(r'\d+\s*$', line):
            toc_pattern_count += 1
    
    # If > 3 lines match ToC pattern, probably ToC
    return toc_pattern_count > 3


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    """
    Test the ToC parser
    
    Usage:
        python src/toc_parser.py <path_to_pdf>
    """
    import sys
    from pdf_extractor import PDFExtractor
    
    if len(sys.argv) != 2:
        print("Usage: python src/toc_parser.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Extract first 10 pages (where ToC usually is)
    print("Extracting PDF pages...")
    extractor = PDFExtractor(pdf_path)
    pages = extractor.extract(start_page=1, end_page=10)
    
    # Parse ToC
    print("\nParsing Table of Contents...")
    toc_mapping = parse_table_of_contents(pages)
    
    # Display results
    if toc_mapping:
        print("\n" + "="*60)
        print("Table of Contents Mapping:")
        print("="*60)
        
        for page_num in sorted(toc_mapping.keys()):
            print(f"Page {page_num:3d}: {toc_mapping[page_num]}")
        
        print("="*60)
        print(f"\nTotal sections: {len(toc_mapping)}")
    else:
        print("\n❌ No ToC entries found")
        print("This could mean:")
        print("  - PDF doesn't have a ToC")
        print("  - ToC format doesn't match our patterns")
        print("  - ToC is after page 10")
