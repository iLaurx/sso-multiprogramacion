# Cambios del backend a FCFS — Actividad 6

Guía del motor implementado de **Sistemas Operativos**. Describe el código actual de `simulation/`, no una propuesta. Sustituye las reglas de lotes de `contrato-api.md` para integrar FCFS. No se modificaron API ni frontend en este paso.

## Métodos disponibles

Se importa con `from simulation import SimulationEngine, SimulationStateError`.

| Método | Comportamiento real |
| --- | --- |
| `SimulationEngine.create(numero_trabajos, seed=None)` | Genera todos los procesos, admite hasta tres residentes y despacha el primero en reloj 0. Cantidad: entero positivo, sin bool; semilla: entero sin bool o None. Entrada inválida genera ValueError. |
| `tick()` | Avanza un segundo simulado en running: servicio de CPU, espera de listos y bloqueos. Funciona con CPU libre. En paused o completed no cambia nada. Devuelve None. |
| `interrupt()` | I: mueve la CPU a blocked durante 10 segundos simulados. Conserva servicio y memoria; despacha al siguiente listo. No avanza el reloj. |
| `fail()` | E: termina la CPU como error, registra finalización, conserva servicio real y resultado None. Libera memoria y admite al siguiente nuevo. No avanza el reloj. |
| `pause()` / `resume()` | P/C: detienen todo o continúan. Repetir P en pausa o C en running es válido. En completed generan SimulationStateError. |
| `snapshot()` | Devuelve un diccionario nuevo serializable a JSON, sin ticks ni cambios de estado. Las acciones anteriores devuelven None: consultar después con este método. |
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

## Implementado y pendiente de integración

Implementado y probado en el motor: FCFS, admisión continua, tres residentes contando bloqueados, I durante 10 segundos, E con servicio real, P/C completos, reloj con CPU libre, cierre correcto, tiempos y snapshots independientes serializables.

El servicio actual de `backend/service.py` ya utiliza el motor y transmite su snapshot sin transformarlo, agregando `simulacion_id`. Por eso las respuestas HTTP reciben estos cambios aunque no se hayan editado API ni rutas. Sus acciones actuales son interrupt, error, pause y continue; no existe endpoint público de tick. La frase de `contrato-api.md` que afirma que solo health está implementado está desactualizada frente al código actual.

Pendiente: revisar formalmente la integración y su documentación de API con este esquema, adaptar la pantalla de lotes y probar el recorrido visual. La pantalla actual espera lote_actual, lotes_pendientes y lote; esos campos ya no se devuelven. No debe calcular tiempos localmente. La aprobación de las pruebas del motor/API no acredita esa adaptación visual. README y los ejemplos antiguos de contrato-api siguen pendientes de actualización en su etapa correspondiente.

No se agregaron funciones de actividad 8, creación de procesos durante ejecución ni controles N/B. Commit local autorizado por el usuario; no se hizo push ni despliegue.
