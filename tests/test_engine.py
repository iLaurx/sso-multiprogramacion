import json
import random

import pytest

from simulation import SimulationEngine, SimulationStateError
from simulation.generator import generate_processes
from simulation.models import calculate


# * Comprueba IDs consecutivos, tamaños de lote y primer despacho con reloj cero.
# ? parametrize ejecuta la misma prueba con las cantidades y tamaños esperados indicados.
@pytest.mark.parametrize("count, sizes", [(1, [1]), (3, [3]), (4, [3, 1]), (7, [3, 3, 1])])
def test_generation_and_initial_state(count, sizes):
    processes = generate_processes(count, seed=123)
    assert [p.id for p in processes] == list(range(1, count + 1))
    assert [sum(p.lote == batch for p in processes) for batch in range(1, len(sizes) + 1)] == sizes
    state = SimulationEngine.create(count, seed=123).snapshot()
    assert state["estado"] == "running"
    assert state["reloj"] == 0
    assert state["lote_actual"] == 1
    assert state["lotes_pendientes"] == len(sizes) - 1
    assert state["en_ejecucion"]["id"] == 1
    assert [p["id"] for p in state["en_espera"]] == list(range(2, min(count, 3) + 1))
    assert state["terminados"] == []


# * Verifica que cantidades no positivas o de otro tipo sean rechazadas.
# ? pytest.raises exige que la llamada genere ValueError con el mensaje indicado.
@pytest.mark.parametrize("invalid", [0, -1, True, False, 2.5, 2.0, "3", None])
def test_invalid_quantity(invalid):
    with pytest.raises(ValueError, match="entero positivo"):
        SimulationEngine.create(invalid)


# * Verifica que una semilla booleana, decimal o de texto no se acepte como entero.
@pytest.mark.parametrize("invalid", [True, 1.5, "123"])
def test_invalid_seed(invalid):
    with pytest.raises(ValueError, match="semilla"):
        SimulationEngine.create(1, seed=invalid)


# * Comprueba rangos, operaciones, divisores válidos y repetibilidad con la misma semilla.
# ? Compara el estado aleatorio global antes y después para detectar cambios ajenos al motor.
def test_random_generation_is_valid_and_local():
    before = random.getstate()
    processes = generate_processes(2000, seed=123)
    assert random.getstate() == before
    assert {p.operacion for p in processes} == {"+", "-", "*", "/", "%"}
    assert {p.tme for p in processes} == set(range(7, 19))
    for p in processes:
        assert -99 <= p.operando_a <= 99
        assert -99 <= p.operando_b <= 99
        if p.operacion in ("/", "%"):
            assert p.operando_b != 0
    assert processes == generate_processes(2000, seed=123)


# * Compara cada operación con un resultado conocido, incluyendo residuo con negativos.
# ? Cada conjunto de parámetros aporta símbolo, operandos y resultado esperado.
@pytest.mark.parametrize("operation,a,b,expected", [
    ("+", 8, 3, 11), ("-", 8, 3, 5), ("*", -8, 3, -24),
    ("/", 8, 3, 8 / 3), ("%", -8, 3, 1), ("%", 8, -3, -1),
])
def test_operation_results(operation, a, b, expected):
    assert calculate(operation, a, b) == expected


# * Ejecuta dos ticks, interrumpe y comprueba la nueva cola [3,1] mientras ejecuta el ID 2.
# ? Después termina 2 y 3 para verificar que el ID 1 retoma sus dos segundos acumulados.
def test_tick_and_interrupt_preserve_time_and_queue(known_engine):
    engine = known_engine()
    engine.tick()
    engine.tick()
    state = engine.snapshot()
    assert state["en_ejecucion"]["ejecutado"] == 2
    assert state["en_ejecucion"]["restante"] == 5
    engine.interrupt()
    state = engine.snapshot()
    assert state["reloj"] == 2
    assert state["en_ejecucion"]["id"] == 2
    assert [p["id"] for p in state["en_espera"]] == [3, 1]
    assert state["en_espera"][-1]["ejecutado"] == 2
    assert state["en_espera"][-1]["restante"] == 5
    for _ in range(14):
        engine.tick()
    assert engine.snapshot()["en_ejecucion"]["id"] == 1
    assert engine.snapshot()["en_ejecucion"]["ejecutado"] == 2
    for _ in range(5):
        engine.tick()
    assert engine.snapshot()["reloj"] == 21
    assert [p["id"] for p in engine.snapshot()["terminados"]] == [2, 3, 1]


# * Comprueba que interrumpir al único proceso lo vuelve a despachar sin perderlo ni avanzar.
# ? Los snapshots antes y después deben ser iguales, incluido el tiempo ejecutado.
def test_interrupt_single_live_process(known_engine):
    engine = known_engine(1)
    engine.tick()
    before = engine.snapshot()
    engine.interrupt()
    assert engine.snapshot() == before


