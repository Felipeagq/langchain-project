# Implementación de Persistencia de Memoria por Sesiones con FastAPI

## Arquitectura General

Este documento explica cómo implementar un sistema de memoria persistente que permita múltiples sesiones simultáneas de conversación usando FastAPI y SQLAlchemy.

## Componentes del Sistema

### 1. Modelo de Datos (models.py)

Agregar una nueva tabla para almacenar mensajes:

```python
class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)  # Identificador único de sesión
    role = Column(String, nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)  # Contenido del mensaje
    timestamp = Column(DateTime, default=datetime.utcnow)  # Fecha/hora
```

**¿Por qué esta estructura?**
- `session_id`: Permite diferenciar conversaciones de diferentes usuarios/sesiones
- `role`: Distingue entre mensajes del usuario y respuestas del asistente
- `timestamp`: Mantiene el orden cronológico de los mensajes
- Index en `session_id`: Optimiza las consultas de historial

### 2. Gestor de Memoria Persistente (memory_manager.py)

Crear un nuevo archivo que maneje la persistencia:

```python
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from database import SessionLocal
from models import Mensaje
from typing import List

class PersistentMemoryManager:
    """
    Gestiona la memoria de conversaciones con persistencia en base de datos.
    """

    @staticmethod
    def save_message(session_id: str, role: str, content: str):
        """
        Guarda un mensaje en la base de datos.

        Args:
            session_id: Identificador único de la sesión
            role: "user" o "assistant"
            content: Contenido del mensaje
        """
        db = SessionLocal()
        try:
            mensaje = Mensaje(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(mensaje)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_history(session_id: str) -> List[Mensaje]:
        """
        Recupera el historial de mensajes de una sesión.

        Returns:
            Lista de mensajes ordenados por timestamp
        """
        db = SessionLocal()
        try:
            return db.query(Mensaje)\
                .filter(Mensaje.session_id == session_id)\
                .order_by(Mensaje.timestamp)\
                .all()
        finally:
            db.close()

    @staticmethod
    def load_memory_for_agent(session_id: str) -> ConversationBufferMemory:
        """
        Carga el historial desde BD y lo convierte en memoria de LangChain.

        Returns:
            ConversationBufferMemory con historial cargado
        """
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Cargar mensajes históricos
        mensajes = PersistentMemoryManager.get_history(session_id)

        # Convertir a formato LangChain
        for msg in mensajes:
            if msg.role == "user":
                memory.chat_memory.add_user_message(msg.content)
            elif msg.role == "assistant":
                memory.chat_memory.add_ai_message(msg.content)

        return memory

    @staticmethod
    def clear_session(session_id: str):
        """
        Elimina todos los mensajes de una sesión.
        """
        db = SessionLocal()
        try:
            db.query(Mensaje)\
                .filter(Mensaje.session_id == session_id)\
                .delete()
            db.commit()
        finally:
            db.close()
```

### 3. API con FastAPI (api.py)

Crear un nuevo archivo para la API REST:

