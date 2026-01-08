# 🤖 Sistema Multi-Agente con LangChain

Proyecto de demostración de sistemas multi-agente inteligentes usando LangChain, OpenAI y SQLAlchemy. Incluye dos implementaciones: una versión de línea de comandos simple y una API REST completa con memoria persistente por sesiones.

---

## 📁 Estructura del Proyecto

```
lchain/
├── agente_sencillo/          # Versión CLI básica
│   ├── main.py               # Punto de entrada (terminal interactiva)
│   ├── agente_recepcionista.py  # Router que clasifica intenciones
│   ├── agente_crear.py       # Agente para crear clientes
│   ├── agente_consultar.py   # Agente para consultar clientes
│   ├── database.py           # Configuración de SQLAlchemy
│   ├── models.py             # Modelos de BD (Cliente)
│   ├── tools.py              # Herramientas de LangChain
│   └── llm.py                # Configuración del modelo LLM
│
└── server/                   # Versión API REST avanzada
    ├── entrypoint.py         # Servidor FastAPI
    ├── memory_manager.py     # Gestor de memoria persistente
    ├── agente_recepcionista.py  # Router con contexto
    ├── agente_crear.py       # Agente crear con memoria
    ├── agente_consultar.py   # Agente consultar con memoria
    ├── database.py           # Configuración de SQLAlchemy
    ├── models.py             # Modelos de BD (Cliente, Mensaje)
    ├── tools.py              # Herramientas de LangChain
    ├── llm.py                # Configuración del modelo LLM
    └── README.md             # Documentación detallada del servidor
```

---

## 🎯 Características Principales

### Agente Sencillo (CLI)
- ✅ Sistema multi-agente con router inteligente
- ✅ Terminal interactiva simple
- ✅ Persistencia de clientes en SQLite
- ✅ Clasificación automática de intenciones
- ✅ Ideal para pruebas rápidas y demos

### Server (API REST)
- ✅ API REST completa con FastAPI
- ✅ **Memoria persistente por sesiones**
- ✅ **Contexto multi-mensaje**: Mantiene conversaciones naturales
- ✅ Múltiples sesiones simultáneas independientes
- ✅ Historial de conversaciones en base de datos
- ✅ Router con análisis de contexto
- ✅ Documentación interactiva (Swagger/OpenAPI)
- ✅ CORS configurado para integraciones frontend
- ✅ Ideal para producción y aplicaciones web

---

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.9+
- OpenAI API Key
- pip / virtualenv

### 1. Instalación General

```bash
# Clonar el repositorio
git clone <tu-repo>
cd lchain

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
OPENAI_API_KEY=tu-clave-api-aqui
```

---

## 💻 Uso del Agente Sencillo (CLI)

### Ejecutar

```bash
cd agente_sencillo
python main.py
```

### Ejemplo de Uso

```
🤖 Sistema Multi-Agente iniciado
Escribe 'salir' para terminar

Cliente: Crea un cliente llamado Juan con email juan@example.com

🧭 Recepcionista decidió → crear

> Entering new AgentExecutor chain...
✅ Cliente creado: Juan (juan@example.com)

Sistema: ✅ Cliente creado: Juan (juan@example.com)

Cliente: Lista todos los clientes

🧭 Recepcionista decidió → consultar

📋 Clientes registrados:
  1. Juan - juan@example.com

Cliente: salir
```

### Características

- Interfaz de línea de comandos interactiva
- Sin memoria de conversaciones (cada mensaje es independiente)
- Base de datos `clientes.db` en SQLite
- Perfecto para desarrollo y pruebas locales

---

## 🌐 Uso del Server (API REST)

### Ejecutar

```bash
cd server
python entrypoint.py
```

O con uvicorn:

```bash
uvicorn server.entrypoint:app --reload --port 5050
```

El servidor estará disponible en: `http://localhost:5050`

Documentación interactiva: `http://localhost:5050/docs`


### Características Avanzadas

#### 1. Memoria Persistente por Sesiones
- Cada sesión (session_id) mantiene su propio historial
- El historial sobrevive a reinicios del servidor
- Múltiples usuarios pueden chatear simultáneamente de forma independiente

