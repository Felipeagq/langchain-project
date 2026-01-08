from database import engine, Base
from agente_crear import agente_crear
from agente_consultar import agente_consultar
from agente_recepcionista import router_chain

def init_db():
    Base.metadata.create_all(bind=engine)

def procesar_mensaje(mensaje: str):
    decision = router_chain.invoke(
        {"mensaje": mensaje}
    )["text"].strip().lower()

    print(f"\n🧭 Recepcionista decidió → {decision}")

    if decision == "crear":
        return agente_crear.invoke(mensaje)

    elif decision == "consultar":
        return agente_consultar.invoke(mensaje)

    else:
        return "❓ No entendí la solicitud"

if __name__ == "__main__":
    init_db()

    print("🤖 Sistema Multi-Agente iniciado")
    print("Escribe 'salir' para terminar\n")

    while True:
        user_input = input("Cliente: ")
        if user_input.lower() in ["salir", "exit"]:
            break

        respuesta = procesar_mensaje(user_input)
        print("\nSistema:", respuesta)
