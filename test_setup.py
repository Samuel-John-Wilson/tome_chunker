
"""Test that all dependencies are installed correctly"""

print("Testing imports...\n")

try:
    import pdfminer
    print("✅ pdfminer.six")
except ImportError as e:
    print(f"❌ pdfminer.six: {e}")

try:
    import chromadb
    print("✅ chromadb")
except ImportError as e:
    print(f"❌ chromadb: {e}")

try:
    import sentence_transformers
    print("✅ sentence-transformers")
except ImportError as e:
    print(f"❌ sentence-transformers: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv")
except ImportError as e:
    print(f"❌ python-dotenv: {e}")

try:
    import tqdm
    print("✅ tqdm")
except ImportError as e:
    print(f"❌ tqdm: {e}")

print("\n✅ All dependencies installed successfully!")
