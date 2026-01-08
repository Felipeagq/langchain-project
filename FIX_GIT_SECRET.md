# 🔐 Solución: API Key expuesta en Git

GitHub bloqueó tu push porque detectó una API Key de OpenAI en el commit `d9eeb81`.

## Paso 1: Revertir el último commit (mantener cambios)

```bash
git reset --soft HEAD~1
```

Esto deshace el commit pero mantiene todos tus cambios.

## Paso 2: Verificar que el archivo llm.py esté correcto

Abre `server/llm.py` y asegúrate de que NO contenga la API key directamente:

```python
# ✅ CORRECTO - Usa variable de entorno
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

# ❌ INCORRECTO - API key hardcodeada
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key="sk-proj-..."  # ¡NO HACER ESTO!
)
```

## Paso 3: Verificar que existe el archivo .env

```bash
ls -la server/.env
```

Si no existe, créalo:

```bash
echo "OPENAI_API_KEY=tu-clave-aqui" > server/.env
```

## Paso 4: Asegurarte de que .env esté en .gitignore

```bash
# Verificar si .env está ignorado
cat .gitignore | grep .env

# Si no está, agregarlo
echo ".env" >> .gitignore
echo "**/.env" >> .gitignore
```

## Paso 5: Hacer el commit nuevamente (limpio)

```bash
# Ver qué archivos están listos para commit
git status

# Agregar archivos (sin .env)
git add .

# Hacer commit
git commit -m "Implementar sistema de contexto multi-mensaje con memoria persistente"
```

## Paso 6: Push al repositorio

```bash
git push origin master
```

## ⚠️ IMPORTANTE: Rotar la API Key

Aunque elimines la key del repositorio, GitHub la vio y es posible que OpenAI también. Debes:

1. **Ir a OpenAI Dashboard**: https://platform.openai.com/api-keys
2. **Revocar la API key comprometida**
3. **Generar una nueva API key**
4. **Actualizar tu archivo .env local**:
   ```bash
   echo "OPENAI_API_KEY=tu-nueva-clave" > server/.env
   ```

## Verificación Final

Antes de hacer push, verifica que no haya secretos:

```bash
# Buscar posibles API keys en archivos staged
git diff --cached | grep -i "sk-"
git diff --cached | grep -i "api_key"

# Si encuentra algo, revisa esos archivos
```

## Si el problema persiste

Si aún así GitHub bloquea el push, es porque el commit anterior sigue en el historial. En ese caso:

```bash
# Ver el historial
git log --oneline -5

# Si ves el commit problemático (d9eeb81), necesitas reescribir el historial
# ADVERTENCIA: Esto reescribe el historial
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch server/llm.py" \
  --prune-empty --tag-name-filter cat -- --all

# O usar git-filter-repo (más moderno):
# pip install git-filter-repo
# git filter-repo --path server/llm.py --invert-paths

# Después de limpiar:
git push origin master --force
```

## Alternativa más simple: Empezar de cero en una nueva rama

Si todo lo demás falla:

```bash
# Crear una nueva rama limpia
git checkout -b master-clean

# Copiar solo los archivos que quieres (sin historial)
git add server/
git commit -m "Sistema multi-agente con memoria persistente (limpio)"

# Eliminar la rama master antigua
git branch -D master

# Renombrar la nueva rama a master
git branch -m master

# Force push
git push origin master --force
```

---

## Resumen de comandos rápidos

```bash
# 1. Deshacer commit
git reset --soft HEAD~1

# 2. Verificar que llm.py no tenga la key
cat server/llm.py | grep -i "sk-"

# 3. Asegurar .env en .gitignore
echo ".env" >> .gitignore

# 4. Commit limpio
git add .
git commit -m "Implementar sistema de contexto multi-mensaje"

# 5. Push
git push origin master
```

**¡No olvides rotar tu API key en OpenAI!**
