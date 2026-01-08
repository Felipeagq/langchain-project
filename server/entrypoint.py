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

    class Config:
        json_schema_extra = {
            "example": {
                "mensaje": "Crea un cliente llamado Juan con email juan@example.com"
            }
        }


class ChatResponse(BaseModel):
    respuesta: str
    session_id: str
    decision: str  # "crear" o "consultar"

    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": "✅ Cliente creado: Juan (juan@example.com)",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "decision": "crear"
            }
        }


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
        "endpoints": {
            "POST /chat": "Enviar mensaje (Header: session-id opcional)",
            "GET /history/{session_id}": "Ver historial de una sesión",
            "DELETE /history/{session_id}": "Borrar historial de una sesión"
        },
        "documentation": "/docs"
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
        print(f"\n🆕 Nueva sesión creada: {session_id}")
    else:
        print(f"\n🔄 Sesión existente: {session_id}")

    print(f"📥 Mensaje del usuario: {request.mensaje}")

    # 2. Cargar memoria ANTES de guardar el mensaje actual
    memory = PersistentMemoryManager.load_memory_for_agent(session_id)

    # Mostrar historial cargado para debug
    historial_previo = memory.chat_memory.messages
    if historial_previo:
        print(f"📚 Historial previo cargado: {len(historial_previo)} mensajes")
        # Mostrar últimos 2 mensajes para debug
        for i, msg in enumerate(historial_previo[-2:], 1):
            role_emoji = "👤" if msg.type == "human" else "🤖"
            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"  {role_emoji} Mensaje {len(historial_previo)-2+i}: {content_preview}")
    else:
        print(f"📭 No hay historial previo (primera interacción)")

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
        print(f"🤖 Decisión del router (con contexto): {decision}")
    except Exception as e:
        decision = "error"
        respuesta = f"❌ Error al procesar la solicitud: {str(e)}"
        print(f"❌ Error en router: {str(e)}")

    # 5. Agregar el mensaje actual a la memoria para que el agente lo vea
    memory.chat_memory.add_user_message(request.mensaje)

    # 6. Procesar con el agente correspondiente
    if decision == "crear":
        print(f"➕ Procesando con agente CREAR...")
        print(f"   📝 Contexto disponible para el agente: {len(memory.chat_memory.messages)} mensajes totales")

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
            print(f"   📋 Enviando contexto enriquecido al agente")
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
            print(f"❌ Error: {str(e)}")

    elif decision == "consultar":
        print(f"🔍 Procesando con agente CONSULTAR...")
        print(f"   📝 Contexto disponible para el agente: {len(memory.chat_memory.messages)} mensajes totales")

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
            print(f"   📋 Enviando contexto enriquecido al agente")
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
            print(f"❌ Error: {str(e)}")

    else:
        respuesta = "❓ No entendí la solicitud. Por favor, reformula tu mensaje."
        print(f"❓ No se pudo determinar la acción")

    # 7. Guardar respuesta del asistente en BD
    PersistentMemoryManager.save_message(
        session_id=session_id,
        role="assistant",
        content=respuesta
    )

    print(f"📤 Respuesta generada: {respuesta[:100]}{'...' if len(respuesta) > 100 else ''}")
    print(f"✅ Proceso completado\n")

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
    print(f"\n📜 Consultando historial para sesión: {session_id}")
    mensajes = PersistentMemoryManager.get_history(session_id)
    print(f"📊 Total de mensajes encontrados: {len(mensajes)}")

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
    print(f"\n🗑️ Eliminando historial de sesión: {session_id}")
    PersistentMemoryManager.clear_session(session_id)
    print(f"✅ Historial eliminado correctamente")
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
        log_level="info",
        use_colors=True
    )
