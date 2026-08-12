import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type
)
from groq import RateLimitError, APIStatusError, APIConnectionError


load_dotenv()


def get_llm(
    model: str = "openai/gpt-oss-120b",
    temperature: float = 0
):
    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=os.environ["GROQ_API_KEY"]
    )


@retry(
    retry=retry_if_exception_type(
        (RateLimitError, APIStatusError, APIConnectionError)
    ),
    wait=wait_exponential(
        multiplier=3,
        min=5,
        max=60
    ),
    stop=stop_after_attempt(6),
)
def invoke_with_retry(llm, messages):
    return llm.invoke(messages)
