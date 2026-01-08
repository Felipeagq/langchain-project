from langchain.agents import initialize_agent, AgentType
from tools import crear_cliente
from llm import llm

agente_crear = initialize_agent(
    tools=[crear_cliente],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={
        "prefix": """
Eres un agente que SOLO crea clientes.
Antes de ejecutar la herramienta debes asegurarte
de tener nombre y email.
Si falta información, pregúntala.
"""
    }
)
