from langchain_openai import ChatOpenAI
import os


# Configurar el LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)
