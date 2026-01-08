from langchain.memory import ConversationBufferMemory
from database import SessionLocal
from models import Mensaje
from typing import List


class PersistentMemoryManager:
    """
    Gestiona la memoria de conversaciones con persistencia en base de datos.
    Permite guardar, recuperar y limpiar el historial de mensajes por sesión.
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

        Args:
            session_id: Identificador único de la sesión

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

        Args:
            session_id: Identificador único de la sesión

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

        Args:
            session_id: Identificador único de la sesión
        """
        db = SessionLocal()
        try:
            db.query(Mensaje)\
                .filter(Mensaje.session_id == session_id)\
                .delete()
            db.commit()
        finally:
            db.close()
