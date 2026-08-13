import chromadb

client = chromadb.PersistentClient(path="chroma_db")


collection = client.get_or_create_collection(
    name="chunks"
)


def store_embeddings(ids, chunks, embeddings, metadatas):
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
def get_collection_count():
    return collection.count()    

def delete_document_chunks(document_id):
    collection.delete(
        where={
            "document_id": document_id
        }
    )