```python
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from database import engine, Base
from agente_crear import agente_crear
from agente_consultar import agente_consultar
from agente_recepcionista import router_chain
from memory_manager import PersistentMemoryManager

# Inicializar FastAPI
app = FastAPI(title="Sistema Multi-Agente con Memoria Persistente")

# Crear tablas
Base.metadata.create_all(bind=engine)

# Modelos Pydantic para request/response
class ChatRequest(BaseModel):
    mensaje: str

class ChatResponse(BaseModel):
    respuesta: str
    session_id: str
    decision: str  # "crear" o "consultar"

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_id: Optional[str] = Header(None)
):
    """
    Endpoint principal de chat con memoria persistente.

    Headers:
        session-id: ID de sesión (opcional, se genera si no existe)

    Body:
        mensaje: El mensaje del usuario

    Returns:
        Respuesta del sistema + session_id para siguientes peticiones
    """
    # 1. Generar session_id si no existe
    if not session_id:
        session_id = str(uuid.uuid4())

    # 2. Guardar mensaje del usuario en BD
    PersistentMemoryManager.save_message(
        session_id=session_id,
        role="user",
        content=request.mensaje
    )

    # 3. Cargar memoria desde BD
    memory = PersistentMemoryManager.load_memory_for_agent(session_id)

    # 4. Decidir qué agente usar (recepcionista)
    decision = router_chain.invoke(
        {"mensaje": request.mensaje}
    )["text"].strip().lower()

    # 5. Procesar con el agente correspondiente
    if decision == "crear":
        resultado = agente_crear.invoke(
            {"input": request.mensaje},
            config={"configurable": {"memory": memory}}
        )
        respuesta = resultado.get("output", str(resultado))

    elif decision == "consultar":
        resultado = agente_consultar.invoke(
            {"input": request.mensaje},
            config={"configurable": {"memory": memory}}
        )
        respuesta = resultado.get("output", str(resultado))

    else:
        respuesta = "❓ No entendí la solicitud"

    # 6. Guardar respuesta del asistente en BD
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

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Obtiene el historial completo de una sesión.
    """
    mensajes = PersistentMemoryManager.get_history(session_id)

    return {
        "session_id": session_id,
        "total_mensajes": len(mensajes),
        "historial": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in mensajes
        ]
    }

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Elimina el historial de una sesión.
    """
    PersistentMemoryManager.clear_session(session_id)
    return {"message": f"Historial de sesión {session_id} eliminado"}

@app.get("/")
async def root():
    return {
        "message": "API Multi-Agente con Memoria Persistente",
        "endpoints": {
            "POST /chat": "Enviar mensaje",
            "GET /history/{session_id}": "Ver historial",
            "DELETE /history/{session_id}": "Borrar historial"
        }
    }
```

### 4. Actualizar agentes para soportar memoria

Modificar `agente_crear.py` y `agente_consultar.py`:

```python
from langchain.agents import initialize_agent, AgentType
from tools import crear_cliente
from llm import llm

def crear_agente_con_memoria(memory=None):
    """
    Crea el agente con memoria opcional.
    Si no se pasa memoria, funciona sin historial.
    """
    agent_kwargs = {
        "prefix": """
Eres un agente que SOLO crea clientes.
Antes de ejecutar la herramienta debes asegurarte
de tener nombre y email.
Si falta información, pregúntala.
"""
    }

    if memory:
        agent_kwargs["memory"] = memory

    return initialize_agent(
        tools=[crear_cliente],
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_kwargs=agent_kwargs
    )

# Exportar función en lugar de instancia
agente_crear = crear_agente_con_memoria
```

### 5. Dependencias necesarias (requirements.txt)

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
langchain==0.1.0
langchain-openai==0.0.5
sqlalchemy==2.0.25
python-dotenv==1.0.0
pydantic==2.5.0
```

## Flujo de Datos Completo

```
┌─────────────┐
│   Cliente   │
│ (Browser/   │
│  App móvil) │
└──────┬──────┘
       │
       │ POST /chat
       │ Headers: session-id: "abc123"
       │ Body: {mensaje: "Crea cliente Juan"}
       │
       ▼
┌─────────────────────────────────────────┐
│            FastAPI Server               │
│                                         │
│  1. Recibe request                      │
│  2. Si no hay session_id → genera UUID  │
│  3. Guarda mensaje user en BD           │
│     └─► Tabla: mensajes                 │
│                                         │
│  4. Carga historial desde BD            │
│     SELECT * FROM mensajes              │
│     WHERE session_id = 'abc123'         │
│                                         │
│  5. Convierte a ConversationMemory      │
│     ├─► HumanMessage("Hola")            │
│     └─► AIMessage("Hola, ¿cómo...")     │
│                                         │
│  6. Router decide agente                │
│     └─► "crear" o "consultar"           │
│                                         │
│  7. Ejecuta agente con memoria          │
│     agente_crear.invoke(               │
│       input=mensaje,                    │
│       memory=historial_cargado          │
│     )                                   │
│                                         │
│  8. Guarda respuesta en BD              │
│     INSERT INTO mensajes                │
│                                         │
│  9. Retorna respuesta + session_id      │
└─────────────┬───────────────────────────┘
              │
              │ Response:
              │ {
              │   respuesta: "✅ Cliente creado",
              │   session_id: "abc123",
              │   decision: "crear"
              │ }
              │
              ▼
       ┌──────────────┐
       │   Cliente    │
       │ Guarda       │
       │ session_id   │
       │ para próxima │
       │ petición     │
       └──────────────┘
