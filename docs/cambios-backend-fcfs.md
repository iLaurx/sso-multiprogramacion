# Cambios del backend a FCFS — Actividad 6

Guía del motor implementado de **Sistemas Operativos**. Describe el código actual de `simulation/`, no una propuesta. Es la referencia Python para integrar FCFS; `contrato-api.md` describe su envoltura HTTP. No se modificaron API ni frontend en este paso.

La integración siguiente y sus criterios de aceptación están en [entrega-motor.md](entrega-motor.md). El [contrato HTTP](contrato-api.md) ya se actualizó por escrito al código existente; aún falta cerrar las verificaciones de integración indicadas allí. Esta guía conserva los ejemplos y el contrato Python del motor.

## Por dónde empezar en API

1. Usar esta guía y sus cuatro snapshots como referencia del motor. `fcfs.md` explica las reglas; `contrato-api.md` documenta las rutas actuales. Su JSON separado `contrato-api.json` todavía es de lotes y debe reemplazarse al integrar.
2. Revisar el recorrido ya existente: rutas → servicio → `SimulationEngine`. Mantener `simulacion_id` en el servicio y el reloj bajo su control; GET solo consulta. El motor no necesita un segundo planificador ni un reloj adicional.
3. Revisar los esquemas de respuesta o consumidores del equipo: quitar campos de lotes, admitir `new`/`blocked`, tiempos con null y `en_ejecucion: null` aun en running. No traducir null a cero. Las listas conservan el orden recibido.
4. Comprobar las acciones con los nombres HTTP actuales: `interrupt` → `interrupt()`, `error` → `fail()`, `pause` → `pause()` y `continue` → `resume()`. Con todos bloqueados, I/E deben producir conflicto, sin cerrar la simulación ni impedir P/C.
5. Validar el contrato escrito y probar el reloj del servicio con CPU libre, pausa y desbloqueo siguiendo [la entrega](entrega-motor.md#criterios-para-cerrar-api); después coordinar la adaptación de la pantalla. No usar `Process` directamente para crear trabajos durante una simulación.

## Métodos disponibles

Se importa con `from simulation import SimulationEngine, SimulationStateError`.

| Método | Comportamiento real |
| --- | --- |
| `SimulationEngine.create(numero_trabajos, seed=None)` | Genera todos los procesos, admite hasta tres residentes y despacha el primero en reloj 0. Cantidad: entero positivo, sin bool; semilla: entero sin bool o None. Entrada inválida genera ValueError. |
| `tick()` | Avanza un segundo simulado en running: servicio de CPU, espera de listos y bloqueos. Funciona con CPU libre. En paused o completed no cambia nada. Devuelve None. |
| `interrupt()` | I: mueve la CPU a blocked durante 10 segundos simulados. Conserva servicio y memoria; despacha al siguiente listo. No avanza el reloj. |
| `fail()` | E: termina la CPU como error, registra finalización, conserva servicio real y resultado None. Libera memoria y admite al siguiente nuevo. No avanza el reloj. |
| `pause()` / `resume()` | P/C: detienen todo o continúan. Repetir P en pausa o C en running es válido. En completed generan SimulationStateError. |
| `snapshot()` | Devuelve un diccionario nuevo serializable a JSON, sin ticks ni cambios de estado. tick/I/E/P/C devuelven None: consultar después con este método. create devuelve el motor. |
| `memoria_ocupada` | Propiedad entera: listos + CPU + bloqueados, entre 0 y 3. |

I/E generan `SimulationStateError` en pausa, al finalizar o si no hay CPU activa. Con todos bloqueados el estado sigue running, I/E se rechazan y P/C siguen disponibles. El motor no espera segundos reales ni depende de FastAPI; el servicio llama tick y controla la concurrencia.

## Snapshot de simulación

| Campo | Tipo y significado |
| --- | --- |
| `estado` | running, paused o completed. Se conserva. |
| `reloj` | Entero de segundos simulados. Se conserva. |
| `total_trabajos` | Cantidad inicial; todos se generan al crear. Se conserva. |
| `en_ejecucion` | Objeto de proceso o null si la CPU está libre. Se conserva. |
| `en_espera` | Lista de listos ready en orden FCFS; ya no corresponde a un lote. |
| `terminados` | Lista en orden de terminación, tanto finished como error. Se conserva. |
| `nuevos` | Lista de procesos new pendientes de admisión, en orden. Agregada en la adaptación. |
| `bloqueados` | Lista de procesos blocked en orden de bloqueo. Agregada en la adaptación. |
| `memoria_ocupada` | Entero de residentes. Agregado en la adaptación. |

Se eliminan `lote_actual` y `lotes_pendientes`. El motor no devuelve `simulacion_id`: el servicio lo agrega. En completed las colas están vacías, CPU es null y memoria vale 0; reloj y terminados se conservan.

## Datos de cada proceso

| Campos | Tipo y uso |
| --- | --- |
| `id` | Entero único, consecutivo desde 1. Se conserva. |
| `estado` | new, ready, running, blocked, finished o error. new/blocked amplían los estados anteriores. |
| `operacion`, `operando_a`, `operando_b` | Símbolo +, -, *, / o % y operandos enteros. Se conservan. |
| `tme` | Entero aleatorio entre 7 y 18 inclusive. Se conserva. |
| `ejecutado` | Servicio real acumulado; no se duplica con otro campo servicio. Se conserva. |
| `restante` | tme - ejecutado en procesos vivos; 0 en finished/error. Se conserva sin completar artificialmente el servicio por error. |
| `resultado` | Número al finalizar normalmente; null mientras vive o por error. Se conserva: mostrar ERROR cuando estado sea error. |
| `llegada` | Instante de admisión a memoria, null mientras está en nuevos. Ahora público. |
| `primera_atencion` | Instante del primer despacho, null hasta recibir CPU; no se reinicia al desbloquear. Ahora público. |
| `finalizacion` | Instante de terminación normal o por error, null antes de terminar. Ahora público. |
| `retorno` | finalizacion - llegada, null hasta conocer ambos instantes. Ahora público. |
| `respuesta` | primera_atencion - llegada, null hasta conocer ambos instantes. Ahora público. |
| `espera` | Acumulado solo en listos; excluye nuevos, servicio y bloqueo. Ahora público. |
| `bloqueado` | Acumulado de E/S, incluidos bloqueos anteriores y el actual. Ahora público. |
| `inicio_bloqueo` | Instante del bloqueo actual; null fuera de blocked. Ahora público. |

Se elimina `lote` del snapshot de proceso. Permanece temporalmente en el constructor y generador como dato interno sin efecto en FCFS; no debe usarse en la integración.

Solo las entradas de `SimulationEngine.snapshot()['bloqueados']` añaden `bloqueo_transcurrido` y `bloqueo_restante`: reloj - inicio_bloqueo y 10 - transcurrido. Permiten mostrar el bloqueo actual sin confundirlo con `bloqueado` acumulado. Se calculan al consultar, sin modificar datos. No aparecen en el snapshot individual de Process ni en las otras colas.

Todos los tiempos se expresan en segundos simulados enteros. None se serializa como null; cero es un instante válido y no significa dato ausente. Para un terminado: retorno = espera + ejecutado + bloqueado. No se incluye tiempo en nuevos.

## Orden y reloj

Cada tick cuenta el intervalo de quienes ya estaban en CPU, listos o bloqueados. Al cumplirse 10 segundos, el bloqueado vuelve al final de listos, sin liberar memoria. Si coincide con una finalización, se encola antes del nuevo admitido y después de los listos existentes. Los desbloqueados simultáneos respetan su orden de bloqueo. El despacho no consume tiempo: quien recibe CPU al cerrar un tick ejecuta desde el siguiente. Pausa congela todos los tiempos.

## Ejemplos obtenidos del motor

Estos JSON se generaron ejecutando las secuencias indicadas con seed 123, sin sustituir el generador. La prueba `test_documented_json_examples_match_real_engine` reproduce y compara los cuatro ejemplos completos.

### 1. Estado inicial con nuevos y listos

```python
motor = SimulationEngine.create(4, seed=123)
motor.snapshot()
```

```json
{
  "estado": "running",
  "reloj": 0,
  "nuevos": [
    {
      "id": 4,
      "estado": "new",
      "operacion": "+",
      "operando_a": -59,
      "operando_b": -65,
      "tme": 12,
      "ejecutado": 0,
      "restante": 12,
      "resultado": null,
      "llegada": null,
      "primera_atencion": null,
      "finalizacion": null,
      "retorno": null,
      "respuesta": null,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": null
    }
  ],
  "bloqueados": [],
  "memoria_ocupada": 3,
  "total_trabajos": 4,
  "en_ejecucion": {
    "id": 1,
    "estado": "running",
    "operacion": "*",
    "operando_a": -77,
    "operando_b": 97,
    "tme": 7,
    "ejecutado": 0,
    "restante": 7,
    "resultado": null,
    "llegada": 0,
    "primera_atencion": 0,
    "finalizacion": null,
    "retorno": null,
    "respuesta": 0,
    "espera": 0,
    "bloqueado": 0,
    "inicio_bloqueo": null
  },
  "en_espera": [
    {
      "id": 2,
      "estado": "ready",
      "operacion": "*",
      "operando_a": -72,
      "operando_b": -90,
      "tme": 13,
      "ejecutado": 0,
      "restante": 13,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": null,
      "finalizacion": null,
      "retorno": null,
      "respuesta": null,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": null
    },
    {
      "id": 3,
      "estado": "ready",
      "operacion": "%",
      "operando_a": 44,
      "operando_b": -14,
      "tme": 13,
      "ejecutado": 0,
      "restante": 13,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": null,
      "finalizacion": null,
      "retorno": null,
      "respuesta": null,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": null
    }
  ],
  "terminados": []
}
```

### 2. CPU libre con un proceso bloqueado

```python
motor = SimulationEngine.create(1, seed=123)
for _ in range(2):
    motor.tick()
motor.interrupt()
for _ in range(3):
    motor.tick()
motor.snapshot()
```

```json
{
  "estado": "running",
  "reloj": 5,
  "nuevos": [],
  "bloqueados": [
    {
      "id": 1,
      "estado": "blocked",
      "operacion": "*",
      "operando_a": -77,
      "operando_b": 97,
      "tme": 7,
      "ejecutado": 2,
      "restante": 5,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": 0,
      "finalizacion": null,
      "retorno": null,
      "respuesta": 0,
      "espera": 0,
      "bloqueado": 3,
      "inicio_bloqueo": 2,
      "bloqueo_transcurrido": 3,
      "bloqueo_restante": 7
    }
  ],
  "memoria_ocupada": 1,
  "total_trabajos": 1,
  "en_ejecucion": null,
  "en_espera": [],
  "terminados": []
}
```

### 3. Error tras desbloquear, conservando servicio real

```python
# Continuar el ejemplo 2
for _ in range(7):
    motor.tick()
motor.fail()
motor.snapshot()
```

```json
{
  "estado": "completed",
  "reloj": 12,
  "nuevos": [],
  "bloqueados": [],
  "memoria_ocupada": 0,
  "total_trabajos": 1,
  "en_ejecucion": null,
  "en_espera": [],
  "terminados": [
    {
      "id": 1,
      "estado": "error",
      "operacion": "*",
      "operando_a": -77,
      "operando_b": 97,
      "tme": 7,
      "ejecutado": 2,
      "restante": 0,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": 0,
      "finalizacion": 12,
      "retorno": 12,
      "respuesta": 0,
      "espera": 0,
      "bloqueado": 10,
      "inicio_bloqueo": null
    }
  ]
}
```

### 4. Final normal

```python
motor = SimulationEngine.create(1, seed=123)
while motor.status != "completed":
    motor.tick()
motor.snapshot()
```

```json
{
  "estado": "completed",
  "reloj": 7,
  "nuevos": [],
  "bloqueados": [],
  "memoria_ocupada": 0,
  "total_trabajos": 1,
  "en_ejecucion": null,
  "en_espera": [],
  "terminados": [
    {
      "id": 1,
      "estado": "finished",
      "operacion": "*",
      "operando_a": -77,
      "operando_b": 97,
      "tme": 7,
      "ejecutado": 7,
      "restante": 0,
      "resultado": -7469,
      "llegada": 0,
      "primera_atencion": 0,
      "finalizacion": 7,
      "retorno": 7,
      "respuesta": 0,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": null
    }
  ]
}
```

## Resultado de la revisión de entrega

Revisión del 3 de noviembre de 2026 en `feature/fcfs`, con el árbol limpio al comenzar. No se encontraron fallos funcionales del motor en los casos comprobados, por lo que no se cambió su lógica ni su contrato. Se corrigió la descripción del paquete `simulation`, que todavía lo llamaba motor de lotes.

Se añadieron 15 secuencias reproducibles en `tests/test_fcfs_handoff.py`, con cantidades 1, 2, 3, 4 y 7 y semillas 0, 7 y 123. Después de cada control se comprueban procesos únicos y completos, capacidad de memoria, estados, tiempos sin reinicios y la igualdad `tiempo desde llegada = servicio + espera + bloqueo`, también antes de terminar. Incluyen controles rechazados, pausas y cierre tras dejar de interrumpir. El reloj total se contrasta con servicio global más CPU ociosa.

Comando de pruebas del motor:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_engine.py tests/test_models.py tests/test_times.py tests/test_snapshot_fcfs.py tests/test_fcfs_handoff.py
```

Resultado: **79 pruebas del motor aprobadas**. La suite completa con `-m pytest -q` dio **94 aprobadas**, incluidas las pruebas existentes de API y servicio. Los cuatro JSON de esta guía se reprodujeron y compararon exactamente contra el motor. Persisten avisos de permisos de caché de pytest y, en la suite completa, de deprecación Starlette/HTTPX; no son fallos de simulación.

## Motor terminado e incompatibilidades anteriores

Implementado y probado en el motor: FCFS, admisión continua, tres residentes contando bloqueados, I durante 10 segundos, E con servicio real, P/C completos, reloj con CPU libre, cierre correcto, tiempos y snapshots independientes serializables.

El servicio actual de `backend/service.py` ya utiliza el motor y transmite su snapshot sin transformarlo, agregando `simulacion_id`. Por eso las respuestas HTTP reciben estos cambios aunque no se hayan editado API ni rutas. Sus acciones actuales son interrupt, error, pause y continue; no existe endpoint público de tick. `contrato-api.md` ya describe esas rutas existentes; no hay que volver a crearlas.

Pendiente: verificar la integración de API con este esquema, ampliar sus pruebas, sustituir los fixtures JSON antiguos, adaptar la pantalla de lotes y probar el recorrido visual. La pantalla actual espera lote_actual, lotes_pendientes y lote; esos campos ya no se devuelven. No debe calcular tiempos localmente. La aprobación de las pruebas del motor/API no acredita esa adaptación visual. README ya señala esta situación; las tareas por área están en entrega-motor.md.

| Situación | Diagnóstico para API |
| --- | --- |
| Ya no hay lote, lote_actual ni lotes_pendientes | Cambio intencional de contrato FCFS; corregir consumidores anteriores. No implica que falte un lote en el motor. |
| CPU null con running y bloqueados presentes | Estado válido. El servicio debe seguir llamando tick; no usar CPU null como condición de final. |
| I no devuelve el proceso a listos inmediatamente | Comportamiento correcto de actividad 6: bloqueo de 10 segundos, con memoria ocupada. |
| I/E sin CPU activa devuelven SimulationStateError | Rechazo esperado; las rutas actuales lo traducen a HTTP 409. No es un fallo de desbloqueo. |
| resultado null con estado error | Contrato conservado: presentar ERROR a partir del estado. No reemplazar servicio por TME. |
| Bloqueos simultáneos o coincidentes con finalización | Orden definido en esta guía, probado en el motor; no reordenar desde API. |
| lote permanece dentro de Process/generador | Compatibilidad interna temporal sin efecto funcional ni exposición pública. No es trabajo pendiente para consumir snapshot. |

No hay un fallo conocido del motor que bloquee la entrega en el alcance revisado. Quedan la integración HTTP comprobada y la validación visual; no se declaran completadas por actualizar documentación. No se modificaron API, servicio ni frontend. No se agregaron funciones de actividad 8. La entrega del motor hasta `383a46f` se publicó en origin/feature/fcfs; esta actualización de Markdown es posterior y no se ha publicado. No se hizo despliegue.
