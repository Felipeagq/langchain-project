from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar el LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)