```

## Cómo diferenciar sesiones

### Opción 1: Por usuario autenticado
```javascript
// Frontend guarda session_id por usuario
const sessionId = `user_${userId}`;  // "user_123"

fetch('/chat', {
    headers: {'session-id': sessionId}
})
```

### Opción 2: Por conversación
```javascript
// Cada chat tiene su propia sesión
const sessionId = `chat_${chatId}`;  // "chat_abc123"
```

### Opción 3: Generación automática
```javascript
// Primera petición sin session-id
let sessionId = null;

const response = await fetch('/chat', {
    headers: sessionId ? {'session-id': sessionId} : {}
});

// Servidor retorna session_id generado
sessionId = response.session_id;
localStorage.setItem('session_id', sessionId);
```

## Ejemplo de uso

### Iniciar el servidor

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn api:app --reload --port 8000
```

### Cliente 1 - Primera conversación

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "Crea un cliente llamado Juan con email juan@example.com"}'

# Respuesta:
{
  "respuesta": "✅ Cliente creado: Juan (juan@example.com)",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "crear"
}
```

### Cliente 1 - Siguiente mensaje (con memoria)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "session-id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"mensaje": "Ahora crea otro con nombre María"}'

# El agente recordará que ya creó a Juan y continuará la conversación
```

### Cliente 2 - Conversación independiente

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "Lista todos los clientes"}'

# Nueva sesión, no tiene acceso al historial del Cliente 1
{
  "respuesta": "- Juan | juan@example.com\n- María | ...",
  "session_id": "661f9511-f3a-52e5-b827-557766551111",
  "decision": "consultar"
}
```

### Ver historial de una sesión

```bash
curl http://localhost:8000/history/550e8400-e29b-41d4-a716-446655440000

# Respuesta:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_mensajes": 4,
  "historial": [
    {
      "role": "user",
      "content": "Crea un cliente llamado Juan...",
      "timestamp": "2026-01-08T10:30:00"
    },
    {
      "role": "assistant",
      "content": "✅ Cliente creado: Juan...",
      "timestamp": "2026-01-08T10:30:02"
    },
    ...
  ]
}
```

## Ventajas de esta implementación

✅ **Múltiples sesiones simultáneas**: Cada usuario/conversación es independiente
✅ **Persistencia**: El historial sobrevive a reinicios del servidor
✅ **Escalable**: Múltiples instancias de FastAPI pueden compartir la misma BD
✅ **Auditoría**: Registro completo de todas las interacciones
✅ **Análisis**: Puedes consultar conversaciones antiguas para mejorar el sistema
✅ **Contexto**: Los agentes recuerdan conversaciones anteriores

## Consideraciones de seguridad

- **No exponer session_id en URLs**: Usar headers en su lugar
- **Validar session_id**: Verificar que pertenece al usuario autenticado
- **Limpieza periódica**: Eliminar sesiones antiguas para no saturar la BD
- **Rate limiting**: Prevenir abuso de la API
- **Encriptación**: Considerar encriptar contenido sensible en BD

## Próximos pasos

1. Implementar autenticación de usuarios
2. Agregar límite de mensajes por sesión
3. Implementar resumen automático de conversaciones largas
4. Agregar métricas y monitoreo
5. Implementar caché para sesiones activas
