"""Datos de cada trabajo y cálculo explícito de operaciones."""

from dataclasses import dataclass
from typing import Literal

# ? Literal describe los valores permitidos para el análisis de tipos;
# ? no valida por sí mismo los datos al ejecutar el programa.
Operation = Literal["+", "-", "*", "/", "%"]
ProcessStatus = Literal["new", "ready", "running", "blocked", "finished", "error"]
SimulationStatus = Literal["running", "paused", "completed"]


# * Resuelve la operación mediante una rama explícita para cada símbolo, sin eval.
# ? Recibe el símbolo y dos operandos; devuelve un entero o un real en división.
# ! El generador debe evitar b=0 para / y %. Un símbolo desconocido genera ValueError.
def calculate(operation: Operation, a: int, b: int) -> int | float:
    if operation == "+":
        return a + b
    if operation == "-":
        return a - b
    if operation == "*":
        return a * b
    if operation == "/":
        return a / b
    if operation == "%":
        return a % b
    raise ValueError("Operación no válida")


# * Representa un trabajo: identidad, lote, operación, tiempos, estado y resultado.
# ? dataclass genera el constructor a partir de estos campos y sus valores iniciales.
# ? Un trabajo nuevo está ready, lleva cero segundos y todavía no tiene resultado.
@dataclass
class Process:
    id: int
    lote: int
    operacion: Operation
    operando_a: int
    operando_b: int
    tme: int
    ejecutado: int = 0
    estado: ProcessStatus = "ready"
    resultado: int | float | None = None

    # Instantes del reloj simulado; None indica que el evento aún no ocurrió.
    # Llegada corresponde a la admisión a memoria, no a la generación.
    llegada: int | None = None
    primera_atencion: int | None = None
    finalizacion: int | None = None
    inicio_bloqueo: int | None = None

    # Duraciones en segundos simulados. Espera solo cuenta el tiempo en listos;
    # bloqueado acumula el tiempo de E/S y ejecutado sigue siendo el servicio.
    # El motor acumula espera en listos y bloqueado durante E/S en cada tick.
    espera: int = 0
    bloqueado: int = 0

    @property
    def retorno(self) -> int | None:
        """Duración desde la admisión a memoria hasta la finalización."""
        if self.llegada is None or self.finalizacion is None:
            return None
        return self.finalizacion - self.llegada

    @property
    def respuesta(self) -> int | None:
        """Demora hasta el primer despacho; cero es una respuesta válida."""
        if self.llegada is None or self.primera_atencion is None:
            return None
        return self.primera_atencion - self.llegada

    # * Calcula el tiempo pendiente cada vez que se consulta, sin almacenarlo aparte.
    # ? @property permite leer proceso.restante sin escribir paréntesis.
    # ! Un terminado por error tiene restante=0 aunque no haya consumido todo su TME.
    @property
    def restante(self) -> int:
        if self.estado in ("finished", "error"):
            return 0
        return self.tme - self.ejecutado

    # * Construye un diccionario nuevo con los datos del proceso para enviarlos como JSON.
    # ? Incluye restante como valor calculado; consultar esta copia no modifica el proceso.
    def snapshot(self) -> dict:
        return {
            "id": self.id,
            "estado": self.estado,
            "operacion": self.operacion,
            "operando_a": self.operando_a,
            "operando_b": self.operando_b,
            "tme": self.tme,
            "ejecutado": self.ejecutado,
            "restante": self.restante,
            "resultado": self.resultado,
            "llegada": self.llegada,
            "primera_atencion": self.primera_atencion,
            "finalizacion": self.finalizacion,
            "retorno": self.retorno,
            "respuesta": self.respuesta,
            "espera": self.espera,
            "bloqueado": self.bloqueado,
            "inicio_bloqueo": self.inicio_bloqueo,
        }
