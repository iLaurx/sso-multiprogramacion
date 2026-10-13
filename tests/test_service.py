import asyncio

from backend.service import SimulationService


def test_cierre_termina_las_tareas_del_reloj():
    async def comprobar():
        servicio = SimulationService(auto_clock=True)
        estado = await servicio.create(3, seed=123)

        registro = servicio.simulaciones[estado["simulacion_id"]]
        tarea = registro.task

        # Permitir que la tarea del reloj comience.
        await asyncio.sleep(0)

        await servicio.close()

        assert tarea.done()
        assert tarea.cancelled()
        assert servicio.simulaciones == {}

    asyncio.run(comprobar())