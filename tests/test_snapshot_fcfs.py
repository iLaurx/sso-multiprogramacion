import json
from dataclasses import asdict
from pathlib import Path
import re

from simulation import SimulationEngine


def test_public_snapshot_blocking_pause_and_repeated_block(known_engine):
    engine = known_engine(1)
    process = engine._current
    engine.tick()
    engine.interrupt()
    assert engine.snapshot()["bloqueados"][0]["bloqueo_restante"] == 10
    for _ in range(9):
        engine.tick()
    state = engine.snapshot()
    blocked = state["bloqueados"][0]
    assert (blocked["bloqueado"], blocked["bloqueo_transcurrido"], blocked["bloqueo_restante"]) == (9, 9, 1)
    engine.pause()
    frozen = engine.snapshot()
    internal = asdict(process)
    for _ in range(12):
        engine.tick()
        assert engine.snapshot() == frozen
    assert asdict(process) == internal
    engine.resume()
    engine.tick()
    engine.interrupt()
    state = engine.snapshot()
    assert state["bloqueados"][0]["bloqueado"] == 10
    assert state["bloqueados"][0]["bloqueo_transcurrido"] == 0
    assert state["bloqueados"][0]["bloqueo_restante"] == 10
    state["bloqueados"][0]["bloqueado"] = 999
    assert engine.snapshot()["bloqueados"][0]["bloqueado"] == 10
    assert json.loads(json.dumps(engine.snapshot())) == engine.snapshot()


def test_public_snapshot_known_completion_times(known_engine):
    engine = known_engine(4)
    for _ in range(28):
        engine.tick()
    state = engine.snapshot()
    assert state["memoria_ocupada"] == 0
    assert state["en_ejecucion"] is None
    assert state["nuevos"] == state["en_espera"] == state["bloqueados"] == []
    assert "lote_actual" not in state and "lotes_pendientes" not in state
    for process in state["terminados"]:
        assert "lote" not in process
        assert process["retorno"] == process["espera"] + process["ejecutado"] + process["bloqueado"]
    fourth = state["terminados"][3]
    assert (fourth["llegada"], fourth["finalizacion"], fourth["retorno"], fourth["respuesta"]) == (7, 28, 21, 14)


def test_documented_json_examples_match_real_engine():
    guide = Path(__file__).resolve().parents[1] / "docs" / "cambios-backend-fcfs.md"
    examples = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", guide.read_text(encoding="utf-8"), re.S)]
    engine = SimulationEngine.create(4, seed=123)
    expected = [engine.snapshot()]
    engine = SimulationEngine.create(1, seed=123)
    engine.tick()
    engine.tick()
    engine.interrupt()
    for _ in range(3):
        engine.tick()
    expected.append(engine.snapshot())
    for _ in range(7):
        engine.tick()
    engine.fail()
    expected.append(engine.snapshot())
    engine = SimulationEngine.create(1, seed=123)
    while engine.status != "completed":
        engine.tick()
    expected.append(engine.snapshot())
    assert examples == expected
