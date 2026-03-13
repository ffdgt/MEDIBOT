from src.helper import load_pdf_file, text_split, get_embedding_model
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os
import time

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "medbot")

# Step 1 - Load and chunk PDF
print("📄 Loading PDF...")
extracted_data = load_pdf_file("data/")
print(f"✅ Loaded {len(extracted_data)} pages")

print("✂️  Splitting into chunks...")
text_chunks = text_split(extracted_data)
print(f"✅ Created {len(text_chunks)} chunks")

# Step 2 - Load embedding model
print("🤖 Loading embedding model...")
embeddings = get_embedding_model()
print("✅ Embedding model ready")

# Step 3 - Create Pinecone index
print("🌲 Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

# Delete if exists and recreate
existing_indexes = [i.name for i in pc.list_indexes()]
if INDEX_NAME in existing_indexes:
    print(f"⚠️  Index '{INDEX_NAME}' already exists, skipping creation...")
else:
    print(f"🔨 Creating index '{INDEX_NAME}'...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    # Wait for index to be ready
    print("⏳ Waiting for index to be ready...")
    time.sleep(20)
    print("✅ Index created!")

# Step 4 - Store embeddings
print("📤 Uploading embeddings to Pinecone (this may take a few minutes)...")
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    embedding=embeddings,
    index_name=INDEX_NAME
)
print("✅ All embeddings uploaded successfully!")
print(f"🎉 Pinecone index '{INDEX_NAME}' is ready with {len(text_chunks)} chunks!")