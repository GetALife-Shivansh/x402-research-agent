import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

FALLBACK_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b"
]

def get_llm(
    model: str = "openai/gpt-oss-120b",
    temperature: float = 0
):
    primary_model = os.environ.get("GROQ_PRIMARY_MODEL", model)
    fallback_models = [m for m in FALLBACK_MODELS if m != primary_model]
    
    primary_llm = ChatGroq(
        model=primary_model,
        temperature=temperature,
        api_key=os.environ["GROQ_API_KEY"]
    )
    
    fallbacks = [
        ChatGroq(
            model=fb,
            temperature=temperature,
            api_key=os.environ["GROQ_API_KEY"]
        )
        for fb in fallback_models
    ]
    
    return primary_llm.with_fallbacks(fallbacks)

def invoke_with_retry(llm_or_runnable, messages):
    return llm_or_runnable.invoke(messages)