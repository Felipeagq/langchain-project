from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from llm import llm

prompt_router = PromptTemplate(
    input_variables=["mensaje"],
    template="""
Eres un recepcionista de un sistema.

Clasifica la intención del usuario en UNA palabra:

- crear → registrar, agregar, guardar clientes
- consultar → listar, ver, buscar clientes

Mensaje: {mensaje}

Responde SOLO con:
crear
consultar
"""
)

router_chain = LLMChain(
    llm=llm,
    prompt=prompt_router
)
