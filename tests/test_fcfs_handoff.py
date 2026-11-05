"""Revisión de entrega: invariantes públicas durante secuencias de controles."""

import json
from random import Random

import pytest

from simulation import SimulationEngine, SimulationStateError


def processes(state):
    current = [state["en_ejecucion"]] if state["en_ejecucion"] else []
    return current + state["nuevos"] + state["en_espera"] + state["bloqueados"] + state["terminados"]


def check_state(state, count):
    all_processes = processes(state)
    assert sorted(p["id"] for p in all_processes) == list(range(1, count + 1))
    assert json.loads(json.dumps(state)) == state
    assert "lote_actual" not in state and "lotes_pendientes" not in state
    resident_count = len(state["en_espera"]) + len(state["bloqueados"]) + int(state["en_ejecucion"] is not None)
    assert state["memoria_ocupada"] == resident_count <= 3
    assert not state["nuevos"] or resident_count == 3
    assert (state["estado"] == "completed") == (len(state["terminados"]) == count)
    if state["estado"] == "running" and state["en_ejecucion"] is None:
        assert state["bloqueados"] and not state["en_espera"]
    for queue, status in (("nuevos", "new"), ("en_espera", "ready"), ("bloqueados", "blocked")):
        assert all(p["estado"] == status for p in state[queue])
    if state["en_ejecucion"]:
        assert state["en_ejecucion"]["estado"] == "running"
    for p in all_processes:
        assert "lote" not in p
        assert 0 <= p["ejecutado"] <= p["tme"]
        assert p["espera"] >= 0 and p["bloqueado"] >= 0
        if p["estado"] == "new":
            assert p["llegada"] is p["primera_atencion"] is p["finalizacion"] is None
            assert p["respuesta"] is p["retorno"] is None
            assert p["ejecutado"] == p["espera"] == p["bloqueado"] == 0
            continue
        assert 0 <= p["llegada"] <= state["reloj"]
        end = p["finalizacion"] if p["finalizacion"] is not None else state["reloj"]
        assert end - p["llegada"] == p["ejecutado"] + p["espera"] + p["bloqueado"]
        if p["primera_atencion"] is None:
            assert p["respuesta"] is None and p["estado"] == "ready"
        else:
            assert p["llegada"] <= p["primera_atencion"] <= end
            assert p["respuesta"] == p["primera_atencion"] - p["llegada"]
        if p["finalizacion"] is None:
            assert p["retorno"] is None
            assert p["restante"] == p["tme"] - p["ejecutado"]
        else:
            assert p["estado"] in ("finished", "error")
            assert p["retorno"] == end - p["llegada"]
            assert p["restante"] == 0
            if p["estado"] == "finished":
                assert p["ejecutado"] == p["tme"]
            else:
                assert p["resultado"] is None
        if p["estado"] == "blocked":
            assert p["bloqueo_transcurrido"] == state["reloj"] - p["inicio_bloqueo"]
            assert 0 <= p["bloqueo_transcurrido"] < 9
            assert p["bloqueo_restante"] == 9 - p["bloqueo_transcurrido"]
        else:
            assert p["inicio_bloqueo"] is None


@pytest.mark.parametrize("count", [1, 2, 3, 4, 7])
@pytest.mark.parametrize("seed", [0, 7, 123])
def test_mixed_controls_preserve_time_partition_and_finish(count, seed):
    engine = SimulationEngine.create(count, seed=seed)
    rng = Random(seed)
    first_attention = {}
    idle_ticks = 0
    for step in range(600):
        before = engine.snapshot()
        check_state(before, count)
        if before["estado"] == "completed":
            break
        if before["estado"] == "paused":
            action = rng.choice(("tick", "pause", "resume", "interrupt", "fail"))
        else:
            action = rng.choice(("tick", "tick", "tick", "interrupt", "fail", "pause", "resume"))
        # Tras explorar controles, finalizar sin nuevas interrupciones ni pausas.
        if step >= 300:
            action = "resume" if before["estado"] == "paused" else "tick"
        rejected = action in ("interrupt", "fail") and (
            before["estado"] == "paused" or before["en_ejecucion"] is None
        )
        if rejected:
            with pytest.raises(SimulationStateError):
                getattr(engine, action)()
            assert engine.snapshot() == before
        else:
            getattr(engine, action)()
        after = engine.snapshot()
        if action == "tick" and before["estado"] == "running":
            idle_ticks += int(before["en_ejecucion"] is None)
            assert after["reloj"] == before["reloj"] + 1
        else:
            assert after["reloj"] == before["reloj"]
        for p in processes(after):
            if p["primera_atencion"] is not None:
                assert first_attention.setdefault(p["id"], p["primera_atencion"]) == p["primera_atencion"]
        assert after["reloj"] == sum(p["ejecutado"] for p in processes(after)) + idle_ticks
        assert engine.snapshot() == after
    else:
        pytest.fail("La simulación no terminó tras dejar de interrumpir y pausar")
    frozen = engine.snapshot()
    engine.tick()
    assert engine.snapshot() == frozen
    for action in (engine.interrupt, engine.fail, engine.pause, engine.resume):
        with pytest.raises(SimulationStateError):
            action()
        assert engine.snapshot() == frozen
