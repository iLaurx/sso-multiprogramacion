"""Recorridos del servicio y HTTP: mismo snapshot, reloj, quantum y colas."""
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
    oracle = SimulationEngine.create(4, seed=123, quantum=100)
    with TestClient(app) as client:
        response = client.post('/api/simulations', json={'numero_trabajos': 4, 'seed': 123, 'quantum': 100})
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
        for name in ('interrupt', 'error', 'add_process'):
            assert client.post(route + '/actions', json={'accion': name}).status_code == 409
            check(paused_cpu)
        action('continue', oracle.resume)
        for _ in range(3):
            blocked = action('interrupt', oracle.interrupt)
        assert blocked['en_ejecucion'] is None
        assert blocked['tiempo_turno'] is None
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
        eighth = tick(8)
        assert [p['bloqueo_restante'] for p in eighth['bloqueados']] == [1, 1, 1]
        ninth = tick(1)
        assert ninth['en_ejecucion']['id'] == 1
        assert ninth['en_ejecucion']['ejecutado'] == 2
        assert [p['id'] for p in ninth['en_espera']] == [2, 3]
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
        assert final['tiempo_turno'] is None
        assert final['nuevos'] == final['en_espera'] == final['bloqueados'] == []
        for p in final['terminados']:
            assert p['retorno'] == p['espera'] + p['ejecutado'] + p['bloqueado']
        assert tick(3) == final
        for name in ('interrupt', 'error', 'pause', 'continue', 'add_process'):
            assert client.post(route + '/actions', json={'accion': name}).status_code == 409
            check(final)


def test_http_round_robin_turns_pause_idle_and_actions():
    app = create_app(auto_clock=False)
    oracle = SimulationEngine.create(2, seed=123, quantum=3)
    with TestClient(app) as client:
        res = client.post('/api/simulations', json={'numero_trabajos': 2, 'seed': 123, 'quantum': 3})
        assert res.status_code == 201
        initial = res.json()
        sid = initial['simulacion_id']
        route = f'/api/simulations/{sid}'

        assert initial == {'simulacion_id': sid, **oracle.snapshot()}
        assert initial['quantum'] == 3
        assert initial['tiempo_turno'] == 0
        assert initial['en_ejecucion']['id'] == 1

        # Avanza 2 ticks: sigue P1 con tiempo_turno == 2
        for _ in range(2):
            client.portal.call(app.state.service.tick_once, sid)
            oracle.tick()
        mid_turn = client.get(route).json()
        assert mid_turn == {'simulacion_id': sid, **oracle.snapshot()}
        assert mid_turn['en_ejecucion']['id'] == 1
        assert mid_turn['tiempo_turno'] == 2

        # Tercer tick: vence el quantum=3, P1 pasa a listos con ejecutado=3 y entra P2 con tiempo_turno=0
        client.portal.call(app.state.service.tick_once, sid)
        oracle.tick()
        rotated = client.get(route).json()
        assert rotated == {'simulacion_id': sid, **oracle.snapshot()}
        assert rotated['reloj'] == 3
        assert rotated['quantum'] == 3
        assert rotated['tiempo_turno'] == 0
        assert rotated['en_ejecucion']['id'] == 2
        assert rotated['en_espera'][0]['id'] == 1
        assert rotated['en_espera'][0]['ejecutado'] == 3
        assert rotated['en_espera'][0]['restante'] == 4

        # Pausa conserva quantum y tiempo_turno
        oracle.pause()
        paused = client.post(route + '/actions', json={'accion': 'pause'}).json()
        assert paused == {'simulacion_id': sid, **oracle.snapshot()}
        assert paused['estado'] == 'paused'
        assert paused['quantum'] == 3
        assert paused['tiempo_turno'] == 0

        # Continuar y agregar proceso dinámico
        oracle.resume()
        client.post(route + '/actions', json={'accion': 'continue'})
        oracle.add_process()
        added = client.post(route + '/actions', json={'accion': 'add_process'}).json()
        assert added == {'simulacion_id': sid, **oracle.snapshot()}
        assert added['total_trabajos'] == 3

        # Escenario de CPU libre con bloqueado (quantum=3, tiempo_turno=None)
        oracle_idle = SimulationEngine.create(1, seed=123, quantum=3)
        res_idle = client.post('/api/simulations', json={'numero_trabajos': 1, 'seed': 123, 'quantum': 3}).json()
        sid_idle = res_idle['simulacion_id']
        route_idle = f'/api/simulations/{sid_idle}'
        client.portal.call(app.state.service.tick_once, sid_idle)
        oracle_idle.tick()
        oracle_idle.interrupt()
        idle_state = client.post(route_idle + '/actions', json={'accion': 'interrupt'}).json()
        assert idle_state == {'simulacion_id': sid_idle, **oracle_idle.snapshot()}
        assert idle_state['en_ejecucion'] is None
        assert idle_state['tiempo_turno'] is None
        assert idle_state['quantum'] == 3
        assert len(idle_state['bloqueados']) == 1


