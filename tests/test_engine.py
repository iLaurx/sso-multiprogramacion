import json
import random

import pytest

from simulation import SimulationEngine, SimulationStateError
from simulation.generator import generate_processes
from simulation.models import calculate


# * Comprueba IDs consecutivos, admisión inicial y primer despacho con reloj cero.
# ? parametrize ejecuta la prueba con distintas cantidades de procesos.
@pytest.mark.parametrize("count", [1, 3, 4, 7])
def test_generation_and_initial_state(count):
    processes = generate_processes(count, seed=123)
    assert [p.id for p in processes] == list(range(1, count + 1))
    state = SimulationEngine.create(count, seed=123).snapshot()
    assert state["estado"] == "running"
    assert state["reloj"] == 0
    assert state["memoria_ocupada"] == min(count, 3)
    assert [p["id"] for p in state["nuevos"]] == list(range(4, count + 1))
    assert all(p["estado"] == "new" for p in state["nuevos"])
    assert state["bloqueados"] == []
    assert "lote_actual" not in state
    assert "lotes_pendientes" not in state
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


# * Ejecuta dos ticks, bloquea al ID 1 y despacha el ID 2 con el ID 3 en listos.
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
    assert [p["id"] for p in state["en_espera"]] == [3]
    assert [p["id"] for p in state["bloqueados"]] == [1]
    assert state["bloqueados"][0]["ejecutado"] == 2
    assert state["bloqueados"][0]["restante"] == 5
    for _ in range(14):
        engine.tick()
    assert engine.snapshot()["en_ejecucion"]["id"] == 1
    assert engine.snapshot()["en_ejecucion"]["ejecutado"] == 2
    for _ in range(5):
        engine.tick()
    assert engine.snapshot()["reloj"] == 21
    assert [p["id"] for p in engine.snapshot()["terminados"]] == [2, 3, 1]


# * Un único proceso deja CPU libre nueve segundos y retoma el servicio conservado.
def test_interrupt_single_live_process(known_engine):
    engine = known_engine(1)
    engine.tick()
    before = engine.snapshot()
    engine.interrupt()
    assert engine.clock == before["reloj"]
    assert engine.snapshot()["en_ejecucion"] is None
    assert engine.status == "running"
    for _ in range(8):
        engine.tick()
        assert engine.snapshot()["en_ejecucion"] is None
        assert engine.snapshot()["bloqueados"][0]["ejecutado"] == 1
    engine.tick()
    assert engine.snapshot()["bloqueados"] == []
    assert engine.snapshot()["en_ejecucion"]["ejecutado"] == 1
    for _ in range(6):
        engine.tick()
    assert engine.status == "completed"
    assert engine.clock == 16


# * Comprueba el error tras dos ticks y la admisión inmediata del siguiente nuevo.
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
    assert [p["id"] for p in state["en_espera"]] == [3, 4]
    assert state["nuevos"] == []
    assert state["memoria_ocupada"] == 3
    engine.fail()
    engine.fail()
    state = engine.snapshot()
    assert state["memoria_ocupada"] == 1
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


