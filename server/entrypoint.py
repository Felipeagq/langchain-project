from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from database import engine, Base
from agente_crear import crear_agente_con_memoria as crear_agente_crear
from agente_consultar import crear_agente_con_memoria as crear_agente_consultar
from agente_recepcionista import router_chain, router_con_memoria
from memory_manager import PersistentMemoryManager

# Inicializar FastAPI
app = FastAPI(
    title="Sistema Multi-Agente con Memoria Persistente",
    description="API REST para gestión de clientes con agentes conversacionales y memoria por sesiones",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)


# Modelos Pydantic para request/response
class ChatRequest(BaseModel):
    mensaje: str

class ChatResponse(BaseModel):
    respuesta: str
    session_id: str
    decision: str  # "crear" o "consultar"

class HistoryResponse(BaseModel):
    session_id: str
    total_mensajes: int
    historial: list


@app.get("/")
async def root():
    """
    Endpoint raíz con información de la API
    """
    return {
        "message": "API Multi-Agente con Memoria Persistente",
        "version": "1.0.0",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_id: Optional[str] = Header(None, alias="session-id")
):
    """
    Endpoint principal de chat con memoria persistente.

    **Headers:**
    - session-id: ID de sesión (opcional, se genera automáticamente si no existe)

    **Body:**
    - mensaje: El mensaje del usuario

    **Returns:**
    - Respuesta del sistema + session_id para siguientes peticiones
    """
    # 1. Generar session_id si no existe
    if not session_id:
        session_id = str(uuid.uuid4())

    # 2. Cargar memoria ANTES de guardar el mensaje actual
    memory = PersistentMemoryManager.load_memory_for_agent(session_id)

    # 3. Guardar mensaje del usuario DESPUÉS de cargar historial
    PersistentMemoryManager.save_message(
        session_id=session_id,
        role="user",
        content=request.mensaje
    )

    # 4. Decidir qué agente usar (recepcionista CON contexto)
    try:
        # Usar el router que considera el historial
        decision = router_con_memoria(request.mensaje, memory)
    except Exception as e:
        decision = "error"
        respuesta = f"❌ Error al procesar la solicitud: {str(e)}"

    # 5. Agregar el mensaje actual a la memoria para que el agente lo vea
    memory.chat_memory.add_user_message(request.mensaje)

    # 6. Procesar con el agente correspondiente
    if decision == "crear":
        # Crear un resumen del contexto para el agente
        contexto_resumido = []
        for msg in memory.chat_memory.messages[:-1]:  # Excluir el último (mensaje actual)
            if msg.type == "human":
                contexto_resumido.append(f"Usuario dijo: {msg.content}")
            else:
                contexto_resumido.append(f"Asistente respondió: {msg.content}")

        # Construir mensaje enriquecido con contexto
        if contexto_resumido:
            mensaje_con_contexto = f"""Contexto de la conversación anterior:
                                {chr(10).join(contexto_resumido)}
                                Mensaje actual del usuario: {request.mensaje}
                                IMPORTANTE: Revisa el contexto anterior para extraer nombre y email si ya fueron mencionados."""
        else:
            mensaje_con_contexto = request.mensaje

        try:
            agente = crear_agente_crear(memory)
            resultado = agente.invoke(
                {"input": mensaje_con_contexto}
            )
            respuesta = resultado.get("output", str(resultado))
        except Exception as e:
            respuesta = f"❌ Error en agente crear: {str(e)}"

    elif decision == "consultar":
        # Crear un resumen del contexto para el agente
        contexto_resumido = []
        for msg in memory.chat_memory.messages[:-1]:  # Excluir el último (mensaje actual)
            if msg.type == "human":
                contexto_resumido.append(f"Usuario dijo: {msg.content}")
            else:
                contexto_resumido.append(f"Asistente respondió: {msg.content}")

        # Construir mensaje enriquecido con contexto
        if contexto_resumido:
            mensaje_con_contexto = f"""Contexto de la conversación anterior:
                                    {chr(10).join(contexto_resumido)}
                                    Mensaje actual del usuario: {request.mensaje}
                                    IMPORTANTE: Revisa el contexto anterior para entender qué información busca el usuario."""
        else:
            mensaje_con_contexto = request.mensaje

        try:
            agente = crear_agente_consultar(memory)
            resultado = agente.invoke(
                {"input": mensaje_con_contexto}
            )
            respuesta = resultado.get("output", str(resultado))
        except Exception as e:
            respuesta = f"❌ Error en agente consultar: {str(e)}"

    else:
        respuesta = "❓ No entendí la solicitud. Por favor, reformula tu mensaje."

    # 7. Guardar respuesta del asistente en BD
    PersistentMemoryManager.save_message(
        session_id=session_id,
        role="assistant",
        content=respuesta
    )

    return ChatResponse(
        respuesta=respuesta,
        session_id=session_id,
        decision=decision
    )


@app.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """
    Obtiene el historial completo de una sesión.

    **Path Parameters:**
    - session_id: ID de la sesión a consultar

    **Returns:**
    - Historial completo de mensajes de la sesión
    """
    mensajes = PersistentMemoryManager.get_history(session_id)

    return HistoryResponse(
        session_id=session_id,
        total_mensajes=len(mensajes),
        historial=[
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in mensajes
        ]
    )


@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Elimina el historial de una sesión.

    **Path Parameters:**
    - session_id: ID de la sesión a eliminar

    **Returns:**
    - Mensaje de confirmación
    """
    PersistentMemoryManager.clear_session(session_id)
    return {
        "message": f"Historial de sesión {session_id} eliminado correctamente",
        "session_id": session_id
    }


@app.get("/health")
async def health_check():
    """
    Endpoint de verificación de estado del servidor
    """
    return {
        "status": "ok",
        "service": "Sistema Multi-Agente",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(
        "entrypoint:app",
        host="localhost",
        port=5050,
        reload=True,
    )
