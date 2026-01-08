# Ejemplo: Conversación Multi-Mensaje con Contexto

Este archivo muestra cómo el sistema ahora mantiene el contexto entre mensajes.

## Escenario 1: Crear cliente en varios mensajes

### Mensaje 1
```json
POST /chat
{
  "mensaje": "Quiero crear un cliente"
}
```

**Sistema:**
- 📥 Mensaje del usuario: Quiero crear un cliente
- 📭 No hay historial previo (primera interacción)
- 🤖 Decisión del router (con contexto): crear
- ➕ Procesando con agente CREAR...
- 📤 Respuesta: "Claro, ¿cuál es el nombre del cliente?"

### Mensaje 2 (mismo session-id)
```json
POST /chat
Headers: { "session-id": "550e8400-..." }
{
  "mensaje": "Juan Pérez"
}
```

**Sistema:**
- 📥 Mensaje del usuario: Juan Pérez
- 📚 Historial previo cargado: 2 mensajes
- 🤖 Decisión del router (con contexto): crear ← **Mantiene el contexto!**
- ➕ Procesando con agente CREAR...
- 📤 Respuesta: "Perfecto, ¿cuál es el email de Juan Pérez?"

### Mensaje 3 (mismo session-id)
```json
POST /chat
Headers: { "session-id": "550e8400-..." }
{
  "mensaje": "juan@example.com"
}
```

**Sistema:**
- 📥 Mensaje del usuario: juan@example.com
- 📚 Historial previo cargado: 4 mensajes
- 🤖 Decisión del router (con contexto): crear ← **Sigue entendiendo el contexto!**
- ➕ Procesando con agente CREAR...
- 📤 Respuesta: "✅ Cliente creado: Juan Pérez (juan@example.com)"

---

## Escenario 2: Consultar con refinamiento

### Mensaje 1
```json
POST /chat
{
  "mensaje": "Lista los clientes"
}
```

**Sistema:**
- 🤖 Decisión: consultar
- 📤 Respuesta: "Clientes registrados: Juan Pérez, María García, Carlos López"

### Mensaje 2 (mismo session-id)
```json
POST /chat
Headers: { "session-id": "550e8400-..." }
{
  "mensaje": "Solo los que tienen gmail"
}
```

**Sistema:**
- 📚 Historial previo cargado: 2 mensajes
- 🤖 Decisión del router (con contexto): consultar ← **Entiende que sigue consultando!**
- 🔍 Procesando con agente CONSULTAR...
- 📤 Respuesta: "Clientes con Gmail: María García (maria@gmail.com)"

---

## Comparación: Antes vs Ahora

### ❌ ANTES (sin contexto)
```
Usuario: "Quiero crear un cliente"
Sistema: "crear" ✓

Usuario: "Juan Pérez"
Sistema: "consultar" ✗ (pierde el contexto, no sabe qué hacer con "Juan Pérez")
```

### ✅ AHORA (con contexto)
```
Usuario: "Quiero crear un cliente"
Sistema: "crear" ✓

Usuario: "Juan Pérez"
Sistema: "crear" ✓ (mantiene el contexto, sabe que es parte de crear cliente)
```

---

## Cómo funciona internamente

1. **Cargar historial**: Antes de decidir, se carga el historial completo de la sesión
2. **Router con memoria**: El router recibe el mensaje ACTUAL + HISTORIAL
3. **LLM analiza contexto**: El modelo ve toda la conversación para decidir
4. **Mantiene intención**: Si el usuario está continuando una tarea, mantiene la misma decisión
5. **Agentes procesan**: Los agentes especializados también ven el historial completo

## Ventajas

- ✅ Conversaciones más naturales
- ✅ No necesitas repetir la intención en cada mensaje
- ✅ Puedes proporcionar información gradualmente
- ✅ El sistema "recuerda" qué estabas haciendo
- ✅ Funciona incluso después de reiniciar el servidor (persiste en BD)