def test_http_add_process_and_bcp_pause_consistency():
    app = create_app(auto_clock=False)
    oracle = SimulationEngine.create(2, seed=123, quantum=4)
    with TestClient(app) as client:
        res = client.post('/api/simulations', json={'numero_trabajos': 2, 'seed': 123, 'quantum': 4})
        assert res.status_code == 201
        sid = res.json()['simulacion_id']
        route = f'/api/simulations/{sid}'

        oracle.add_process()
        added_ready = client.post(route + '/actions', json={'accion': 'add_process'})
        assert added_ready.status_code == 200
        data_ready = added_ready.json()
        assert data_ready == {'simulacion_id': sid, **oracle.snapshot()}
        assert data_ready['memoria_ocupada'] == 3
        assert data_ready['total_trabajos'] == 3
        assert [p['id'] for p in data_ready['en_espera']] == [2, 3]
        assert data_ready['nuevos'] == []

        oracle.add_process()
        added_new = client.post(route + '/actions', json={'accion': 'add_process'})
        assert added_new.status_code == 200
        data_new = added_new.json()
        assert data_new == {'simulacion_id': sid, **oracle.snapshot()}
        assert data_new['total_trabajos'] == 4
        assert len(data_new['nuevos']) == 1
        nuevo = data_new['nuevos'][0]
        assert nuevo['id'] == 4
        assert nuevo['estado'] == 'new'
        assert nuevo['llegada'] is None
        assert nuevo['primera_atencion'] is None
        assert nuevo['finalizacion'] is None
        assert nuevo['retorno'] is None
        assert nuevo['respuesta'] is None

        oracle.pause()
        bcp_pause = client.post(route + '/actions', json={'accion': 'pause'})
        assert bcp_pause.status_code == 200
        bcp_data = bcp_pause.json()
        assert bcp_data['estado'] == 'paused'
        assert bcp_data == client.get(route).json()

        assert client.post(route + '/actions', json={'accion': 'add_process'}).status_code == 409


def test_http_known_times(known_engine):
    known_engine(4)  # Sustituye solo el generador por trabajos 8+3, TME=7.
    app = create_app(auto_clock=False)
    with TestClient(app) as client:
        sid = client.post('/api/simulations', json={'numero_trabajos': 4, 'quantum': 10}).json()['simulacion_id']
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
        a, b = await asyncio.gather(
            service.create(4, 123, quantum=5),
            service.create(1, 123, quantum=2),
        )
        aid, bid = a['simulacion_id'], b['simulacion_id']
        assert a['quantum'] == 5 and b['quantum'] == 2
        register = service.simulaciones[aid]
        async with register.lock:
            pending = [asyncio.create_task(service.tick_once(aid)),
                       asyncio.create_task(service.apply_action(aid, 'interrupt')),
                       asyncio.create_task(service.apply_action(aid, 'add_process')),
                       asyncio.create_task(service.get_snapshot(aid))]
            await asyncio.sleep(0)
            assert all(not task.done() for task in pending)
        _, _, action_add, snapshot = await asyncio.gather(*pending)
        assert action_add == snapshot
        assert snapshot['reloj'] == 1
        assert snapshot['total_trabajos'] == 5
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
        initial = await service.create(1, 123, quantum=3)
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
            for _ in range(8):
                await pulse()
            state = await service.get_snapshot(sid)
            assert state['reloj'] == 8 and state['en_ejecucion'] is None
            assert state['tiempo_turno'] is None
            assert state['bloqueados'][0]['bloqueo_restante'] == 1
            await pulse()
            assert (await service.get_snapshot(sid))['en_ejecucion']['ejecutado'] == 0
            for _ in range(7):
                await pulse()
            await asyncio.wait_for(task, 1)
            final = await service.get_snapshot(sid)
            assert final['estado'] == 'completed' and final['reloj'] == 16
            assert final['terminados'][0]['bloqueado'] == 9
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
            assert actual.pop('simulacion_id') != example.pop('simulacion_id')
            assert actual == example
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize('seed', [True, 1.0, '123', [], {}])
def test_http_rejects_invalid_seed(seed):
    with TestClient(create_app(auto_clock=False)) as client:
        assert client.post('/api/simulations', json={'numero_trabajos': 1, 'seed': seed}).status_code == 422


@pytest.mark.parametrize('quantum', [0, -1, -10, True, False, 1.5, '3', None, [], {}])
def test_http_rejects_invalid_quantum(quantum):
    with TestClient(create_app(auto_clock=False)) as client:
        assert client.post('/api/simulations', json={'numero_trabajos': 1, 'quantum': quantum}).status_code == 422