from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base


class Cliente(Base):
    """Modelo para almacenar clientes"""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Cliente nombre={self.nombre} email={self.email}>"


class Mensaje(Base):
    """Modelo para almacenar mensajes de conversaciones por sesión"""
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)  # Identificador único de sesión
    role = Column(String, nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)  # Contenido del mensaje
    timestamp = Column(DateTime, default=datetime.utcnow)  # Fecha/hora

    def __repr__(self):
        return f"<Mensaje session={self.session_id} role={self.role}>"
