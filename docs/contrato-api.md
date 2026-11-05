# Contrato HTTP actual e integración FCFS — Actividad 6

Referencia del código revisado en `backend/routes.py`, `backend/schemas.py` y `backend/service.py`. Las rutas ya existen; no se implementaron ni modificaron en esta actualización de documentación. El motor y su salida se describen en [cambios-backend-fcfs.md](cambios-backend-fcfs.md). Las verificaciones que debe completar API están en [entrega-motor.md](entrega-motor.md).

## Rutas existentes

| Método y ruta | Entrada | Respuesta correcta |
| --- | --- | --- |
| `GET /api/health` | Ninguna. | 200: status con valor ok. |
| `POST /api/simulations` | numero_trabajos entero positivo; seed opcional, entero o null. | 201: simulacion_id y snapshot inicial. |
| `GET /api/simulations/{simulacion_id}` | ID existente. | 200: simulacion_id y snapshot actual, sin avanzar tiempo. |
| `POST /api/simulations/{simulacion_id}/actions` | accion: interrupt, error, pause o continue. | 200: simulacion_id y snapshot después de la acción. |

Ejemplo de creación: `{"numero_trabajos":4,"seed":123}`. Ejemplo de acción: `{"accion":"interrupt"}`. No hay endpoint público de tick ni de creación de procesos durante la ejecución.

## Servicio y reloj

`SimulationService` conserva motores por ID, una tarea de reloj y un `asyncio.Lock` por simulación. El reloj llama `tick()`; el motor ignora ticks en paused/completed. El bloqueo serializa ticks, acciones y snapshots. GET no llama tick.

El servicio devuelve la envoltura `{"simulacion_id": simulacion_id, **motor.snapshot()}` sin renombrar los campos del motor. La opción `auto_clock=False` permite pruebas deterministas. `tick_once(simulacion_id)` es un método interno del servicio para avanzar en pruebas; no es una ruta HTTP. El servidor utiliza estado en memoria y un solo worker.

## Acciones y errores

| accion | Método del motor | Efecto |
| --- | --- | --- |
| interrupt | interrupt() | Bloquea la CPU 10 segundos simulados conservando memoria y avance. |
| error | fail() | Termina la CPU por error, libera memoria y admite un nuevo si existe. |
| pause | pause() | Congela reloj, CPU, espera y bloqueos. |
| continue | resume() | Reanuda desde el mismo estado. |

- 422: cantidad o semilla de tipo incorrecto, cantidad no positiva, acción desconocida o cuerpo inválido. No aceptar bool, decimales ni cadenas como enteros.
- 404: simulación inexistente en consulta o acciones.
- 409: `SimulationStateError`: I/E sin CPU, en pausa o al terminar; P/C al terminar.
- P en paused y C en running son válidos y no consumen tiempo.

Los errores controlados usan `detail` con texto; la validación de FastAPI puede devolver una lista. Mantener los datos del motor intactos después de una acción rechazada.

## Respuesta FCFS

El objeto superior contiene `simulacion_id` del servicio y estos campos del motor:

| Campo | Tipo y significado |
| --- | --- |
| estado | running, paused o completed. |
| reloj | Entero de segundos simulados. |
| total_trabajos | Cantidad inicial. |
| nuevos | Lista de procesos new pendientes de entrar a memoria. |
| en_espera | Lista de procesos ready en orden FCFS. |
| en_ejecucion | Proceso running o null. Puede ser null con estado running. |
| bloqueados | Lista de procesos blocked en orden de bloqueo. |
| terminados | Lista de procesos finished/error en orden de terminación. |
| memoria_ocupada | Entero de 0 a 3; incluye listos, CPU y bloqueados. |

Cada proceso contiene `id`, `estado`, `operacion`, `operando_a`, `operando_b`, `tme`, `ejecutado`, `restante`, `resultado`, `llegada`, `primera_atencion`, `finalizacion`, `retorno`, `respuesta`, `espera`, `bloqueado` e `inicio_bloqueo`. Ver tipos y fórmulas en [la guía del motor](cambios-backend-fcfs.md#datos-de-cada-proceso).

Solo dentro de `bloqueados` se agregan `bloqueo_transcurrido` y `bloqueo_restante` del bloqueo actual. `bloqueado` es el acumulado de todos sus bloqueos. Los instantes y tiempos todavía desconocidos son null; cero sigue siendo válido. El servicio no debe reemplazarlos ni volver a calcularlos.

`ejecutado` es el servicio. `restante` es cero al terminar por error aunque el servicio sea menor que TME. `resultado` es numérico al terminar normalmente y null por error o mientras vive; mostrar ERROR según `estado == error`.

Se eliminaron `lote`, `lote_actual` y `lotes_pendientes` de la respuesta. No agregar valores ficticios para conservar la pantalla anterior. En completed: CPU null, listas de nuevos/listos/bloqueados vacías, memoria 0 y resultados conservados.

## Ejemplos reproducibles y comprobaciones

Para implementar la pantalla, empezar por [la guía de frontend](guia-frontend-fcfs.md): incluye campos y tiempos, representación de estados y cuatro respuestas HTTP completas capturadas y contrastadas con el motor, con su secuencia de reproducción.

`fixtures/motor-inicial.json` es el snapshot de `SimulationEngine.create(4, seed=123).snapshot()`. `contrato-api.json` es una respuesta inicial real generada con `await SimulationService(auto_clock=False).create(4, seed=123)`: contiene un UUID generado por el servicio, que cambiará en cada creación. Ambos reemplazan los ejemplos históricos de lotes. `test_fcfs_json_examples_are_reproducible` compara todos los campos, excluyendo únicamente el UUID variable del ejemplo HTTP.

Los cuatro ejemplos de [la guía del motor](cambios-backend-fcfs.md#ejemplos-obtenidos-del-motor) siguen siendo válidos; HTTP agrega únicamente `simulacion_id`.

`tests/test_api_fcfs.py`, `test_api.py` y `test_service.py` comprueban creación con cuatro procesos, snapshot completo en cada ruta, orden FCFS, null y cero, admisión normal/por error, bloqueo de tres residentes, segundos 9/10, pausa con CPU y con todos bloqueados, consultas sin avance, errores sin mutaciones, tiempos conocidos, finalización, aislamiento, lock compartido y cierre. La tarea automática se prueba con pulsos controlados de su espera de un segundo, sin esperar segundos reales. Al completar el último tick la tarea termina; `close()` cancela las restantes y libera los registros. Las acciones desconocidas directas del servicio generan ValueError; HTTP las rechaza antes con 422.

El reloj automático puede avanzar entre dos GET por el paso del tiempo; consultar no origina ticks. No se ha validado la interfaz FCFS ni un recorrido de navegador con reloj real en este paso.