# * Ejecuta todos los trabajos conocidos y comprueba tiempos, orden FCFS y cierre.
# ? Con TME=7, cada siete ticks termina un proceso y se despacha el siguiente.
# ! Después del cierre, tick no cambia nada y los controles generan SimulationStateError.
@pytest.mark.parametrize("count", [1, 3, 4, 7])
def test_normal_completion_and_continuous_admission(known_engine, count):
    engine = known_engine(count)
    for elapsed in range(1, count * 7 + 1):
        engine.tick()
        state = engine.snapshot()
        assert state["reloj"] == elapsed
        assert len(state["terminados"]) == elapsed // 7
        if elapsed < count * 7:
            current = state["en_ejecucion"]
            assert current["id"] == elapsed // 7 + 1
            assert state["memoria_ocupada"] == min(3, count - elapsed // 7)
            assert [p["id"] for p in state["en_espera"]] == list(
                range(current["id"] + 1, min(count, current["id"] + 2) + 1)
            )
    state = engine.snapshot()
    assert state["estado"] == "completed"
    assert state["memoria_ocupada"] == 0
    assert state["nuevos"] == []
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
    engine = known_engine(7)
    expected = engine.snapshot()
    assert json.loads(json.dumps(expected)) == expected
    for _ in range(5):
        assert engine.snapshot() == expected
    changed = engine.snapshot()
    changed["en_ejecucion"]["ejecutado"] = 999
    changed["en_espera"].clear()
    changed["nuevos"][0]["id"] = 999
    changed["bloqueados"].append({"id": 999})
    changed["terminados"].append({"id": 999})
    assert engine.snapshot() == expected


# * Mezcla ticks, interrupciones y errores para revisar las reglas después de cada transición.
# ? La semilla fija tanto los trabajos como la secuencia de acciones para reproducir fallos.
# ! Comprueba IDs sin duplicados, tiempos válidos, memoria y resultados finales.
@pytest.mark.parametrize("seed", range(10))
def test_mixed_actions_preserve_invariants_and_results(seed):
    engine = SimulationEngine.create(7, seed=seed)
    rng = random.Random(seed)
    idle = 0
    while engine.status != "completed":
        # ? getattr obtiene el método por nombre y () lo ejecuta; tick tiene doble probabilidad.
        action = rng.choice(("tick", "tick", "interrupt", "fail"))
        if engine._current is None:
            action = "tick"
        if action == "tick" and engine._current is None:
            idle += 1
        getattr(engine, action)()
        state = engine.snapshot()
        live = ([state["en_ejecucion"]] if state["en_ejecucion"] else []) + state["en_espera"]
        visible = live + state["terminados"] + state["nuevos"] + state["bloqueados"]
        assert len(visible) == 7
        assert state["memoria_ocupada"] == len(live) + len(state["bloqueados"]) <= 3
        if state["nuevos"]:
            assert state["memoria_ocupada"] == 3
        assert all(p["estado"] == "new" and p["ejecutado"] == 0 for p in state["nuevos"])
        assert len({p["id"] for p in visible}) == len(visible)
        assert all(0 <= p["ejecutado"] <= p["tme"] for p in visible)
        assert state["reloj"] == sum(p["ejecutado"] for p in visible) + idle
        assert all(p["restante"] == p["tme"] - p["ejecutado"] for p in live)
        assert all(p["estado"] == "ready" for p in state["en_espera"])
        for p in state["terminados"]:
            assert p["restante"] == 0
            if p["estado"] == "finished":
                assert p["resultado"] == calculate(p["operacion"], p["operando_a"], p["operando_b"])
            else:
                assert p["estado"] == "error" and p["resultado"] is None
    assert len(engine.snapshot()["terminados"]) == 7


@pytest.mark.parametrize("finish", ["normal", "error"])
def test_admission_does_not_wait_for_other_residents(known_engine, finish):
    engine = known_engine(7)
    pending = list(engine._new)
    assert all(p.llegada is None for p in pending)
    if finish == "normal":
        for _ in range(7):
            engine.tick()
    else:
        engine.tick()
        engine.fail()
    state = engine.snapshot()
    assert state["en_ejecucion"]["id"] == 2
    assert [p["id"] for p in state["en_espera"]] == [3, 4]
    assert [p["id"] for p in state["nuevos"]] == [5, 6, 7]
    assert pending[0].llegada == state["reloj"]
    assert all(p.llegada is None for p in pending[1:])


def test_blocked_residents_keep_memory_and_prevent_completion(known_engine):
    engine = known_engine(4)
    # El bloqueo público conserva el espacio y evita cerrar con CPU libre.
    resident = engine._current
    engine.interrupt()
    assert [p.id for p in engine._new] == [4]
    assert engine.memoria_ocupada == 3
    engine.fail()
    assert [p.id for p in engine._queue] == [4]
    assert engine.memoria_ocupada == 3
    engine.fail()
    engine.fail()
    assert engine.status == "running"
    assert engine._current is None
    assert engine.memoria_ocupada == 1
    before = engine.clock
    engine.tick()
    assert engine.clock == before + 1
    assert resident.ejecutado == 0
    engine.pause()
    state = engine.snapshot()
    engine.tick()
    assert engine.snapshot() == state


def test_fcfs_order_ignores_legacy_batch_metadata(known_engine):
    engine = known_engine(4)
    for process in [engine._current, *engine._queue, *engine._new]:
        process.lote = 99 - process.id
    while engine.status != "completed":
        engine.tick()
    assert [p["id"] for p in engine.snapshot()["terminados"]] == [1, 2, 3, 4]


def test_repeated_blocking_and_pause_at_deadline(known_engine):
    engine = known_engine(1)
    process = engine._current
    engine.tick()
    engine.interrupt()
    assert process.inicio_bloqueo == 1
    for _ in range(8):
        engine.tick()
    assert process.bloqueado == 8
    engine.pause()
    before = engine.snapshot()
    for _ in range(20):
        engine.tick()
    assert engine.snapshot() == before
    assert (process.bloqueado, process.inicio_bloqueo) == (8, 1)
    engine.resume()
    engine.tick()
    assert engine._current is process
    assert (process.ejecutado, process.bloqueado, process.inicio_bloqueo) == (1, 9, None)
    engine.interrupt()
    assert process.inicio_bloqueo == 10
    for _ in range(9):
        engine.tick()
    assert engine._current is process
    assert (process.ejecutado, process.bloqueado, process.inicio_bloqueo) == (1, 18, None)


def test_simultaneous_blocks_return_in_order_without_admitting_new(known_engine):
    engine = known_engine(4)
    for _ in range(3):
        engine.interrupt()
    assert engine._current is None
    assert engine.memoria_ocupada == 3
    assert [p.id for p in engine._new] == [4]
    for action in (engine.interrupt, engine.fail):
        with pytest.raises(SimulationStateError, match="activo"):
            action()
    for _ in range(8):
        engine.tick()
        assert engine._current is None
        assert engine.status == "running"
    engine.tick()
    assert engine._current.id == 1
    assert [p.id for p in engine._queue] == [2, 3]
    assert engine._blocked == []
    assert [p.id for p in engine._new] == [4]
    assert engine._current.ejecutado == 0


def test_unblock_joins_tail_before_new_admission_on_same_tick(known_engine):
    engine = known_engine(5)
    blocked = engine._current
    engine.interrupt()
    engine._current.tme = 9
    for _ in range(8):
        engine.tick()
    assert blocked.estado == "blocked"
    assert blocked.bloqueado == 8
    engine.tick()
    assert engine._current.id == 3
    assert [p.id for p in engine._queue] == [1, 4]
    assert [p.id for p in engine._new] == [5]
    assert blocked.bloqueado == 9
    assert engine.memoria_ocupada == 3


def test_staggered_blocks_progress_while_cpu_executes(known_engine):
    engine = known_engine(3)
    first = engine._current
    engine.interrupt()
    for _ in range(3):
        engine.tick()
    second = engine._current
    engine.interrupt()
    for _ in range(6):
        engine.tick()
    assert (first.bloqueado, second.bloqueado) == (9, 6)
    engine.tick()
    assert engine._current is first
    assert first.ejecutado == 0
    assert second.bloqueado == 7
    for _ in range(3):
        engine.tick()
    assert engine._current is first
    assert [p.id for p in engine._queue] == [2]
    assert engine._blocked == []
    assert (first.ejecutado, second.ejecutado) == (3, 3)
