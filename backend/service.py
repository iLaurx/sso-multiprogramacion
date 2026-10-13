import asyncio
import uuid
from typing import Dict
from simulation import SimulationEngine, SimulationStateError

class RegistroSimulacion:
    def __init__(self, motor: SimulationEngine, lock: asyncio.Lock, task: asyncio.Task | None = None):
        self.motor = motor
        self.lock = lock
        self.task = task

class SimulationService:
    def __init__(self, auto_clock: bool = True):
        self.simulaciones: Dict[str, RegistroSimulacion] = {}
        self.auto_clock = auto_clock

    async def _clock_task(self, simulacion_id: str):
        while True:
            await asyncio.sleep(1)
            registro = self.simulaciones.get(simulacion_id)
            if not registro:
                break
            async with registro.lock:
                if registro.motor.status == "completed":
                    break
                registro.motor.tick()

    async def create(self, numero_trabajos: int, seed: int | None = None) -> dict:
        motor = SimulationEngine.create(numero_trabajos=numero_trabajos, seed=seed)
        simulacion_id = str(uuid.uuid4())
        lock = asyncio.Lock()
        
        task = None
        if self.auto_clock:
            task = asyncio.create_task(self._clock_task(simulacion_id))
            
        registro = RegistroSimulacion(motor=motor, lock=lock, task=task)
        self.simulaciones[simulacion_id] = registro
        
        async with lock:
            return {"simulacion_id": simulacion_id, **motor.snapshot()}

    async def get_snapshot(self, simulacion_id: str) -> dict | None:
        registro = self.simulaciones.get(simulacion_id)
        if not registro:
            return None
        async with registro.lock:
            return {"simulacion_id": simulacion_id, **registro.motor.snapshot()}

    async def apply_action(self, simulacion_id: str, accion: str) -> dict:
        registro = self.simulaciones.get(simulacion_id)
        if not registro:
            raise KeyError("Simulación no encontrada")
            
        async with registro.lock:
            if accion == "interrupt":
                registro.motor.interrupt()
            elif accion == "error":
                registro.motor.fail()
            elif accion == "pause":
                registro.motor.pause()
            elif accion == "continue":
                registro.motor.resume()
            
            return {"simulacion_id": simulacion_id, **registro.motor.snapshot()}

    async def tick_once(self, simulacion_id: str):
        registro = self.simulaciones.get(simulacion_id)
        if registro:
            async with registro.lock:
                registro.motor.tick()

    async def close(self):
        for registro in self.simulaciones.values():
            if registro.task and not registro.task.done():
                registro.task.cancel()
        self.simulaciones.clear()