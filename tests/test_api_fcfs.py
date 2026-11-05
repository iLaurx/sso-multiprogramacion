"""Recorridos FCFS del servicio y HTTP: mismo snapshot, reloj y colas."""
import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.service import SimulationService
from simulation import SimulationEngine


@pytest.mark.parametrize('ending', ['normal', 'error'])
def test_http_preserves_entire_engine_snapshot_and_times(ending):
    app = create_app(auto_clock=False)
    oracle = SimulationEngine.create(4, seed=123)
    with TestClient(app) as client:
        response = client.post('/api/simulations', json={'numero_trabajos': 4, 'seed': 123})
        assert response.status_code == 201
        initial = response.json()
        sid = initial['simulacion_id']
        route = f'/api/simulations/{sid}'

        def check(data):
            assert data == {'simulacion_id': sid, **oracle.snapshot()}
            for _ in range(3):
                assert client.get(route).json() == data
            return data

        def action(name, method):
            method()
            res = client.post(route + '/actions', json={'accion': name})
            assert res.status_code == 200
            return check(res.json())

        def tick(count):
            for _ in range(count):
                client.portal.call(app.state.service.tick_once, sid)
                oracle.tick()
            return check(client.get(route).json())

        check(initial)
        assert initial['nuevos'][0]['llegada'] is None
        tick(2)
        paused_cpu = action('pause', oracle.pause)
        assert tick(3) == paused_cpu
        for name in ('interrupt', 'error'):
            assert client.post(route + '/actions', json={'accion': name}).status_code == 409
            check(paused_cpu)
        action('continue', oracle.resume)
        for _ in range(3):
            blocked = action('interrupt', oracle.interrupt)
        assert blocked['en_ejecucion'] is None
        assert blocked['estado'] == 'running'
        assert blocked['memoria_ocupada'] == 3
        assert [p['id'] for p in blocked['nuevos']] == [4]
        for name in ('interrupt', 'error'):
            assert client.post(route + '/actions', json={'accion': name}).status_code == 409
            check(blocked)
        paused = action('pause', oracle.pause)
        assert tick(15) == paused
        action('pause', oracle.pause)
        action('continue', oracle.resume)
        action('continue', oracle.resume)
        ninth = tick(9)
        assert [p['bloqueo_restante'] for p in ninth['bloqueados']] == [1, 1, 1]
        tenth = tick(1)
        assert tenth['en_ejecucion']['id'] == 1
        assert tenth['en_ejecucion']['ejecutado'] == 2
        assert [p['id'] for p in tenth['en_espera']] == [2, 3]
        if ending == 'error':
            admitted = action('error', oracle.fail)
            assert admitted['terminados'][0]['ejecutado'] == 2
        else:
            admitted = tick(5)
        assert [p['id'] for p in admitted['en_espera']] == [3, 4]
        assert admitted['en_espera'][-1]['llegada'] == admitted['reloj']
        while oracle.status != 'completed':
            tick(1)
        final = check(client.get(route).json())
        assert final['memoria_ocupada'] == 0
        assert final['en_ejecucion'] is None
        assert final['nuevos'] == final['en_espera'] == final['bloqueados'] == []
        for p in final['terminados']:
            assert p['retorno'] == p['espera'] + p['ejecutado'] + p['bloqueado']
        assert tick(3) == final
        for name in ('interrupt', 'error', 'pause', 'continue'):
            assert client.post(route + '/actions', json={'accion': name}).status_code == 409
            check(final)


def test_http_known_times(known_engine):
    known_engine(4)  # Sustituye solo el generador por trabajos 8+3, TME=7.
    app = create_app(auto_clock=False)
    with TestClient(app) as client:
        sid = client.post('/api/simulations', json={'numero_trabajos': 4}).json()['simulacion_id']
        for _ in range(28):
            client.portal.call(app.state.service.tick_once, sid)
        final = client.get(f'/api/simulations/{sid}').json()
        fields = ('llegada', 'primera_atencion', 'finalizacion', 'retorno', 'respuesta', 'espera', 'ejecutado', 'bloqueado')
        assert [tuple(p[k] for k in fields) for p in final['terminados']] == [
            (0, 0, 7, 7, 0, 0, 7, 0), (0, 7, 14, 14, 7, 7, 7, 0),
            (0, 14, 21, 21, 14, 14, 7, 0), (7, 21, 28, 21, 14, 14, 7, 0)]


