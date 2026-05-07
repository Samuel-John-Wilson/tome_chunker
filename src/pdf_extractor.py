# PDF Extractor 

from io import StringIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from typing import List, Dict
import re

# Import configuration
from src.config import MIN_LINE_LENGTH

def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF file using pdfminer.six."""
    try:
        # Create a StringIO object to hold the extracted text
        output = StringIO()
        
        # Configure LAParams (Layout Parameters)
        # These control how pdfminer interprets the PDF layout

        laparams = LAParams(
            line_margin=0.5,   # Distance between lines
            word_margin=0.1, # Distance between words
            char_margin=2.0,  # Distance between characters
            boxes_flow=0.5,   # How much to consider text as flowing in a block
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
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

"""
- `with open()` automatically closes files (context manager)
- `'rb'` means read binary (PDFs are binary files)
- `StringIO` is like a file, but in memory
- Type hints (`: str`) help with code clarity
"""

# 2: Clean extracted text

def _clean_text(text: str) -> str:
    """Clean extracted text by removing artifacts"""
    
    # Remove watermark
    text = re.sub(r'Sam Wilson \(Order #\d+\)', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Filter out short lines
    lines = text.split('\n')
    cleaned_lines = [
        line for line in lines 
        if len(line.strip()) >= MIN_LINE_LENGTH
    ]
    
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
        

    def extract(self, start_page: int =1, end_page: int =None) -> List[Dict[str, any]]:
        # Extract text and split into pages
        # Returns a list of page dictionaries

        # Print what we're doing
        print(f"Extracting text from {self.pdf_path}...")

        # Extract text
        try:
            full_text = extract_text(self.pdf_path)
        except (FileNotFoundError, ValueError) as e:
            raise e

        # Split by form feed character (page break)
        # pdfminer inserts '\f' between pages
        raw_pages = full_text.split('\f')

        # Process each page

        pages_data = []
        for page_num, page_text in enumerate(raw_pages, start=1):
            # apply page-range filtering
            if page_num < start_page:
                continue
            if end_page is not None and page_num > end_page:
                break
            # skip empty pages
            if not page_text.strip():
                continue
            # Clean the page text
            cleaned_text = _clean_text(page_text)
            # create page dictionary
            pages_data.append({'page_num' : page_num, 
                               'text': cleaned_text,
                               'metadata': {
                                   'source': self.pdf_path,
                                   'page': page_num
                               } 
                            })
            # print results
        if end_page:
            print(f"✅ Extracted pages {start_page}-{end_page} ({len(pages_data)} pages)")
        else:     
            print(f"✅ Extracted {len(pages_data)} pages")
        return pages_data
    
# 4: Testing / Debug Section

if __name__ == "__main__":
    #This section only runs when we execute this file directly (not imported as a module)

    import sys
    # Check if a PDF path was provided as a command-line argument
    if len(sys.argv) != 2:
        print("Useage: python src/pdf_extractor.py <path_to_pdf>")
        sys.exit(1)
    else:
        pdf_path = sys.argv[1]

    # Create an instance of PDFExtractor
    extractor = PDFExtractor(pdf_path)
    # Extract pages
    try:
        pages = extractor.extract()
        # Print the first page's text as a sample
        if pages:
            print(f"\n{'='*60}")
            print(f"First page preview:")
            print('='*60)
            print(pages[0]['text'][:500])
            print("...")
            print('='*60)
            print(f"\nExtracted {len(pages)} total pages")
            print(f"First page has {len(pages[0]['text'])} characters")
        else:
            print("No pages extracted - PDF may be empty or image-based")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

""" 
- `sys.argv` contains command-line arguments
- `sys.argv[0]` is the script name
- `sys.argv[1]` is the first argument
"""

