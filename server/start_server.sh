#!/bin/bash

echo "🚀 Iniciando servidor de chat con memoria persistente..."
echo ""

# Verificar que exista .env
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado"
    echo "📝 Creando .env desde .env.example..."
    cp .env.example .env
    echo "⚠️  Por favor edita el archivo .env y agrega tu OPENAI_API_KEY"
    echo "   Luego ejecuta este script nuevamente"
    exit 1
fi

# Verificar que OPENAI_API_KEY esté configurada
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "tu-clave-api-aqui" ]; then
    echo "❌ OPENAI_API_KEY no está configurada en .env"
    echo "📝 Por favor edita .env y agrega tu API key de OpenAI"
    exit 1
fi

echo "✅ Configuración validada"
echo ""

# Iniciar servidor
echo "🌐 Servidor disponible en: http://localhost:8000"
echo "📚 Documentación: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

uvicorn api:app --reload --port 8000