#### 2. Contexto Multi-Mensaje
- El sistema recuerda toda la conversación
- No necesitas repetir información en cada mensaje
- Conversaciones naturales de varios turnos

**Ejemplo:**
```
Usuario: "Quiero crear un cliente"
Sistema: "¿Cuál es el nombre?"

Usuario: "Juan"  ← No necesita decir "el nombre es Juan"
Sistema: "¿Cuál es el email?"

Usuario: "juan@email.com"  ← El sistema recuerda "Juan"
Sistema: "✅ Cliente creado: Juan (juan@email.com)"
```

#### 3. Router con Análisis de Contexto
- El router considera el historial completo
- Mantiene la intención correcta en conversaciones largas
- Si estás creando un cliente, sigue en modo "crear" aunque solo digas "Felipe"

---

## 🏗️ Arquitectura del Sistema

### Flujo de Procesamiento

```
1. Usuario envía mensaje
   ↓
2. Sistema carga historial de la sesión (si existe)
   ↓
3. Router analiza mensaje + contexto
   ↓
4. Decide: "crear" o "consultar"
   ↓
5. Agente especializado procesa con contexto completo
   ↓
6. Respuesta se guarda en BD junto con mensaje
   ↓
7. Cliente recibe respuesta + session_id
```

### Componentes Principales

#### 🎯 Agente Recepcionista (Router)
- Clasifica la intención del usuario
- Analiza el contexto de mensajes previos
- Decide qué agente especializado debe actuar
- Retorna: "crear" o "consultar"

#### ➕ Agente Crear
- Especializado en crear clientes
- Valida que tenga nombre y email
- Extrae información del historial
- Solicita datos faltantes
- Ejecuta herramienta `crear_cliente`

#### 🔍 Agente Consultar
- Especializado en consultar clientes
- Lista clientes de la base de datos
- Puede filtrar resultados según contexto
- Ejecuta herramienta `consultar_clientes`

#### 💾 Memory Manager (Solo Server)
- Gestiona persistencia del historial
- Carga/guarda mensajes en SQLite
- Convierte entre formatos de LangChain y BD
- Permite múltiples sesiones independientes

---

## 📊 Base de Datos

### Tabla: `clientes` (Ambos proyectos)
| Campo  | Tipo    | Descripción        |
|--------|---------|-------------------|
| id     | Integer | Primary Key       |
| nombre | String  | Nombre del cliente|
| email  | String  | Email (unique)    |

### Tabla: `mensajes` (Solo Server)
| Campo      | Tipo     | Descripción                    |
|------------|----------|--------------------------------|
| id         | Integer  | Primary Key                    |
| session_id | String   | ID de sesión (indexed)         |
| role       | String   | "user" o "assistant"           |
| content    | Text     | Contenido del mensaje          |
| timestamp  | DateTime | Fecha y hora del mensaje       |

---

## 🔧 Tecnologías Utilizadas

- **LangChain**: Framework para aplicaciones con LLMs
- **OpenAI GPT-4o-mini**: Modelo de lenguaje
- **FastAPI**: Framework web moderno (Server)
- **SQLAlchemy**: ORM para base de datos
- **SQLite**: Base de datos local
- **Pydantic**: Validación de datos
- **Python-dotenv**: Gestión de variables de entorno

---

## 🔐 Seguridad y Mejores Prácticas

### Variables de Entorno
- ✅ Nunca incluyas tu API key en el código
- ✅ Usa archivo `.env` para secrets
- ✅ Agrega `.env` al `.gitignore`

### Producción (Server)
- 🔒 Implementar autenticación de usuarios
- 🔒 Rate limiting para prevenir abuso
- 🔒 Validar que session_id pertenece al usuario autenticado
- 🔒 Configurar CORS con orígenes específicos
- 🔒 Usar PostgreSQL en lugar de SQLite
- 🔒 Implementar logging y monitoreo
- 🔒 Encriptar mensajes sensibles en BD

---

## 🐛 Troubleshooting

### Error: "No module named 'langchain'"
```bash
pip install -r requirements.txt
```

### Error: "OPENAI_API_KEY not found"
Crea un archivo `.env` con tu clave:
```bash
echo "OPENAI_API_KEY=tu-clave-aqui" > .env
```
---

## 📚 Recursos Adicionales

- [Documentación de LangChain](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

