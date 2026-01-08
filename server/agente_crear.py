from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from tools import crear_cliente
from llm import llm


def crear_agente_con_memoria(memory: ConversationBufferMemory = None):
    """
    Crea el agente de creación de clientes con memoria opcional.
    Si no se pasa memoria, funciona sin historial.

    Args:
        memory: ConversationBufferMemory opcional con historial de la sesión

    Returns:
        Agente de LangChain configurado para crear clientes
    """
    agent_kwargs = {
        "prefix": """
Eres un agente que SOLO crea clientes.

IMPORTANTE: Antes de preguntar información, REVISA EL HISTORIAL DE LA CONVERSACIÓN.
El usuario puede haber proporcionado el nombre o email en mensajes anteriores.

Proceso:
1. Revisa el historial completo de la conversación
2. Extrae el nombre si ya fue mencionado
3. Extrae el email si ya fue mencionado
4. Si tienes AMBOS (nombre Y email), ejecuta la herramienta crear_cliente
5. Si falta alguno, pregunta SOLO por lo que falta

Ejemplos:
- Si el usuario dijo "Mi nombre es Juan" antes, NO vuelvas a preguntar el nombre
- Si el usuario dijo "Mi correo es juan@email.com" antes, NO vuelvas a preguntar el email
- Si ya tienes ambos datos, procede a crear el cliente inmediatamente

NO repitas preguntas que ya fueron respondidas en el historial.
"""
    }

    if memory:
        return initialize_agent(
            tools=[crear_cliente],
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            agent_kwargs=agent_kwargs
        )
    else:
        return initialize_agent(
            tools=[crear_cliente],
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            agent_kwargs=agent_kwargs
        )
