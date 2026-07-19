MAQUINAS = {
    "prueba_electrica": "Prueba eléctrica",
    "dimensiones": "Dimensiones",
    "rotary": "Rotary",
    "sistema_navegacion": "Sistema de navegación",
}

MAQUINA_OPTIONS = [
    {"id": key, "label": label}
    for key, label in MAQUINAS.items()
]


def maquina_label(maquina_id: str) -> str:
    return MAQUINAS.get(maquina_id, maquina_id or "Sin máquina")
