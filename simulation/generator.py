"""Generación reproducible sin modificar el generador aleatorio global."""

from random import Random

from .models import Process


# * Valida la entrada y devuelve trabajos nuevos, ordenados por ID y agrupados de tres.
# ? numero_trabajos es un entero positivo; seed permite repetir los mismos datos.
# ! Una cantidad o semilla de tipo incorrecto genera ValueError antes de crear trabajos.
def generate_processes(
    numero_trabajos: int, seed: int | None = None, *, rng: Random | None = None
) -> list[Process]:
    # ! bool hereda de int: type(...) is int evita aceptar True como un trabajo.
    if type(numero_trabajos) is not int or numero_trabajos <= 0:
        raise ValueError("El número de trabajos debe ser un entero positivo")
    if seed is not None and type(seed) is not int:
        raise ValueError("La semilla debe ser un entero o None")
    # ? Este generador es local: no altera el estado aleatorio de otros módulos.
    rng = rng if rng is not None else Random(seed)
    return [generate_process(process_id, rng) for process_id in range(1, numero_trabajos + 1)]


def generate_process(process_id: int, rng: Random) -> Process:
    """Genera los datos de un proceso usando el azar privado de la simulación."""
    tme = rng.randint(7, 18)
    operation = rng.choice(("+", "-", "*", "/", "%"))
    a, b = rng.randint(-99, 99), rng.randint(-99, 99)
    while operation in ("/", "%") and b == 0:
        b = rng.randint(-99, 99)
    return Process(process_id, (process_id - 1) // 3 + 1, operation, a, b, tme)
