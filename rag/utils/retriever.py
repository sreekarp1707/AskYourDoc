from .bm25 import search_bm25
from .chroma_db import collection
from .embeddings import model


def retrieve_chunks(query, user_id, document_id=None, n_results=3):
    query_embedding = model.encode(query).tolist()

    if document_id is None:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={
                "user_id": user_id
            },
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={
                "$and": [
                    {"user_id": user_id},
                    {"document_id": document_id},
                ]
            },
        )

    chroma_results = []

    for i in range(len(results["documents"][0])):
        metadata = results["metadatas"][0][i]

        chroma_results.append(
            {
                "id": results["ids"][0][i],
                "chunk": results["documents"][0][i],
                "metadata": metadata,
                "distance": results["distances"][0][i],
                "chunk_number": metadata["chunk_number"] + 1,
                "document_id": metadata["document_id"],
            }
        )

    bm25_results = search_bm25(
        query,
        user_id=user_id,
        document_id=document_id,
        n_results=n_results,
    )

    rrf_scores = {}
    combined_results = {}

    for rank, result in enumerate(chroma_results):
        chunk_id = result["id"]

        rrf_scores[chunk_id] = (
            rrf_scores.get(chunk_id, 0)
            + 2 / (60 + rank + 1)
        )

        combined_results[chunk_id] = result

    for rank, result in enumerate(bm25_results):
        chunk_id = (
            f'{result["document_id"]}_'
            f'{result["metadata"]["chunk_number"]}'
        )

        rrf_scores[chunk_id] = (
            rrf_scores.get(chunk_id, 0)
            + 1 / (60 + rank + 1)
        )

        combined_results[chunk_id] = result

    ranked_results = sorted(
        combined_results.items(),
        key=lambda item: rrf_scores[item[0]],
        reverse=True,
    )

    final_results = []

    for chunk_id, result in ranked_results:
        result["rrf_score"] = rrf_scores[chunk_id]
        result["id"] = chunk_id
        final_results.append(result)

    return final_results[:n_results]