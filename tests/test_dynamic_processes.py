"""Actividad 8: altas, consulta completa y cierre con población variable."""

import json
import random

import pytest

from simulation import SimulationEngine, SimulationStateError
from simulation.generator import generate_processes
from test_fcfs_handoff import check_state


def test_generation_continues_private_random_sequence():
    before = random.getstate()
    engine = SimulationEngine.create(2, seed=123)
    added = [engine.add_process() for _ in range(2000)]
    expected = generate_processes(2002, seed=123)[2:]
    for actual, process in zip(added, expected):
        for key in ("id", "operacion", "operando_a", "operando_b", "tme"):
            assert actual[key] == process.snapshot()[key]
        assert 7 <= actual["tme"] <= 18
        assert -99 <= actual["operando_a"] <= 99
        assert -99 <= actual["operando_b"] <= 99
        if actual["operacion"] in ("/", "%"):
            assert actual["operando_b"] != 0
    assert random.getstate() == before
    assert engine.snapshot()["total_trabajos"] == 2002
    assert engine.memoria_ocupada == 3


def test_add_with_space_keeps_cpu_and_uses_current_admission_time():
    engine = SimulationEngine.create(1, seed=123)
    engine.tick()
    current = engine.snapshot()["en_ejecucion"]
    added = engine.add_process()
    assert added["id"] == 2 and added["estado"] == "ready"
    assert added["llegada"] == 1 and added["primera_atencion"] is None
    assert added["ejecutado"] == added["espera"] == 0
    assert engine.clock == 1
    assert engine.snapshot()["en_ejecucion"] == current
    added["id"] = -1
    assert engine.processes_snapshot()[1]["id"] == 2


def test_new_queue_keeps_fifo_and_ids_after_finished_processes(known_engine):
    engine = known_engine(4)
    engine.tick()
    added = engine.add_process()
    assert added["id"] == 5 and added["estado"] == "new"
    assert added["llegada"] is added["respuesta"] is added["retorno"] is None
    assert [p["id"] for p in engine.snapshot()["nuevos"]] == [4, 5]
    engine.fail()
    assert [p["id"] for p in engine.snapshot()["en_espera"]] == [3, 4]
    engine.tick()
    engine.fail()
    state = engine.snapshot()
    assert [p["id"] for p in state["en_espera"]] == [4, 5]
    assert state["en_espera"][1]["llegada"] == 2
    assert state["en_espera"][1]["espera"] == 0
    assert engine.add_process()["id"] == 6
    assert engine.total_trabajos == 6


@pytest.mark.parametrize("count", [1, 3])
def test_add_with_idle_cpu_and_blocked_residents(known_engine, count):
    engine = known_engine(count)
    for _ in range(count):
        engine.interrupt()
    assert engine.snapshot()["en_ejecucion"] is None
    added = engine.add_process()
    assert engine.status == "running"
    assert added["estado"] == ("running" if count == 1 else "new")
    assert engine.memoria_ocupada == min(3, count + 1)
    assert len(engine.snapshot()["bloqueados"]) == count
    if count == 3:
        for _ in range(9):
            engine.tick()
        assert [p["id"] for p in engine.snapshot()["nuevos"]] == [4]
        engine.fail()
        assert engine.snapshot()["en_espera"][-1]["id"] == 4


@pytest.mark.parametrize("status", ["paused", "completed"])
def test_rejected_add_does_not_change_state_or_consume_randomness(status):
    engine = SimulationEngine.create(1, seed=7)
    if status == "paused":
        engine.pause()
    else:
        engine.fail()
    before = engine.snapshot()
    random_state = engine._rng.getstate()
    with pytest.raises(SimulationStateError):
        engine.add_process()
    assert engine.snapshot() == before
    assert engine._rng.getstate() == random_state
    if status == "paused":
        engine.resume()
        assert engine.add_process()["id"] == 2


def test_all_processes_query_preserves_every_state_and_returns_copies(known_engine):
    engine = known_engine(5)
    engine.fail()
    engine.interrupt()
    engine.tick()
    engine.add_process()
    before = engine.snapshot()
    rows = engine.processes_snapshot()
    assert [p["id"] for p in rows] == list(range(1, 7))
    assert {p["estado"] for p in rows} == {"error", "blocked", "running", "ready", "new"}
    assert rows[1]["bloqueo_restante"] == 8
    assert json.loads(json.dumps(rows)) == rows
    rows[0]["ejecutado"] = 999
    rows.clear()
    assert engine.snapshot() == before


@pytest.mark.parametrize("seed", range(5))
def test_dynamic_controls_preserve_times_and_finish_every_process(seed):
    engine = SimulationEngine.create(4, seed=seed)
    rng = random.Random(seed)
    count = 4
    idle = 0
    for _ in range(180):
        if engine.status == "completed":
            break
        action = rng.choice(("tick", "tick", "add_process", "interrupt", "fail"))
        if action in ("interrupt", "fail") and engine.snapshot()["en_ejecucion"] is None:
            action = "tick"
        if action == "tick" and engine.snapshot()["en_ejecucion"] is None:
            idle += 1
        getattr(engine, action)()
        count += int(action == "add_process")
        check_state(engine.snapshot(), count)
        assert engine.clock == sum(p["ejecutado"] for p in engine.processes_snapshot()) + idle
    for _ in range(count * 18 + 9):
        if engine.status == "completed":
            break
        engine.tick()
        check_state(engine.snapshot(), count)
    assert engine.status == "completed"
    assert len(engine.processes_snapshot()) == len(engine.snapshot()["terminados"]) == count
    assert engine.total_trabajos == count
    before = engine.snapshot()
    engine.tick()
    assert engine.snapshot() == before