def test_service_concurrency_isolation_and_snapshot_copies():
    async def run():
        service = SimulationService(auto_clock=False)
        a, b = await asyncio.gather(service.create(4, 123), service.create(1, 123))
        aid, bid = a['simulacion_id'], b['simulacion_id']
        register = service.simulaciones[aid]
        async with register.lock:
            pending = [asyncio.create_task(service.tick_once(aid)),
                       asyncio.create_task(service.apply_action(aid, 'interrupt')),
                       asyncio.create_task(service.get_snapshot(aid))]
            await asyncio.sleep(0)
            assert all(not task.done() for task in pending)
        _, action, snapshot = await asyncio.gather(*pending)
        assert action == snapshot
        assert snapshot['reloj'] == 1
        assert snapshot['bloqueados'][0]['ejecutado'] == 1
        await asyncio.gather(*(service.tick_once(aid) for _ in range(3)),
                             *(service.get_snapshot(aid) for _ in range(10)))
        assert (await service.get_snapshot(aid))['reloj'] == 4
        assert await service.get_snapshot(bid) == b
        snapshot['bloqueados'].clear()
        assert len((await service.get_snapshot(aid))['bloqueados']) == 1
        before = await service.get_snapshot(aid)
        with pytest.raises(ValueError):
            await service.apply_action(aid, 'unknown')
        assert await service.get_snapshot(aid) == before
        assert await service.get_snapshot('missing') is None
        with pytest.raises(KeyError):
            await service.apply_action('missing', 'pause')
        await service.close()
        await service.close()
        assert not service.simulaciones
    asyncio.run(run())


def test_automatic_clock_idle_pause_completion_and_cleanup(monkeypatch):
    async def run():
        real_sleep = asyncio.sleep
        pulses = asyncio.Queue()
        waiting = asyncio.Event()
        async def controlled_sleep(seconds):
            assert seconds == 1
            waiting.set()
            await pulses.get()
            waiting.clear()
        monkeypatch.setattr('backend.service.asyncio.sleep', controlled_sleep)
        service = SimulationService(auto_clock=True)
        initial = await service.create(1, 123)
        sid = initial['simulacion_id']
        task = service.simulaciones[sid].task
        async def pulse():
            await asyncio.wait_for(waiting.wait(), 1)
            pulses.put_nowait(None)
            await real_sleep(0)
        try:
            await service.apply_action(sid, 'interrupt')
            await service.apply_action(sid, 'pause')
            before = await service.get_snapshot(sid)
            await pulse()
            assert await service.get_snapshot(sid) == before
            await service.apply_action(sid, 'continue')
            for _ in range(9):
                await pulse()
            state = await service.get_snapshot(sid)
            assert state['reloj'] == 9 and state['en_ejecucion'] is None
            assert state['bloqueados'][0]['bloqueo_restante'] == 1
            await pulse()
            assert (await service.get_snapshot(sid))['en_ejecucion']['ejecutado'] == 0
            for _ in range(7):
                await pulse()
            await asyncio.wait_for(task, 1)
            final = await service.get_snapshot(sid)
            assert final['estado'] == 'completed' and final['reloj'] == 17
            assert final['terminados'][0]['bloqueado'] == 10
        finally:
            await service.close()
        assert task.done() and not service.simulaciones
    asyncio.run(run())


def test_fcfs_json_examples_are_reproducible():
    motor = SimulationEngine.create(4, seed=123)
    assert json.loads(Path('docs/fixtures/motor-inicial.json').read_text(encoding='utf-8')) == motor.snapshot()
    async def run():
        service = SimulationService(auto_clock=False)
        try:
            actual = await service.create(4, seed=123)
            example = json.loads(Path('docs/contrato-api.json').read_text(encoding='utf-8'))
            # El UUID publicado fue generado realmente; cada ejecución obtiene otro.
            assert actual.pop('simulacion_id') != example.pop('simulacion_id')
            assert actual == example
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('seed', [True, 1.0, '123', [], {}])
def test_http_rejects_invalid_seed(seed):
    with TestClient(create_app(auto_clock=False)) as client:
        assert client.post('/api/simulations', json={'numero_trabajos': 1, 'seed': seed}).status_code == 422
