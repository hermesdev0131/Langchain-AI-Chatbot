from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Zilliz

# Initialize the OpenAI embeddings with the "text-embedding-3-large" model.
embedding = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=""
)
print("Embeddings loaded")

connection_args={
    "uri": "",  # e.g., "https://your-instance.zillizcloud.com"
    "token": ""
}

# Explicitly set COSINE for both index_params and search_params
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {"M": 8, "efConstruction": 64}
}
search_params = {
    "metric_type": "COSINE",
    "params": {"ef": 10}
}
# Connect to your Zilliz Cloud instance by supplying the URI and token.
vector_store = Zilliz(
        embedding_function=embedding,
        collection_name="ic_0306",
        connection_args=connection_args,
        auto_id=True,
        drop_old=False,           # <--- Let the script drop the old collection
        index_params=index_params,
        search_params=search_params
    )
print("Connected to Zilliz Cloud")

# Example query to check if the vector store is working correctly
results = vector_store.similarity_search("Innovation Campus", k=2)
print("results: ", results)
for doc in results:
    print(doc.page_content)