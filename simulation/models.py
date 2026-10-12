"""Datos de cada trabajo y cálculo explícito de operaciones."""

from dataclasses import dataclass
from typing import Literal

# ? Literal describe los valores permitidos para el análisis de tipos;
# ? no valida por sí mismo los datos al ejecutar el programa.
Operation = Literal["+", "-", "*", "/", "%"]
ProcessStatus = Literal["ready", "running", "finished", "error"]
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
            "lote": self.lote,
            "estado": self.estado,
            "operacion": self.operacion,
            "operando_a": self.operando_a,
            "operando_b": self.operando_b,
            "tme": self.tme,
            "ejecutado": self.ejecutado,
            "restante": self.restante,
            "resultado": self.resultado,
        }
