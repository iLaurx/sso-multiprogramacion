"""Transiciones del motor. El servicio externo decide cuándo llamar tick()."""

from collections import deque

from .generator import generate_processes
from .models import Process, SimulationStatus, calculate


# * Identifica controles que no se pueden aplicar en el estado actual del motor.
# ? La API puede capturar esta excepción y usar su mensaje en una respuesta HTTP 409.
class SimulationStateError(RuntimeError):
    """Acción incompatible con el estado actual; la API puede traducirla a 409."""


# * Mantiene la simulación y coordina procesos en espera, en ejecución y terminados.
# ? Cada instancia conserva su propio reloj, lotes y estado, independiente de las demás.
# ! No espera segundos reales ni controla concurrencia: esas tareas pertenecen al servicio.
class SimulationEngine:
    # * Genera los trabajos, prepara los lotes y despacha el primer proceso en tiempo cero.
    # ? Recibe cantidad y semilla; la validación de ambas se delega al generador.
    def __init__(self, numero_trabajos: int, seed: int | None = None):
        processes = generate_processes(numero_trabajos, seed)
        self.total_trabajos = numero_trabajos
        self.clock = 0
        self.status: SimulationStatus = "running"
        # ? deque permite retirar el primer lote o proceso sin desplazar toda la colección.
        self._pending_batches = deque(
            processes[start:start + 3] for start in range(0, numero_trabajos, 3)
        )
        # ? _queue contiene solo la espera del lote activo; los futuros siguen separados.
        self._queue: deque[Process] = deque()
        self._current: Process | None = None
        self._batch: int | None = None
        self._finished: list[Process] = []
        self._dispatch()

    # * Punto de entrada público para construir y devolver una nueva simulación.
    # ? @classmethod recibe la clase en cls y llama a su constructor con cantidad y semilla.
    @classmethod
    def create(cls, numero_trabajos: int, seed: int | None = None) -> "SimulationEngine":
        """Construye una simulación running en tiempo cero."""
        return cls(numero_trabajos, seed)

    # * Selecciona el siguiente proceso; si se agotó la cola, carga el siguiente lote.
    # ? popleft retira el primero, respetando el orden de la cola; no consume tiempo.
    # ! Se llama al inicio o después de retirar/reencolar el actual, nunca mientras sigue activo.
    def _dispatch(self) -> None:
        if not self._queue and self._pending_batches:
            batch = self._pending_batches.popleft()
            self._batch = batch[0].lote
            self._queue.extend(batch)
        if self._queue:
            self._current = self._queue.popleft()
            self._current.estado = "running"
        else:
            # * Sin cola ni lotes pendientes, cierra la simulación y conserva los terminados.
            self._current = None
            self._batch = None
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
        process = self._require_running()
        self.clock += 1
        process.ejecutado += 1
        if process.ejecutado == process.tme:
            process.resultado = calculate(process.operacion, process.operando_a, process.operando_b)
            process.estado = "finished"
            self._finished.append(process)
            self._dispatch()

    # * Aplica I: pasa el actual a ready, lo coloca al final y despacha el primero de la cola.
    # ? Si es el único proceso vivo del lote, vuelve a quedar en ejecución él mismo.
    # ! Conserva ejecutado y el reloj; no mueve el proceso a otro lote.
    def interrupt(self) -> None:
        process = self._require_running()
        process.estado = "ready"
        self._queue.append(process)
        self._dispatch()

    # * Aplica E: guarda el actual como error y permite que siga el próximo proceso.
    # ? El resultado queda en None; la interfaz identifica ERROR por el campo estado.
    # ! No completa artificialmente el TME ni agrega segundos al reloj.
    def fail(self) -> None:
        process = self._require_running()
        process.estado = "error"
        process.resultado = None
        self._finished.append(process)
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
    # ? Los lotes pendientes excluyen el activo; en_espera respeta el orden real de su cola.
    # ! Solo lee el estado: no llama tick ni devuelve referencias a los procesos internos.
    def snapshot(self) -> dict:
        """Copia serializable; no avanza tiempo ni expone objetos internos."""
        return {
            "estado": self.status,
            "reloj": self.clock,
            "lote_actual": self._batch,
            "lotes_pendientes": len(self._pending_batches),
            "total_trabajos": self.total_trabajos,
            "en_ejecucion": self._current.snapshot() if self._current else None,
            "en_espera": [process.snapshot() for process in self._queue],
            "terminados": [process.snapshot() for process in self._finished],
        }
