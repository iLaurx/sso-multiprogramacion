"""Transiciones del motor. El servicio externo decide cuándo llamar tick()."""

from collections import deque
from random import Random

from .generator import generate_process, generate_processes
from .models import Process, SimulationStatus, calculate


# * Identifica controles que no se pueden aplicar en el estado actual del motor.
# ? La API puede capturar esta excepción y usar su mensaje en una respuesta HTTP 409.
class SimulationStateError(RuntimeError):
    """Acción incompatible con el estado actual; la API puede traducirla a 409."""


# * Mantiene la simulación y coordina procesos en espera, en ejecución y terminados.
# ? Cada instancia conserva su propio reloj, colas y estado, independiente de las demás.
# ! No espera segundos reales ni controla concurrencia: esas tareas pertenecen al servicio.
class SimulationEngine:
    BLOCK_DURATION = 9

    # * Genera los trabajos, admite hasta tres en memoria y despacha el primer proceso en tiempo cero.
    # ? Recibe cantidad y semilla; la validación de ambas se delega al generador.
    def __init__(self, numero_trabajos: int, seed: int | None = None):
        if seed is not None and type(seed) is not int:
            raise ValueError("La semilla debe ser un entero o None")
        self._rng = Random(seed)
        processes = generate_processes(numero_trabajos, seed, rng=self._rng)
        self._next_id = numero_trabajos + 1
        self.total_trabajos = numero_trabajos
        self.clock = 0
        self.status: SimulationStatus = "running"
        self._new: deque[Process] = deque(processes)
        for process in self._new:
            process.estado = "new"
        # Conservamos _queue como cola de listos.
        self._queue: deque[Process] = deque()
        self._blocked: list[Process] = []
        self._current: Process | None = None
        self._finished: list[Process] = []
        self._dispatch()

    # * Punto de entrada público para construir y devolver una nueva simulación.
    # ? @classmethod recibe la clase en cls y llama a su constructor con cantidad y semilla.
    @classmethod
    def create(cls, numero_trabajos: int, seed: int | None = None) -> "SimulationEngine":
        """Construye una simulación running en tiempo cero."""
        return cls(numero_trabajos, seed)

    @property
    def memoria_ocupada(self) -> int:
        """Los bloqueados conservan su espacio aunque no usen CPU."""
        return len(self._queue) + len(self._blocked) + int(self._current is not None)

    def add_process(self) -> dict:
        """Genera un proceso en running, admite si cabe y devuelve una copia de sus datos."""
        if self.status != "running":
            raise SimulationStateError("Solo se pueden agregar procesos durante la ejecución")
        process = generate_process(self._next_id, self._rng)
        process.estado = "new"
        self._new.append(process)
        self._next_id += 1
        self.total_trabajos += 1
        self._dispatch()
        return process.snapshot()

    def _admit(self) -> None:
        """Admite nuevos al final de listos, sin superar tres residentes."""
        while self._new and self.memoria_ocupada < 3:
            process = self._new.popleft()
            process.estado = "ready"
            process.llegada = self.clock
            self._queue.append(process)

    def _dispatch(self) -> None:
        """Admite y despacha en FCFS; no desaloja un proceso activo."""
        self._admit()
        if self._current is None and self._queue:
            self._current = self._queue.popleft()
            self._current.estado = "running"
            if self._current.primera_atencion is None:
                self._current.primera_atencion = self.clock
        if self._current is None and not self._new and not self._queue and not self._blocked:
            self.status = "completed"

    # * Comprueba que hay un proceso ejecutándose antes de permitir tick, I o E.
    # ? Devuelve el proceso actual o genera SimulationStateError si el control es incompatible.
    def _require_running(self) -> Process:
        if self.status == "paused":
            raise SimulationStateError("La simulación está pausada")
        if self.status != "running" or self._current is None:
            raise SimulationStateError("No hay un proceso activo")
        return self._current

    # * Ejecuta una unidad: suma tiempo y, al alcanzar el TME, calcula y guarda el resultado.
    # ? Devuelve None; para obtener el nuevo estado hay que consultar snapshot().
    # ! Despachar el siguiente no añade tiempo; en paused o completed no cambia nada.
    def tick(self) -> None:
        """Avanza un segundo simulado; pausa y final son operaciones sin cambios."""
        if self.status != "running":
            return
        # El intervalo se cuenta según el estado de cada residente al comenzar.
        # Un proceso desbloqueado se despacha al final y ejecuta desde el próximo tick.
        process = self._current
        # Solo cuentan quienes estaban listos durante este intervalo.
        # Nuevos y desbloqueados al final del tick empiezan a esperar después.
        for ready in self._queue:
            ready.espera += 1
        self.clock += 1
        if process is not None:
            process.ejecutado += 1
            if process.ejecutado == process.tme:
                process.resultado = calculate(process.operacion, process.operando_a, process.operando_b)
                process.estado = "finished"
                process.finalizacion = self.clock
                self._finished.append(process)
                self._current = None
        for blocked in self._blocked[:]:
            blocked.bloqueado += 1
            if self.clock - blocked.inicio_bloqueo >= self.BLOCK_DURATION:
                self._blocked.remove(blocked)
                blocked.inicio_bloqueo = None
                blocked.estado = "ready"
                self._queue.append(blocked)
        # Si coinciden desbloqueo y finalización, el desbloqueado se encola
        # antes del nuevo admitido, siempre detrás de los listos existentes.
        self._dispatch()

    # * Bloquea durante 9 segundos simulados sin liberar memoria (E en actividad 8).
    # ? Conserva el servicio y no avanza el reloj al aplicar la acción.
    def interrupt(self) -> None:
        process = self._require_running()
        process.estado = "blocked"
        process.inicio_bloqueo = self.clock
        self._blocked.append(process)
        self._current = None
        self._dispatch()

    # * Guarda el actual como error (W en actividad 8) y permite que siga el próximo.
    # ? El resultado queda en None; la interfaz identifica ERROR por el campo estado.
    # ! No completa artificialmente el TME ni agrega segundos al reloj.
    def fail(self) -> None:
        process = self._require_running()
        process.estado = "error"
        process.finalizacion = self.clock
        process.resultado = None
        self._finished.append(process)
        self._current = None
        self._dispatch()

    # * Aplica P: cambia el motor a paused para que los siguientes ticks no avancen.
    # ? Repetir P en pausa es válido; una simulación completed genera SimulationStateError.
    def pause(self) -> None:
        if self.status == "completed":
            raise SimulationStateError("La simulación ya terminó")
        self.status = "paused"

    # * Aplica C: cambia a running y permite continuar desde el tiempo que ya se ejecutó.
    # ? Repetir C en running es válido; no altera procesos ni tiempos.
    # ! Una simulación completed no se reinicia: hay que crear otra instancia.
    def resume(self) -> None:
        if self.status == "completed":
            raise SimulationStateError("La simulación ya terminó")
        self.status = "running"

    # * Reúne el estado del motor y las copias de sus procesos en un diccionario nuevo.
    # ? en_espera conserva su nombre y representa la cola de listos en orden FCFS.
    # ! Solo lee el estado: no llama tick ni devuelve referencias a los procesos internos.
    def snapshot(self) -> dict:
        """Copia serializable; no avanza tiempo ni expone objetos internos."""
        return {
            "estado": self.status,
            "reloj": self.clock,
            "nuevos": [process.snapshot() for process in self._new],
            "bloqueados": [
                {
                    **process.snapshot(),
                    "bloqueo_transcurrido": self.clock - process.inicio_bloqueo,
                    "bloqueo_restante": self.BLOCK_DURATION - (self.clock - process.inicio_bloqueo),
                }
                for process in self._blocked
            ],
            "memoria_ocupada": self.memoria_ocupada,
            "total_trabajos": self.total_trabajos,
            "en_ejecucion": self._current.snapshot() if self._current else None,
            "en_espera": [process.snapshot() for process in self._queue],
            "terminados": [process.snapshot() for process in self._finished],
        }

    def processes_snapshot(self) -> list[dict]:
        """Consulta todos los procesos por ID, con tiempos y bloqueo restante; sin pausar."""
        state = self.snapshot()
        processes = state["nuevos"] + state["en_espera"] + state["bloqueados"] + state["terminados"]
        if state["en_ejecucion"] is not None:
            processes.append(state["en_ejecucion"])
        return sorted(processes, key=lambda process: process["id"])
