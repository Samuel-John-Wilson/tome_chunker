"""Configuration settings for the application.
   Centralize all magic numbers and settings here for easy maintenance and readability."""

# Text cleaning settings
MIN_LINE_LENGTH = 3  # Minimum number of characters in a line to be considered valid
REMOVE_EXCESSIVE_WHITESPACE = True  # Whether to remove excessive whitespace from text

# Chunking parameters
CHUNK_SIZE = 1000  # Target characters per chunk
CHUNK_OVERLAP = 200  # Characters to overlap between chunks
MIN_CHUNK_SIZE = 100  # Don't create chunks smaller than this

# Section detection
SECTION_MARKERS = [
    "Chapter",
    "CHAPTER",
    "Part",
    "PART",
    "Section",
    "SECTION"
]