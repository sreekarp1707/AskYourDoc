import os
import pickle

from rank_bm25 import BM25Okapi
from .chunker import chunk_text


BM25_INDEX_PATH = "bm25_index.pkl"


def _load_index():
    if not os.path.exists(BM25_INDEX_PATH):
        return {
            "chunks": [],
            "metadatas": [],
            "bm25": None,
        }

    with open(BM25_INDEX_PATH, "rb") as file:
        return pickle.load(file)


def _save_index(data):
    with open(BM25_INDEX_PATH, "wb") as file:
        pickle.dump(data, file)


def _tokenize(text):
    return text.lower().split()


def add_chunks(chunks, metadatas):
    data = _load_index()

    data["chunks"].extend(chunks)
    data["metadatas"].extend(metadatas)

    tokenized_chunks = [
        _tokenize(chunk)
        for chunk in data["chunks"]
    ]

    data["bm25"] = BM25Okapi(tokenized_chunks)

    _save_index(data)


def search_bm25(
    query,
    user_id,
    document_id=None,
    n_results=3,
):
    data = _load_index()

    if not data["chunks"] or data["bm25"] is None:
        return []

    query_tokens = _tokenize(query)
    scores = data["bm25"].get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )

    results = []

    for index in ranked_indices:
        metadata = data["metadatas"][index]

        if metadata["user_id"] != user_id:
            continue

        if (
            document_id is not None
            and metadata["document_id"] != document_id
        ):
            continue

        results.append(
            {
                "chunk": data["chunks"][index],
                "metadata": metadata,
                "bm25_score": float(scores[index]),
                "chunk_number": metadata["chunk_number"] + 1,
                "document_id": metadata["document_id"],
            }
        )

        if len(results) >= n_results:
            break

    return results

def rebuild_index(documents):
    chunks = []
    metadatas = []

    for document in documents:
        if document.document_file.name.lower().endswith(".pdf"):
            from .file_reader import extract_pdf_pages
            from .chunker import chunk_pdf_pages

            pages = extract_pdf_pages(document.document_file)
            chunk_data = chunk_pdf_pages(pages)

            document_chunks = [
                item["text"]
                for item in chunk_data
            ]

            document_metadatas = [
                {
                    "user_id": document.user_id,
                    "document_id": document.id,
                    "chunk_number": i,
                    "page_number": item["page_number"],
                }
                for i, item in enumerate(chunk_data)
            ]

        else:
            document_chunks = chunk_text(
                document.extracted_text
            )

            document_metadatas = [
                {
                    "user_id": document.user_id,
                    "document_id": document.id,
                    "chunk_number": i,
                }
                for i in range(len(document_chunks))
            ]

        chunks.extend(document_chunks)
        metadatas.extend(document_metadatas)

    data = {
        "chunks": chunks,
        "metadatas": metadatas,
        "bm25": None,
    }

    if chunks:
        tokenized_chunks = [
            _tokenize(chunk)
            for chunk in chunks
        ]

        data["bm25"] = BM25Okapi(tokenized_chunks)

    _save_index(data)

def delete_document_chunks(document_id):
    data = _load_index()

    filtered_chunks = []
    filtered_metadatas = []

    for chunk, metadata in zip(
        data["chunks"],
        data["metadatas"],
    ):
        if metadata["document_id"] != document_id:
            filtered_chunks.append(chunk)
            filtered_metadatas.append(metadata)

    data["chunks"] = filtered_chunks
    data["metadatas"] = filtered_metadatas

    if filtered_chunks:
        tokenized_chunks = [
            _tokenize(chunk)
            for chunk in filtered_chunks
        ]

        data["bm25"] = BM25Okapi(tokenized_chunks)
    else:
        data["bm25"] = None

    _save_index(data)    