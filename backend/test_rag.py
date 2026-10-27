from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


VECTORSTORE_PATH = "vectorstore"


print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Loading FAISS vector store...")

vectorstore = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)

print("RAG system loaded successfully!")


while True:

    question = input("\nAsk a question (type 'exit' to stop): ")

    if question.lower() == "exit":
        break

    results = vectorstore.similarity_search_with_score(
        question,
        k=3
    )

    print("\n========== RETRIEVED DOCUMENTS ==========\n")

    for i, (document, score) in enumerate(
        results,
        start=1
    ):

        print(f"Result {i}")
        print("-" * 50)

        print(document.page_content)

        print(f"\nDistance Score: {score}")

        print("=" * 50)