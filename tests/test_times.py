from dataclasses import asdict

import pytest

from simulation.models import Process


def advance(engine, seconds):
    for _ in range(seconds):
        engine.tick()


def times(process):
    return (
        process.llegada, process.primera_atencion, process.finalizacion,
        process.retorno, process.respuesta, process.espera,
        process.ejecutado, process.bloqueado,
    )


def test_unknown_times_and_zero_are_distinct():
    process = Process(1, 1, "+", 8, 3, 7)
    assert times(process) == (None, None, None, None, None, 0, 0, 0)
    process.llegada = 0
    assert process.respuesta is None
    assert process.retorno is None
    process.primera_atencion = 0
    process.finalizacion = 0
    assert process.respuesta == process.retorno == 0


def test_fcfs_known_times_exclude_time_in_new(known_engine):
    engine = known_engine(4)
    processes = [engine._current, *engine._queue, *engine._new]
    assert times(processes[0]) == (0, 0, None, None, 0, 0, 0, 0)
    assert times(processes[1]) == (0, None, None, None, None, 0, 0, 0)
    assert times(processes[3]) == (None, None, None, None, None, 0, 0, 0)
    advance(engine, 7)
    assert times(processes[3]) == (7, None, None, None, None, 0, 0, 0)
    advance(engine, 21)
    assert [times(p) for p in processes] == [
        (0, 0, 7, 7, 0, 0, 7, 0),
        (0, 7, 14, 14, 7, 7, 7, 0),
        (0, 14, 21, 21, 14, 14, 7, 0),
        (7, 21, 28, 21, 14, 14, 7, 0),
    ]
    assert all(p.retorno == p.espera + p.ejecutado + p.bloqueado for p in processes)


def test_wait_after_unblocking_and_first_attention_not_reset(known_engine):
    engine = known_engine(3)
    first, second, third = engine._current, *engine._queue
    advance(engine, 2)
    engine.interrupt()
    advance(engine, 9)
    assert times(first) == (0, 0, None, None, 0, 0, 2, 9)
    assert [p.id for p in engine._queue] == [1]
    advance(engine, 5)
    assert engine._current is first
    assert times(first) == (0, 0, None, None, 0, 5, 2, 9)
    advance(engine, 5)
    assert [times(p) for p in (first, second, third)] == [
        (0, 0, 21, 21, 0, 5, 7, 9),
        (0, 2, 9, 9, 2, 2, 7, 0),
        (0, 9, 16, 16, 9, 9, 7, 0),
    ]


def test_repeated_blocks_idle_cpu_and_error_keep_real_service(known_engine):
    engine = known_engine(1)
    process = engine._current
    advance(engine, 2)
    engine.interrupt()
    advance(engine, 9)
    advance(engine, 1)
    engine.interrupt()
    advance(engine, 9)
    engine.fail()
    assert times(process) == (0, 0, 21, 21, 0, 0, 3, 18)
    assert process.estado == "error"
    assert process.ejecutado < process.tme
    assert process.retorno == process.espera + process.ejecutado + process.bloqueado


def test_error_before_first_tick_records_zero_instants(known_engine):
    engine = known_engine(4)
    process = engine._current
    new = engine._new[0]
    engine.fail()
    assert times(process) == (0, 0, 0, 0, 0, 0, 0, 0)
    assert new.llegada == 0
    assert new.primera_atencion is None


@pytest.mark.parametrize("idle_cpu", [False, True])
def test_pause_freezes_all_process_data_and_derived_times(known_engine, idle_cpu):
    engine = known_engine(4)
    processes = [engine._current, *engine._queue, *engine._new]
    advance(engine, 2)
    engine.interrupt()
    if idle_cpu:
        engine.interrupt()
        engine.interrupt()
    advance(engine, 3)
    engine.pause()
    before = [(asdict(p), times(p)) for p in processes]
    clock = engine.clock
    advance(engine, 30)
    assert engine.clock == clock
    assert [(asdict(p), times(p)) for p in processes] == before
    engine.resume()
    advance(engine, 1)
    assert engine.clock == clock + 1
    assert processes[0].bloqueado == 4


def test_snapshot_exposes_times_and_reads_do_not_change_them(known_engine):
    engine = known_engine(4)
    processes = [engine._current, *engine._queue, *engine._new]
    engine.tick()
    engine.interrupt()
    engine.tick()
    engine.fail()
    before = [(asdict(p), times(p)) for p in processes]
    snapshot = engine.snapshot()
    assert set(snapshot) == {
        "estado", "reloj", "nuevos", "bloqueados", "memoria_ocupada",
        "total_trabajos", "en_ejecucion", "en_espera", "terminados",
    }
    visible = [snapshot["en_ejecucion"], *snapshot["en_espera"],
               *snapshot["bloqueados"], *snapshot["nuevos"], *snapshot["terminados"]]
    for process in visible:
        assert set(process) == {
            "id", "estado", "operacion", "operando_a", "operando_b",
            "tme", "ejecutado", "restante", "resultado",
            "llegada", "primera_atencion", "finalizacion", "retorno", "respuesta",
            "espera", "bloqueado", "inicio_bloqueo",
        } | ({"bloqueo_transcurrido", "bloqueo_restante"} if process["estado"] == "blocked" else set())
    assert snapshot["bloqueados"][0]["bloqueo_transcurrido"] == 1
    assert snapshot["bloqueados"][0]["bloqueo_restante"] == 8
    for _ in range(5):
        assert engine.snapshot() == snapshot
    assert [(asdict(p), times(p)) for p in processes] == before
