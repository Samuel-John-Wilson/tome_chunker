# PDF Extractor 

from io import StringIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from typing import List, Dict
import re

# Import configuration settings
from src.config import MIN_LINE_LENGTH

def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF file using pdfminer.six."""
    
    # Create a StringIO object to hold the extracted text
    output = StringIO()
    
    # Configure LAParams (Layout Parameters)
    # These control how pdfminer interprets the PDF layout

    laparams = LAParams(
        line_margin=0.5   # Distance between lines
        word_margin=0.1   # Distance between words
        char_margin=0.1   # Distance between characters
        boxes_flow=0.5    # How much to consider text as flowing in a block
        detect_vertical=False  # Whether to detect vertical text 
    )

    # Open PDF and extract text
    with open(pdf_path, 'rb') as fp: # rb = read binary
        extract_text_to_fp(
            fp, # input file
            output, #output buffer
            laparams=laparams, # layout parameters
            output_type='text', # we want plain text output
            codec='utf-8' # encoding
        )
    # Get output from buffer
    return output.getvalue()

"""
- `with open()` automatically closes files (context manager)
- `'rb'` means read binary (PDFs are binary files)
- `StringIO` is like a file, but in memory
- Type hints (`: str`) help with code clarity
"""

# 2: Clean extracted text

def _clean_text(text: str) -> str:
    """Clean extracted text by removing unwanted characters and normalizing whitespace."""
    # Remove excessive whitespace
    # re.sub(pattern, replacement, string)
    # Pattern '\n\s*\n' means: newline + any whitespace + newline
    # Replace with exactly two newlines

    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Split into individual lines
    lines = text.split('\n')

    # Filter out short lines (less than MIN_LINE_LENGTH characters)

    cleaned_lines = [
        line for line in lines if len(line.strip()) >= MIN_LINE_LENGTH
    ]

    # Join lines back together
    return '\n'.join(cleaned_lines)

# 3: Main Extractor Class

 """
    Main class for PDF extraction
    
    Why a class?
        - Encapsulates extraction logic
        - Can maintain state (like current page)
        - Easy to extend with more methods
    """
class PDFExtractor:

    def __init__(self, pdf_path: str):
        # store the path
        self.pdf_path = pdf_path
        # Initialize storage for pages
        self.pages = []

    def extract(self) -> List[Dict[str, any]]:
        # Extract text and split into pages
        # Returns a list of page dictionaries

        # Print what we're doing
        print(f"Extracting text from {self.pdf_path}...")

        # Extract text
        full_text = extract_text(self.pdf_path)

        # Split by form feed character (page break)
        # pdfminer inserts '\f' between pages
        raw_pages = full_text.split('\f')

        # Process each page

        pages_data = []
        for page_num, page_text in enumerate(raw_pages, start=1):
            # skip empty pages
            if not page_text.strip():
                continue
            # Clean the page text
            cleaned_text = _clean_text(page_text)
            # create page dictionary
            pages_data.append({'page_num' : page_num, 
                               'text': cleaned_text,
                               'meta_data': {
                                   'source': self.pdf_path,
                                   'page': page_num
                               } 
                            })
            # print results
            print(f"Extracted {len(pages_data)} pages")
        return pages_data
    
# 4: Testing / Debug Section

if __name__ == "__main__":
    #This section only runs when we execute this file directly (not imported as a module)

    import sys
    # Check if a PDF path was provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python src/pdf_extractor.py <path_to_pdf>")
        sys.exit(1)
    else:
        pdf_path = sys.argv[1]

    # Create an instance of PDFExtractor
    extractor = PDFExtractor(pdf_path)
    # Extract pages
    pages = extractor.extract()
    # Print the first page's text as a sample
    if pages:
        print(f"\nFirst page preview:")
        print("=" * 60)
        print(pages[0]['text'][:500]) # First 500 characters of the first page
        print("...")
    else:
        print("Useage: python pdf_extractor.py <path_to_pdf>")

""" 
- `sys.argv` contains command-line arguments
- `sys.argv[0]` is the script name
- `sys.argv[1]` is the first argument
"""

