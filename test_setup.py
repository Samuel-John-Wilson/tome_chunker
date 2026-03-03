print("Testing imports...")

try:
    import pdfminer
    print("✅ pdfminer.six")
except ImportError:
    print("❌ pdfminer.six")

try:
    import chromadb
    print("✅ chromadb")
except ImportError:
    print("❌ chromadb")

try:
    import sentence_transformers
    print("✅ sentence-transformers")
except ImportError:
    print("❌ sentence-transformers")

print("\nSetup complete!")