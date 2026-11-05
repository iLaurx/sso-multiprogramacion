# Motor FCFS — Actividad 8

Alcance autorizado: solo `simulation/`, pruebas del motor y documentación. API,
servicio y frontend conservan su implementación de actividad 6; esta entrega no
acredita su integración con actividad 8. La consigna revisada es
`C:/Users/ele/Downloads/Actividad 8 SSO.pdf`.

## Métodos para API

Importar `SimulationEngine` y `SimulationStateError` desde `simulation`.

| Método | Contrato |
| --- | --- |
| `create(numero_trabajos, seed=None)` | Conserva validaciones y generación inicial. Cada instancia mantiene su propio generador aleatorio; la semilla reproduce datos iniciales y altas posteriores. |
| `add_process() -> dict` | Genera exactamente un proceso, sin argumentos del cliente. Solo en `running`, incluso con CPU libre y bloqueados. En pausa o al finalizar lanza `SimulationStateError`, sin consumir ID ni azar ni cambiar datos. Devuelve una copia del proceso después de intentar admitirlo. |
| `processes_snapshot() -> list[dict]` | Copias de todos los procesos, incluidos nuevos y terminados por error, ordenadas por ID. Incluye bloqueo restante cuando corresponde. Funciona en running, paused y completed; no pausa ni avanza tiempo. |
| `snapshot() -> dict` | Conserva las mismas claves y el orden de las colas. Ahora `total_trabajos` cuenta iniciales más altas aceptadas. |
| `interrupt()` | Bloquea la CPU exactamente 9 segundos simulados, conservando memoria y servicio. Corresponde a E en actividad 8. |
| `fail()` | Termina por error con servicio real y resultado null. Corresponde a W en actividad 8. |
| `pause()` / `resume()` | Conservan el comportamiento P/C. Para B, el equipo debe pausar y luego consultar los procesos dentro de la misma exclusión mutua del servicio. |
| `tick()` | Conserva avance de un segundo, incluidos CPU ociosa y bloqueados. No hace nada en pausa ni al finalizar. |

Los IDs son consecutivos y únicos **dentro de cada simulación**, desde 1; nunca
se reutilizan al terminar un proceso. El total inicial no es un límite de altas.
Los datos conservan rangos: TME 7–18, operandos enteros −99–99, operaciones
`+`, `-`, `*`, `/`, `%`; divisor distinto de cero en división y residuo.

Cada alta entra al final de nuevos. Si hay lugar, se admite al final de listos
en el mismo instante; no desplaza la CPU activa. Si la CPU está libre y hay un
listo, se despacha inmediatamente. Listos + CPU + bloqueados nunca supera tres.
Bloquear no libera memoria. Ningún alta adelanta a los nuevos anteriores.

## Campos y tiempos

Se conservan los campos de proceso documentados en
[cambios-backend-fcfs.md](cambios-backend-fcfs.md). No se añade una lista duplicada
al snapshot general: `processes_snapshot()` reúne sus cinco estados.

- `total_trabajos`: total acumulado de procesos generados, incluidos terminados.
- `nuevos`: su longitud es la cantidad pendiente de admisión.
- `bloqueo_transcurrido`: reloj menos inicio del bloqueo actual (0–8).
- `bloqueo_restante`: 9 menos transcurrido (9–1); al cumplir 9, el proceso sale de bloqueados y estas dos claves desaparecen.
- `bloqueado`: duración acumulada de todos los bloqueos, también el actual.
- `ejecutado`: servicio acumulado real; `restante` es TME menos servicio en vivos y cero en terminados, incluso por error.
- `llegada`: admisión a memoria, no generación. Permanece null en nuevos.
- `primera_atencion`, `finalizacion`, `retorno`, `respuesta`: null hasta que ocurra el evento correspondiente. Cero es válido.
- `espera`: solo tiempo en listos; nuevos queda fuera. Al finalizar, `retorno = espera + ejecutado + bloqueado`.
- `estado`: `new`, `ready`, `running`, `blocked`, `finished` o `error`. El resultado numérico solo existe al terminar normalmente; `error` identifica ERROR.

El motor conserva operación, TME y acumuladores cero de los nuevos para no perder
sus datos. La indicación del PDF de mostrar campos nulos para nuevos corresponde
a la presentación de la tabla; el consumidor debe representarlos sin borrar los
datos internos ni convertir los null de tiempos en cero.

`completed` significa que no quedan nuevos, listos, CPU ni bloqueados; todos los
procesos del total actualizado están en terminados. CPU null por sí sola no
indica final. No se permite reabrir una simulación completed con N.

## Ejemplo Python

```python
motor = SimulationEngine.create(3, seed=123)
nuevo = motor.add_process()       # id=4, estado=new, llegada=None
assert motor.snapshot()["total_trabajos"] == 4
motor.interrupt()                # E: bloquea 9 segundos; no libera memoria
motor.pause()                    # B: pausar antes de consultar la tabla
tabla = motor.processes_snapshot()
assert tabla[0]["bloqueo_restante"] == 9
motor.resume()                   # C
```

El servicio sigue siendo responsable del reloj real y de serializar tick,
controles, altas y consultas con su bloqueo por simulación. Para exponer N/B debe
conectar estos métodos y probar sus rutas; no generar procesos desde API ni
recalcular tiempos. Las rutas actuales no tienen acciones N/B. Los fixtures y
pruebas HTTP de actividad 6 pueden seguir esperando bloqueos de 10 segundos y
deberán revisarse por el compañero de API. No se modificaron en esta tarea.

## Verificación del motor

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_engine.py tests/test_models.py tests/test_times.py tests/test_snapshot_fcfs.py tests/test_fcfs_handoff.py tests/test_dynamic_processes.py
```

92 pruebas aprobadas: 79 actualizadas a bloqueo de 9 segundos y 13 nuevas.
Incluyen 2000 altas reproducibles, rangos/divisores, IDs, rechazo en pausa/final,
admisión con y sin espacio, CPU libre, nuevos FIFO, consultas independientes,
secuencias mixtas con altas, partición de tiempos y cierre de todos los procesos.
