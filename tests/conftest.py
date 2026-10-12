import pytest

from simulation import Process, SimulationEngine


# * Ofrece a las pruebas una fábrica de motores con trabajos de datos conocidos.
# ? pytest entrega esta fixture a las pruebas que declaran el parámetro known_engine.
@pytest.fixture
def known_engine(monkeypatch):
    """Trabajos conocidos: TME=7, operación 8+3, agrupados de tres."""
    # * Crea count trabajos con TME=7 y resultado esperado 11, sin depender del azar.
    # ? Devuelve un motor nuevo; count vale 3 si la prueba no indica otra cantidad.
    def build(count=3):
        processes = [Process(i, (i - 1) // 3 + 1, "+", 8, 3, 7) for i in range(1, count + 1)]
        # ? La lambda devuelve los trabajos conocidos e ignora cantidad y semilla recibidas.
        # ! monkeypatch sustituye el generador solo durante la prueba y luego lo restaura.
        monkeypatch.setattr("simulation.engine.generate_processes", lambda n, seed: processes)
        return SimulationEngine.create(count)
    return build