# * Comprueba el error tras dos ticks y el avance entre lotes al terminar los demás por E.
# ! El error conserva ejecutado=2 y deja restante=0; las acciones no incrementan el reloj.
def test_error_keeps_actual_time_and_moves_to_next(known_engine):
    engine = known_engine(4)
    engine.tick()
    engine.tick()
    engine.fail()
    state = engine.snapshot()
    p = state["terminados"][0]
    assert (p["estado"], p["resultado"], p["ejecutado"], p["restante"]) == ("error", None, 2, 0)
    assert state["reloj"] == 2
    assert state["en_ejecucion"]["id"] == 2
    assert state["lote_actual"] == 1
    engine.fail()
    engine.fail()
    state = engine.snapshot()
    assert state["lote_actual"] == 2
    assert state["lotes_pendientes"] == 0
    assert state["en_ejecucion"]["id"] == 4
    engine.fail()
    assert engine.snapshot()["estado"] == "completed"
    assert engine.snapshot()["reloj"] == 2


# * Verifica que P congela el estado, rechaza I/E y que C permite volver a ejecutar ticks.
# ? También comprueba que repetir P o C en su estado correspondiente no cambia nada.
def test_pause_resume_and_rejected_actions(known_engine):
    engine = known_engine()
    engine.tick()
    engine.pause()
    before = engine.snapshot()
    engine.pause()
    for _ in range(10):
        engine.tick()
    for action in (engine.interrupt, engine.fail):
        with pytest.raises(SimulationStateError, match="pausada"):
            action()
    assert engine.snapshot() == before
    engine.resume()
    before = engine.snapshot()
    engine.resume()
    assert engine.snapshot() == before
    engine.tick()
    assert engine.snapshot()["reloj"] == 2


# * Ejecuta todos los trabajos conocidos y comprueba tiempos, orden, lotes y cierre.
# ? Con TME=7, cada siete ticks termina un proceso y se despacha el siguiente.
# ! Después del cierre, tick no cambia nada y los controles generan SimulationStateError.
@pytest.mark.parametrize("count", [1, 3, 4, 7])
def test_normal_completion_and_batch_transition(known_engine, count):
    engine = known_engine(count)
    for elapsed in range(1, count * 7 + 1):
        engine.tick()
        state = engine.snapshot()
        assert state["reloj"] == elapsed
        assert len(state["terminados"]) == elapsed // 7
        if elapsed < count * 7:
            current = state["en_ejecucion"]
            assert current["id"] == elapsed // 7 + 1
            assert state["lote_actual"] == current["lote"]
            assert all(p["lote"] == current["lote"] for p in state["en_espera"])
    state = engine.snapshot()
    assert state["estado"] == "completed"
    assert state["lote_actual"] is None
    assert state["lotes_pendientes"] == 0
    assert state["en_ejecucion"] is None
    assert state["en_espera"] == []
    assert [p["id"] for p in state["terminados"]] == list(range(1, count + 1))
    assert all(p["resultado"] == 11 and p["restante"] == 0 for p in state["terminados"])
    engine.tick()
    for action in (engine.interrupt, engine.fail, engine.pause, engine.resume):
        with pytest.raises(SimulationStateError):
            action()
        assert engine.snapshot() == state


# * Comprueba que el snapshot se convierte a JSON y que leerlo no modifica el motor.
# ? Al cambiar una copia, el siguiente snapshot debe conservar los datos originales.
def test_snapshot_is_json_safe_independent_and_read_only(known_engine):
    engine = known_engine()
    expected = engine.snapshot()
    assert json.loads(json.dumps(expected)) == expected
    for _ in range(5):
        assert engine.snapshot() == expected
    changed = engine.snapshot()
    changed["en_ejecucion"]["ejecutado"] = 999
    changed["en_espera"].clear()
    changed["terminados"].append({"id": 999})
    assert engine.snapshot() == expected


# * Mezcla ticks, interrupciones y errores para revisar las reglas después de cada transición.
# ? La semilla fija tanto los trabajos como la secuencia de acciones para reproducir fallos.
# ! Comprueba IDs sin duplicados, tiempos válidos, cola del lote activo y resultados finales.
@pytest.mark.parametrize("seed", range(10))
def test_mixed_actions_preserve_invariants_and_results(seed):
    engine = SimulationEngine.create(7, seed=seed)
    rng = random.Random(seed)
    while engine.status != "completed":
        # ? getattr obtiene el método por nombre y () lo ejecuta; tick tiene doble probabilidad.
        getattr(engine, rng.choice(("tick", "tick", "interrupt", "fail")))()
        state = engine.snapshot()
        live = ([state["en_ejecucion"]] if state["en_ejecucion"] else []) + state["en_espera"]
        visible = live + state["terminados"]
        assert len({p["id"] for p in visible}) == len(visible)
        assert all(0 <= p["ejecutado"] <= p["tme"] for p in visible)
        assert state["reloj"] == sum(p["ejecutado"] for p in visible)
        assert all(p["restante"] == p["tme"] - p["ejecutado"] for p in live)
        assert all(p["estado"] == "ready" and p["lote"] == state["lote_actual"] for p in state["en_espera"])
        for p in state["terminados"]:
            assert p["restante"] == 0
            if p["estado"] == "finished":
                assert p["resultado"] == calculate(p["operacion"], p["operando_a"], p["operando_b"])
            else:
                assert p["estado"] == "error" and p["resultado"] is None
    assert len(engine.snapshot()["terminados"]) == 7
