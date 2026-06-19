from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

# Load/open the existing ChromaDB which I've already built
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# Ask a question = "How do I post a need on WithMe?"
question = "How do I post a need on WithMe?"

# Find the most relevant chunks
relevant_chunks = db.similarity_search(question, k=3)

# Send question and chunks to Claude
model = ChatAnthropic(model="claude-sonnet-4-6")

context = "\n\n".join([chunk.page_content for chunk in relevant_chunks])

prompt = f"""You are a helpful assistant for WithMe, a community needs platform.
Use the following information to answer the user's question.
Only answer based on the information provided.

Information:
{context}

User question: {question}
"""

response = model.invoke(prompt)
print(response.content)
