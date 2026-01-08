from langchain.agents import initialize_agent, AgentType
from tools import consultar_clientes
from llm import llm

agente_consultar = initialize_agent(
    tools=[consultar_clientes],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
