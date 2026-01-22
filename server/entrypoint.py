from fastapi import FastAPI, Header, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from twilio.rest import Client
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

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

# Configuración de Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+12697484776")
twilio_client = Client(account_sid, auth_token)


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


@app.post("/whatsapp")
async def recibir_mensaje_whatsapp(From: str = Form(...), Body: str = Form(...)):
    """
    Endpoint para recibir mensajes de WhatsApp via Twilio.
    Usa el sistema multi-agente para generar respuestas inteligentes.
    """
    mensaje = Body.strip()
    # Usar el número de teléfono como session_id para mantener contexto por usuario
    session_id = From.replace("whatsapp:", "").replace("+", "")

    print(f"[WhatsApp] {From}: {mensaje}")
    print(f"[DEBUG] session_id generado: {session_id}")

    # 1. Cargar memoria del usuario
    print(f"[DEBUG] Cargando memoria para session_id: {session_id}")
    memory = PersistentMemoryManager.load_memory_for_agent(session_id)
    print(f"[DEBUG] Memoria cargada - mensajes en historial: {len(memory.chat_memory.messages)}")

    # 2. Guardar mensaje del usuario
    print(f"[DEBUG] Guardando mensaje del usuario en BD...")
    PersistentMemoryManager.save_message(
        session_id=session_id,
        role="user",
        content=mensaje
    )
    print(f"[DEBUG] Mensaje guardado en BD")

    # 3. Decidir qué agente usar
    print(f"[DEBUG] Llamando a router_con_memoria con mensaje: '{mensaje}'")
    try:
        decision = router_con_memoria(mensaje, memory)
        print(f"[DEBUG] router_con_memoria retornó decisión: '{decision}'")
    except Exception as e:
        print(f"[DEBUG] ERROR en router_con_memoria: {str(e)}")
        decision = "error"
        respuesta = f"Error al procesar: {str(e)}"

    # 4. Agregar mensaje a memoria
    print(f"[DEBUG] Agregando mensaje a memoria del agente")
    memory.chat_memory.add_user_message(mensaje)

    # 5. Procesar con el agente correspondiente
    print(f"[DEBUG] Entrando a procesar con decisión: '{decision}'")
    if decision == "crear":
        print(f"[DEBUG] >>> ENTRANDO A RAMA 'crear'")
        contexto_resumido = []
        for msg in memory.chat_memory.messages[:-1]:
            if msg.type == "human":
                contexto_resumido.append(f"Usuario dijo: {msg.content}")
            else:
                contexto_resumido.append(f"Asistente respondió: {msg.content}")

        if contexto_resumido:
            mensaje_con_contexto = f"""Contexto de la conversación anterior:
{chr(10).join(contexto_resumido)}
Mensaje actual del usuario: {mensaje}
IMPORTANTE: Revisa el contexto anterior para extraer nombre y email si ya fueron mencionados."""
        else:
            mensaje_con_contexto = mensaje

        try:
            agente = crear_agente_crear(memory)
            resultado = agente.invoke({"input": mensaje_con_contexto})
            respuesta = resultado.get("output", str(resultado))
        except Exception as e:
            respuesta = f"Error en agente crear: {str(e)}"

    elif decision == "consultar":
        print(f"[DEBUG] >>> ENTRANDO A RAMA 'consultar'")
        contexto_resumido = []
        for msg in memory.chat_memory.messages[:-1]:
            if msg.type == "human":
                contexto_resumido.append(f"Usuario dijo: {msg.content}")
            else:
                contexto_resumido.append(f"Asistente respondió: {msg.content}")

        if contexto_resumido:
            mensaje_con_contexto = f"""Contexto de la conversación anterior:
{chr(10).join(contexto_resumido)}
Mensaje actual del usuario: {mensaje}
IMPORTANTE: Revisa el contexto anterior para entender qué información busca el usuario."""
        else:
            mensaje_con_contexto = mensaje

        try:
            agente = crear_agente_consultar(memory)
            resultado = agente.invoke({"input": mensaje_con_contexto})
            respuesta = resultado.get("output", str(resultado))
        except Exception as e:
            respuesta = f"Error en agente consultar: {str(e)}"

    else:
        print(f"[DEBUG] >>> ENTRANDO A RAMA 'else' - decisión no reconocida: '{decision}'")
        respuesta = "No entendí la solicitud. Por favor, reformula tu mensaje."

    # 6. Guardar respuesta en BD
    print(f"[DEBUG] Respuesta generada: {respuesta[:100]}...")
    print(f"[DEBUG] Guardando respuesta en BD...")
    PersistentMemoryManager.save_message(
        session_id=session_id,
        role="assistant",
        content=respuesta
    )

    # 7. Enviar respuesta via Twilio
    try:
        twilio_client.messages.create(
            from_=twilio_number,
            to=From,
            body=respuesta
        )
    except Exception as e:
        print(f"[WhatsApp] Error enviando mensaje: {e}")

    return JSONResponse(content={"status": "enviado", "session_id": session_id})


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
        host="0.0.0.0",
        port=8004,
        reload=True,
    )
