def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def chunk_pdf_pages(pages, chunk_size=500, overlap=50):
    chunks = []

    for page in pages:
        words = page["text"].split()
        start = 0
        page_chunk_number = 0

        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])

            chunks.append(
                {
                    "text": chunk,
                    "page_number": page["page_number"],
                    "page_chunk_number": page_chunk_number,
                }
            )

            page_chunk_number += 1
            start += chunk_size - overlap

    return chunks