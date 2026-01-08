from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from tools import consultar_clientes
from llm import llm


def crear_agente_con_memoria(memory: ConversationBufferMemory = None):
    """
    Crea el agente de consulta de clientes con memoria opcional.
    Si no se pasa memoria, funciona sin historial.

    Args:
        memory: ConversationBufferMemory opcional con historial de la sesión

    Returns:
        Agente de LangChain configurado para consultar clientes
    """
    agent_kwargs = {
        "prefix": """
Eres un agente que SOLO consulta información de clientes.

IMPORTANTE: Revisa el historial de la conversación para entender el contexto completo.
El usuario puede estar refinando o filtrando una consulta anterior.

Proceso:
1. Revisa el historial para entender qué información busca el usuario
2. Utiliza la herramienta consultar_clientes para obtener la lista
3. Si el usuario pidió un filtro específico (por ejemplo, "solo los que tienen gmail"),
   aplica ese filtro a los resultados
4. Presenta la información de forma clara y organizada

Considera el contexto de mensajes anteriores para dar respuestas más precisas.
"""
    }

    if memory:
        return initialize_agent(
            tools=[consultar_clientes],
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            agent_kwargs=agent_kwargs
        )
    else:
        return initialize_agent(
            tools=[consultar_clientes],
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            agent_kwargs=agent_kwargs
        )
