import os
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_ollama import ChatOllama


# def load_llm() -> BaseChatModel:
#     api_key = os.getenv("OPENAI_API_KEY")
#     return init_chat_model("gpt-4o-mini", api_key=api_key)
    # api_key = os.getenv("GOOGLE_API_KEY")
    # return init_chat_model("gemini-2.0-flash-lite", api_key=api_key)

def load_llm() -> BaseChatModel:
    """
    Carrega o modelo Mistral rodando localmente no Ollama.
    Não usa API key.
    """
    return ChatOllama(
        model="mistral",
        base_url="http://localhost:11434",  # padrão do Ollama
        temperature=0.2,
    )