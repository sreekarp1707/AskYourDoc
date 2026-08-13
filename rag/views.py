import hashlib

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import DocumentUploadForm
from .models import Document
from .utils.chunker import chunk_pdf_pages, chunk_text
from .utils.embeddings import generate_embeddings
from .utils.file_reader import extract_pdf_pages, extract_text
from .utils.gemini_helper import generate_answer
from .utils.query_rewriter import rewrite_question
from .utils.retriever import retrieve_chunks
from .utils.bm25 import add_chunks, delete_document_chunks as delete_bm25_chunks
from .utils.chroma_db import (
    store_embeddings,
    delete_document_chunks as delete_chroma_chunks,
)


@login_required
def dashboard(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user

            extracted_text = extract_text(document.document_file)

            if not extracted_text.strip():
                form.add_error(
                    "document_file",
                    "The uploaded document contains no readable text."
                )
            else:
                document_hash = hashlib.sha256(
                    extracted_text.encode("utf-8")
                ).hexdigest()

                if Document.objects.filter(
                    user=request.user,
                    document_hash=document_hash,
                ).exists():
                    form.add_error(
                        "document_file",
                        "This document has already been uploaded."
                    )
                else:
                    document.extracted_text = extracted_text
                    document.document_hash = document_hash
                    document.save()

                    if document.document_file.name.lower().endswith(".pdf"):
                        pages = extract_pdf_pages(
                            document.document_file
                        )

                        chunk_data = chunk_pdf_pages(pages)

                        chunks = [
                            item["text"]
                            for item in chunk_data
                        ]

                        page_numbers = [
                            item["page_number"]
                            for item in chunk_data
                        ]
                    else:
                        chunks = chunk_text(extracted_text)
                        page_numbers = [None] * len(chunks)

                    embeddings = generate_embeddings(chunks)

                    ids = [
                        f"{document.id}_{i}"
                        for i in range(len(chunks))
                    ]

                    metadatas = []

                    for i in range(len(chunks)):
                        metadata = {
                            "user_id": document.user.id,
                            "document_id": document.id,
                            "chunk_number": i,
                        }

                        if page_numbers[i] is not None:
                            metadata["page_number"] = page_numbers[i]

                        metadatas.append(metadata)

                    store_embeddings(
                        ids,
                        chunks,
                        embeddings,
                        metadatas,
                    )

                    add_chunks(
                        chunks,
                        metadatas,
                    )

                    return redirect("dashboard")
    else:
        form = DocumentUploadForm()

    documents = Document.objects.filter(user=request.user)

    context = {
        "form": form,
        "documents": documents,
    }

    return render(
        request,
        "rag/dashboard.html",
        context,
    )


@login_required
def chat_view(request):
    documents = Document.objects.filter(user=request.user)

    if request.GET.get("new") == "1":
        request.session["chat_history"] = []
        request.session["chat_started"] = False
        request.session["selected_document"] = "all"
        request.session.modified = True
        return redirect("chat")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "start_chat":
            request.session["selected_document"] = request.POST.get(
                "document",
                "all",
            )
            request.session["chat_history"] = []
            request.session["chat_started"] = True
            request.session.modified = True
            return redirect("chat")

        if action == "ask":
            question = request.POST.get("question", "").strip()

            if not question:
                return JsonResponse(
                    {"error": "Question cannot be empty."},
                    status=400,
                )

            previous_chat = request.session.get(
                "chat_history",
                [],
            )
            selected_document = request.session.get(
                "selected_document",
                "all",
            )

            standalone_question = rewrite_question(
                question,
                previous_chat[-3:],
            )

            results = (
                retrieve_chunks(
                    standalone_question,
                    user_id=request.user.id,
                    document_id=int(selected_document),
                )
                if selected_document != "all"
                else retrieve_chunks(
                    standalone_question,
                    user_id=request.user.id,
                )
            )

            answer = generate_answer(
                standalone_question,
                results,
            )

            sources = [
                {
                    "document_name": Document.objects.get(
                        id=result["document_id"]
                    ).document_file.name.split("/")[-1],
                    "chunk_number": result["chunk_number"],
                    "page_number": result["metadata"].get(
                        "page_number"
                    ),
                }
                for result in results
            ]

            previous_chat.append(
                {
                    "question": question,
                    "answer": answer,
                    "sources": sources,
                }
            )

            request.session["chat_history"] = previous_chat
            request.session.modified = True

            return JsonResponse(
                {
                    "question": question,
                    "answer": answer,
                    "sources": sources,
                }
            )

    return render(
        request,
        "rag/chat.html",
        {
            "documents": documents,
            "chat_started": request.session.get(
                "chat_started",
                False,
            ),
            "selected_document": request.session.get(
                "selected_document",
                "all",
            ),
            "chat_messages": request.session.get(
                "chat_history",
                [],
            ),
        },
    )

@login_required
def delete_document(request, document_id):
    if request.method == "POST":
        document = Document.objects.get(
            id=document_id,
            user=request.user,
        )

        delete_chroma_chunks(document.id)
        delete_bm25_chunks(document.id)

        document.delete()

        return redirect("dashboard")

    return redirect("dashboard")