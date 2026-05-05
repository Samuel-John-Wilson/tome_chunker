"""Configuration settings for the application.
   Centralize all magic numbers and settings here for easy maintenance and readability."""

# Text cleaning settings
MIN_LINE_LENGTH = 3  # Minimum number of characters in a line to be considered valid
REMOVE_EXCESSIVE_WHITESPACE = True  # Whether to remove excessive whitespace from text

# Chunking parameters
CHUNK_SIZE = 1000  # Target characters per chunk
CHUNK_OVERLAP = 200  # Characters to overlap between chunks
MIN_CHUNK_SIZE = 100  # Don't create chunks smaller than this

# Section detection - MANUAL.
# These overridden by Table of Contents parsing
# If your pdf has no ToC, input headings here
SECTION_MARKERS = [
    "CHAPTER",
    "PART",
    "SECTION",
    "CHARACTERS",
    "PROFICIENCIES",
    "SPELLS",
    "COMBAT",
    "ADVENTURES"
    "CAMPAIGNS"
    "MONSTERS"
]


# Embedding Model Settings 

# OpenAI embedding model (if using OpenAI)
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

# Local embedding model (if using sentence-transformers)
# all-MiniLM-L6-v2: Fast, 384 dimensions, good quality
LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ============================================================================
# Vector Database Settings
# ============================================================================

# ChromaDB collection name
COLLECTION_NAME = "acks_ii_rules"

# Where to store the database
VECTOR_DB_PATH = "./output/chroma_db"

