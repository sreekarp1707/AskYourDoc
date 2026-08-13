import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def rewrite_question(question, chat_history):

    history = ""

    for chat in reversed(chat_history):
        history += (
            f"User: {chat['question']}\n"
            f"Assistant: {chat['answer']}\n\n"
        )

    prompt = f"""
You are a query rewriting assistant for a Retrieval-Augmented Generation (RAG) system.

Conversation History:
{history}

Current User Question:
{question}

Instructions:
- If the current question depends on the conversation history, rewrite it into a clear standalone question.
- If the current question is already complete, return it exactly as it is.
- Do not answer the question.
- Return only the final standalone question.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if not response.text or not response.text.strip():
            return question

        return response.text.strip()

    except Exception:
        return question