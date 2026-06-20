from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()

# Full path to README
readme_path = os.path.join(os.path.dirname(__file__), "README.md")


#  Load the README
loader = TextLoader(readme_path)
document = loader.load()


# Split into smaller chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(document)

print(f"Loaded {len(document)} document(s)")
print(f"Split into {len(chunks)} chunks")
print("---")
print("First chunk preview:")
print(chunks[0].page_content)


# Store chunks in ChromaDB
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

print(f"Stored {len(chunks)} chunks in ChromaDB using OpenAI embeddings!")
