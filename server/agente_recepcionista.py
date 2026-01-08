from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, create_openai_functions_agent
from llm import llm


# Plantilla de prompt para el router/recepcionista CON historial
prompt_router_con_historial = ChatPromptTemplate.from_messages([
    ("system", """Eres un recepcionista de un sistema de gestión de clientes.

Clasifica la intención del usuario en UNA palabra basándote en el contexto de la conversación:

- crear → registrar, agregar, guardar, añadir clientes
- consultar → listar, ver, buscar, mostrar clientes

IMPORTANTE: Considera el historial de la conversación. Si el usuario está proporcionando información adicional sobre una solicitud anterior, mantén la misma intención.

Ejemplos:
- Usuario: "Crea un cliente" → crear
- Usuario: "Su nombre es Juan" (continuando) → crear
- Usuario: "Lista los clientes" → consultar
- Usuario: "Muéstrame los que tienen gmail" (continuando) → consultar

Responde SOLO con una de estas palabras (sin puntuación ni espacios adicionales):
crear
consultar"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{mensaje}")
])


# Plantilla de prompt para el router/recepcionista SIN historial (fallback)
prompt_router = PromptTemplate(
    input_variables=["mensaje"],
    template="""
Eres un recepcionista de un sistema de gestión de clientes.

Clasifica la intención del usuario en UNA palabra:

- crear → registrar, agregar, guardar, añadir clientes
- consultar → listar, ver, buscar, mostrar clientes

Mensaje: {mensaje}

Responde SOLO con una de estas palabras (sin puntuación ni espacios adicionales):
crear
consultar
"""
)

# Cadena del router (sin historial - para compatibilidad)
router_chain = LLMChain(
    llm=llm,
    prompt=prompt_router
)


def router_con_memoria(mensaje: str, memory):
    """
    Router que considera el historial de la conversación.

    Args:
        mensaje: Mensaje actual del usuario
        memory: Objeto ConversationBufferMemory con el historial

    Returns:
        str: "crear" o "consultar"
    """
    try:
        # Obtener el historial de mensajes
        chat_history = memory.chat_memory.messages

        # Invocar el LLM con el prompt que incluye historial
        response = llm.invoke(
            prompt_router_con_historial.format_messages(
                chat_history=chat_history,
                mensaje=mensaje
            )
        )

        # Extraer la decisión
        decision = response.content.strip().lower()
        return decision
    except Exception as e:
        # Fallback al router sin memoria
        return router_chain.invoke({"mensaje": mensaje})["text"].strip().lower()
