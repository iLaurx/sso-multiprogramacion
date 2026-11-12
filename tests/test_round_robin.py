"""Orden de turnos y coincidencias de Round Robin."""

import pytest
import json
from pathlib import Path
import re

from simulation import SimulationEngine
from test_fcfs_handoff import check_state


def test_round_robin_rotates_and_keeps_service_across_turns(known_engine):
    engine = known_engine(3, quantum=3)
    for _ in range(3):
        engine.tick()
    assert engine._current.id == 2
    assert [p.id for p in engine._queue] == [3, 1]
    for _ in range(6):
        engine.tick()
    assert engine._current.id == 1
    assert engine._current.ejecutado == 3
    assert engine._turn_elapsed == 0
    for _ in range(12):
        engine.tick()
    assert [p.id for p in engine._finished] == [1, 2, 3]
    assert engine.status == "completed"


def test_single_process_restarts_turn_and_finishes(known_engine):
    engine = known_engine(1, quantum=3)
    for _ in range(3):
        engine.tick()
    assert engine._current.id == 1
    assert engine._current.ejecutado == 3
    assert engine._turn_elapsed == 0
    for _ in range(4):
        engine.tick()
    assert engine.status == "completed"
    assert engine._finished[0].ejecutado == 7


def test_completion_takes_precedence_over_quantum(known_engine):
    engine = known_engine(2, quantum=7)
    for _ in range(7):
        engine.tick()
    assert [p.id for p in engine._finished] == [1]
    assert engine._current.id == 2
    assert not engine._queue


def test_unblock_precedes_expired_turn_at_same_instant(known_engine):
    engine = known_engine(3, quantum=9)
    engine.interrupt()
    engine._current.tme = 12
    for _ in range(9):
        engine.tick()
    assert engine._current.id == 3
    assert [p.id for p in engine._queue] == [1, 2]
    assert engine._turn_elapsed == 0


def test_block_idle_pause_resume_and_new_turn_keep_times(known_engine):
    engine = known_engine(1, quantum=3)
    engine.tick()
    engine.tick()
    engine.interrupt()
    assert engine._current is None and engine._turn_elapsed == 0
    for _ in range(4):
        engine.tick()
    engine.pause()
    before = engine.snapshot()
    for _ in range(5):
        engine.tick()
    assert engine.snapshot() == before
    engine.resume()
    for _ in range(5):
        engine.tick()
    assert engine._current.id == 1
    assert engine._turn_elapsed == 0
    assert (engine._current.ejecutado, engine._current.bloqueado) == (2, 9)
    while engine.status != "completed":
        engine.tick()
    process = engine._finished[0]
    assert (process.llegada, process.primera_atencion, process.finalizacion) == (0, 0, 16)
    assert (process.retorno, process.respuesta, process.espera, process.ejecutado) == (16, 0, 0, 7)


def test_error_closes_turn_and_admits_new_process(known_engine):
    engine = known_engine(4, quantum=3)
    engine.tick()
    engine.fail()
    failed = engine._finished[0]
    assert (failed.estado, failed.ejecutado, failed.finalizacion) == ("error", 1, 1)
    assert engine._current.id == 2 and engine._turn_elapsed == 0
    assert [p.id for p in engine._queue] == [3, 4]
    assert engine.memoria_ocupada == 3


def test_adding_at_full_memory_preserves_fifo_and_round_robin_times(known_engine):
    engine = known_engine(4, quantum=2)
    added = engine.add_process()
    assert added["id"] == 5 and added["estado"] == "new"
    assert [p.id for p in engine._new] == [4, 5]
    for _ in range(100):
        check_state(engine.snapshot(), 5)
        if engine.status == "completed":
            break
        engine.tick()
    assert engine.status == "completed"
    assert [p.id for p in engine._finished] == [1, 2, 3, 4, 5]
    assert all(p.retorno == p.espera + p.ejecutado + p.bloqueado for p in engine._finished)


@pytest.mark.parametrize("quantum", [1, 2, 5, 20])
def test_controls_and_timing_invariants_with_different_quantums(known_engine, quantum):
    engine = known_engine(4, quantum=quantum)
    engine.tick()
    engine.interrupt()
    for _ in range(4):
        engine.tick()
    engine.fail()
    engine.pause()
    before = engine.snapshot()
    engine.tick()
    assert engine.snapshot() == before
    engine.resume()
    for _ in range(100):
        check_state(engine.snapshot(), 4)
        if engine.status == "completed":
            break
        engine.tick()
    assert engine.status == "completed"


def test_snapshot_turn_progress_pause_idle_and_completion(known_engine):
    engine = known_engine(1, quantum=3)
    assert (engine.snapshot()["quantum"], engine.snapshot()["tiempo_turno"]) == (3, 0)
    engine.tick()
    assert engine.snapshot()["tiempo_turno"] == 1
    frozen = engine.snapshot()
    assert engine.snapshot() == frozen
    engine.pause()
    engine.tick()
    assert engine.snapshot()["tiempo_turno"] == 1
    engine.resume()
    engine.interrupt()
    assert engine.snapshot()["tiempo_turno"] is None
    for _ in range(9):
        engine.tick()
    assert engine.snapshot()["tiempo_turno"] == 0
    while engine.status != "completed":
        engine.tick()
    assert engine.snapshot()["tiempo_turno"] is None


def test_round_robin_delivery_examples_match_motor():
    guide = Path(__file__).resolve().parents[1] / "docs" / "entrega-motor-round-robin.md"
    examples = [json.loads(block) for block in re.findall(
        r"```json\n(.*?)\n```", guide.read_text(encoding="utf-8"), re.S
    )]
    engine = SimulationEngine.create(2, seed=123, quantum=3)
    expected = [engine.snapshot()]
    for _ in range(3):
        engine.tick()
    expected.append(engine.snapshot())
    engine.pause()
    expected.append(engine.snapshot())
    engine = SimulationEngine.create(1, seed=123, quantum=3)
    engine.tick()
    engine.interrupt()
    expected.append(engine.snapshot())
    assert examples == expected
