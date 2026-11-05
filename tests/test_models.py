from typing import get_args

import pytest

from simulation.generator import generate_processes
from simulation.models import Process, ProcessStatus


def test_generated_processes_keep_legacy_defaults_and_unset_fcfs_times():
    for process in generate_processes(4, seed=123):
        assert process.estado == "ready"
        assert process.ejecutado == 0
        assert process.llegada is None
        assert process.primera_atencion is None
        assert process.finalizacion is None
        assert process.inicio_bloqueo is None
        assert process.espera == 0
        assert process.bloqueado == 0


@pytest.mark.parametrize("status", ["new", "blocked"])
def test_fcfs_states_preserve_service_and_remaining_time(status):
    assert status in get_args(ProcessStatus)
    process = Process(1, 1, "+", 8, 3, 7, ejecutado=2, estado=status)
    assert process.ejecutado == 2
    assert process.restante == 5


def test_fcfs_data_distinguishes_time_zero_and_preserves_snapshot_contract():
    process = Process(
        1, 1, "+", 8, 3, 7, ejecutado=2,
        llegada=0, primera_atencion=0, inicio_bloqueo=2,
        espera=3, bloqueado=10,
    )
    assert process.llegada == process.primera_atencion == 0
    assert process.finalizacion is None
    assert process.inicio_bloqueo == 2
    assert (process.espera, process.bloqueado) == (3, 10)
    assert process.snapshot() == {
        "id": 1, "estado": "ready", "operacion": "+",
        "operando_a": 8, "operando_b": 3, "tme": 7,
        "ejecutado": 2, "restante": 5, "resultado": None,
        "llegada": 0, "primera_atencion": 0, "finalizacion": None,
        "retorno": None, "respuesta": 0, "espera": 3,
        "bloqueado": 10, "inicio_bloqueo": 2,
    }
