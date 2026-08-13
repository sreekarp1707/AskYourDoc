import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_answer(question, retrieved_chunks):
    context = "\n\n".join(
        chunk["chunk"]
        for chunk in retrieved_chunks
    )

    prompt = f"""
You are an AI assistant for a Retrieval-Augmented Generation (RAG) application.

Answer the user's question ONLY using the information explicitly supported by the context below.

Rules:

- Do NOT use your own knowledge.
- Do NOT make up information.
- Do NOT infer or assume an answer from loosely related information.
- First determine whether the context actually contains enough information to answer the question.
- If the context does not directly support an answer, reply exactly:
  "I couldn't find the answer in the uploaded document(s)."
- If the context supports the answer, answer clearly using only that information.
- Every factual statement in your answer must be supported by the provided context.
- If the question asks "what is", "what are", "define", or asks for the meaning of a concept, the context must contain an explicit definition or direct explanation of that concept.
- Do NOT create a definition by combining related statements.
- If the context only mentions or discusses the concept without defining it, reply exactly:
  "I couldn't find the answer in the uploaded document(s)."

Context:
{context}

Question:
{question}

Answer:
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if (
            not response.text
            or
            not response.text.strip()
        ):
            return "Gemini returned an empty response."

        return response.text.strip()

    except Exception as e:
        print("\n========== GEMINI ERROR ==========")
        print(e)
        print("==================================\n")

        return (
            "Unable to generate an answer at the moment. "
            "Please check your internet connection or try again later."
        )