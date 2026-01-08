# Sistema Multi-Agente con Memoria Persistente

API REST desarrollada con FastAPI que implementa un sistema multi-agente conversacional con persistencia de memoria por sesiones usando LangChain y SQLAlchemy.

## Características

- **Múltiples sesiones simultáneas**: Cada usuario/conversación es independiente
- **Persistencia de memoria**: El historial sobrevive a reinicios del servidor
- **Sistema multi-agente**: Router inteligente que delega a agentes especializados
- **Gestión de clientes**: Crear y consultar clientes mediante lenguaje natural
- **API REST completa**: Endpoints para chat, historial y gestión de sesiones

## Arquitectura

```
server/
├── api.py                    # Servidor FastAPI con endpoints REST
├── database.py               # Configuración de SQLAlchemy
├── models.py                 # Modelos de base de datos (Cliente, Mensaje)
├── llm.py                    # Configuración del modelo de lenguaje
├── tools.py                  # Herramientas de LangChain
├── memory_manager.py         # Gestor de memoria persistente
├── agente_crear.py          # Agente para crear clientes
├── agente_consultar.py      # Agente para consultar clientes
├── agente_recepcionista.py  # Router que clasifica intenciones
├── requirements.txt          # Dependencias del proyecto
├── .env.example             # Plantilla de variables de entorno
└── README.md                # Esta documentación
```

## Instalación

### 1. Clonar y navegar al directorio

```bash
cd server
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env y agregar tu API key de OpenAI
# OPENAI_API_KEY=tu-clave-api-aqui
```

## Uso

### Iniciar el servidor

```bash
# Opción 1: Usando uvicorn directamente
uvicorn api:app --reload --port 8000

# Opción 2: Usando Python
python api.py
```

El servidor estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## Endpoints de la API

### POST /chat
Enviar mensaje al sistema

**Headers:**
- `session-id` (opcional): ID de sesión. Si no se provee, se genera automáticamente.

**Body:**
```json
{
  "mensaje": "Crea un cliente llamado Juan con email juan@example.com"
}
```

**Response:**
```json
{
  "respuesta": "✅ Cliente creado: Juan (juan@example.com)",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "crear"
}
```

### GET /history/{session_id}
Obtener historial de una sesión

**Response:**
```json
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
    }
  ]
}
```

### DELETE /history/{session_id}
Eliminar historial de una sesión

**Response:**
```json
{
  "message": "Historial de sesión 550e8400-e29b-41d4-a716-446655440000 eliminado correctamente",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /health
Verificar estado del servidor

### GET /
Información de la API

## Ejemplos de uso

### Con cURL

#### Primera conversación (sin session-id)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "Crea un cliente llamado Juan con email juan@example.com"}'
```

#### Conversación continua (con session-id)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "session-id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"mensaje": "Ahora crea otro cliente llamado María con email maria@example.com"}'
```

#### Consultar clientes
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "session-id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"mensaje": "Lista todos los clientes"}'
```

#### Ver historial
```bash
curl http://localhost:8000/history/550e8400-e29b-41d4-a716-446655440000
```

### Con Python

```python
import requests

# Primera petición - genera session_id
response = requests.post(
    "http://localhost:8000/chat",
    json={"mensaje": "Crea un cliente llamado Juan con email juan@example.com"}
)
data = response.json()
session_id = data["session_id"]
print(f"Respuesta: {data['respuesta']}")

# Segunda petición - usa session_id
response = requests.post(
    "http://localhost:8000/chat",
    json={"mensaje": "Lista todos los clientes"},
    headers={"session-id": session_id}
)
print(response.json()["respuesta"])

# Ver historial
response = requests.get(f"http://localhost:8000/history/{session_id}")
print(response.json())
```

### Con JavaScript/Fetch

```javascript
// Primera petición
let sessionId = null;

const response1 = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mensaje: 'Crea un cliente llamado Juan con email juan@example.com'
  })
});

const data1 = await response1.json();
sessionId = data1.session_id;
console.log(data1.respuesta);

// Segunda petición con session_id
const response2 = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'session-id': sessionId
  },
  body: JSON.stringify({
    mensaje: 'Lista todos los clientes'
  })
});

const data2 = await response2.json();
console.log(data2.respuesta);
```

## Cómo funciona la memoria por sesiones

1. **Primera petición**: Si no se envía `session-id`, el servidor genera un UUID único
2. **Guardar mensaje**: El mensaje del usuario se almacena en la tabla `mensajes` con el `session_id`
3. **Cargar historial**: Se recuperan todos los mensajes de esa sesión desde la base de datos
4. **Procesar con memoria**: El agente recibe el historial completo de la conversación
5. **Guardar respuesta**: La respuesta del agente se almacena en la base de datos
6. **Continuidad**: El cliente guarda el `session_id` y lo envía en peticiones siguientes

## Estructura de la Base de Datos

### Tabla: clientes
| Campo  | Tipo    | Descripción        |
|--------|---------|-------------------|
| id     | Integer | Primary Key       |
| nombre | String  | Nombre del cliente|
| email  | String  | Email (unique)    |

### Tabla: mensajes
| Campo      | Tipo     | Descripción                    |
|------------|----------|--------------------------------|
| id         | Integer  | Primary Key                    |
| session_id | String   | ID de sesión (indexed)         |
| role       | String   | "user" o "assistant"           |
| content    | Text     | Contenido del mensaje          |
| timestamp  | DateTime | Fecha y hora del mensaje       |

## Agentes del Sistema

### 1. Agente Recepcionista (Router)
- Clasifica la intención del usuario
- Decide qué agente especializado debe manejar la solicitud
- Devuelve: "crear" o "consultar"

### 2. Agente Crear
- Especializado en crear clientes
- Valida que se tengan nombre y email antes de crear
- Si falta información, la solicita al usuario

### 3. Agente Consultar
- Especializado en listar y buscar clientes
- Recupera información de la base de datos

## Consideraciones de Producción

- Agregar autenticación de usuarios
- Implementar rate limiting
- Validar que session_id pertenece al usuario autenticado
- Configurar CORS con orígenes específicos
- Implementar limpieza periódica de sesiones antiguas
- Considerar encriptar mensajes sensibles
- Usar PostgreSQL en lugar de SQLite
- Implementar logging y monitoreo
- Agregar manejo de errores más robusto

## Troubleshooting

### Error: "No module named 'langchain'"
```bash
pip install -r requirements.txt
```

### Error: "OPENAI_API_KEY not found"
Asegúrate de tener el archivo `.env` con tu API key:
```bash
OPENAI_API_KEY=tu-clave-api-aqui
```

### Error: "Address already in use"
El puerto 8000 está ocupado. Usa otro puerto:
```bash
uvicorn api:app --reload --port 8001
```

## Licencia

Este proyecto es parte de un sistema de aprendizaje de LangChain y FastAPI.

## Soporte

Para reportar problemas o sugerir mejoras, por favor crea un issue en el repositorio.
