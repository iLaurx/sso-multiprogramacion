# Entrega del motor Round Robin a API

El motor de actividad 10 reemplaza la planificación FCFS por Round Robin. Este documento describe el contrato Python comprobado; API, servicio y frontend requieren adaptación y no se han comprobado como parte de esta entrega.

## Creación y consultas

```python
from simulation import SimulationEngine, SimulationStateError
motor = SimulationEngine.create(2, seed=123, quantum=3)
estado = motor.snapshot()
```

`numero_trabajos` debe ser entero positivo, `seed` entero o `None` y `quantum` entero positivo sin booleanos. La semilla sigue siendo el segundo argumento posicional; `quantum` se pasa por nombre y su valor por defecto es 1 para conservar las llamadas anteriores. La API debe decidir si exige el campo, y transmitir el valor elegido; la interfaz debe solicitarlo. El motor rechaza valores inválidos con `ValueError`.

`snapshot()` agrega `quantum` y `tiempo_turno` (segundos ejecutados en el turno actual, entre 0 y quantum − 1; `null` cuando la CPU está libre). Se reinicia en cada despacho, incluso cuando vuelve a ejecutarse el mismo proceso; no sustituye `ejecutado`, que es el servicio acumulado. Pausar conserva el contador. Consultar no avanza el reloj ni devuelve referencias a procesos internos. Los demás campos y el orden de colas se conservan; el servicio agrega `simulacion_id`.

`tick()` avanza un segundo; `interrupt()` bloquea durante 9 segundos; `fail()` termina por error; `pause()` y `resume()` detienen y reanudan; `add_process()` crea un proceso mientras está running; `processes_snapshot()` consulta todos por ID. Los controles de pantalla E, W, P, C, N y B no se interpretan en el motor. Los bloqueados ocupan memoria; CPU libre con bloqueados sigue running. La primera atención se registra una vez y se conserva el servicio. Las acciones incompatibles generan `SimulationStateError`.

Al agotarse el quantum, si el proceso no terminó, vuelve al final de listos. La finalización tiene prioridad sobre el vencimiento. Si en ese segundo se desbloquea un proceso, se encola primero detrás de los que ya esperaban y luego el desalojado; un nuevo admitido por finalización queda después de los desbloqueados. El despacho no consume tiempo. Llegada es admisión a memoria, espera cuenta solo listos y retorno = espera + servicio + bloqueo.

## Ejemplos completos reproducibles

Los primeros tres snapshots corresponden a `create(2, seed=123, quantum=3)`: inicial, después de tres ticks, y tras `pause()`. El cuarto se obtiene creando `create(1, seed=123, quantum=3)`, avanzando un tick y llamando `interrupt()`. Las pruebas comparan estos bloques con el motor real.

### Inicial

```json
{
  "estado": "running",
  "reloj": 0,
  "quantum": 3,
  "tiempo_turno": 0,
  "nuevos": [],
  "bloqueados": [],
  "memoria_ocupada": 2,
  "total_trabajos": 2,
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
    }
  ],
  "terminados": []
}
```

### Cambio de turno

```json
{
  "estado": "running",
  "reloj": 3,
  "quantum": 3,
  "tiempo_turno": 0,
  "nuevos": [],
  "bloqueados": [],
  "memoria_ocupada": 2,
  "total_trabajos": 2,
  "en_ejecucion": {
    "id": 2,
    "estado": "running",
    "operacion": "*",
    "operando_a": -72,
    "operando_b": -90,
    "tme": 13,
    "ejecutado": 0,
    "restante": 13,
    "resultado": null,
    "llegada": 0,
    "primera_atencion": 3,
    "finalizacion": null,
    "retorno": null,
    "respuesta": 3,
    "espera": 3,
    "bloqueado": 0,
    "inicio_bloqueo": null
  },
  "en_espera": [
    {
      "id": 1,
      "estado": "ready",
      "operacion": "*",
      "operando_a": -77,
      "operando_b": 97,
      "tme": 7,
      "ejecutado": 3,
      "restante": 4,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": 0,
      "finalizacion": null,
      "retorno": null,
      "respuesta": 0,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": null
    }
  ],
  "terminados": []
}
```

### Pausa

```json
{
  "estado": "paused",
  "reloj": 3,
  "quantum": 3,
  "tiempo_turno": 0,
  "nuevos": [],
  "bloqueados": [],
  "memoria_ocupada": 2,
  "total_trabajos": 2,
  "en_ejecucion": {
    "id": 2,
    "estado": "running",
    "operacion": "*",
    "operando_a": -72,
    "operando_b": -90,
    "tme": 13,
    "ejecutado": 0,
    "restante": 13,
    "resultado": null,
    "llegada": 0,
    "primera_atencion": 3,
    "finalizacion": null,
    "retorno": null,
    "respuesta": 3,
    "espera": 3,
    "bloqueado": 0,
    "inicio_bloqueo": null
  },
  "en_espera": [
    {
      "id": 1,
      "estado": "ready",
      "operacion": "*",
      "operando_a": -77,
      "operando_b": 97,
      "tme": 7,
      "ejecutado": 3,
      "restante": 4,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": 0,
      "finalizacion": null,
      "retorno": null,
      "respuesta": 0,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": null
    }
  ],
  "terminados": []
}
```

### CPU libre con bloqueado

```json
{
  "estado": "running",
  "reloj": 1,
  "quantum": 3,
  "tiempo_turno": null,
  "nuevos": [],
  "bloqueados": [
    {
      "id": 1,
      "estado": "blocked",
      "operacion": "*",
      "operando_a": -77,
      "operando_b": 97,
      "tme": 7,
      "ejecutado": 1,
      "restante": 6,
      "resultado": null,
      "llegada": 0,
      "primera_atencion": 0,
      "finalizacion": null,
      "retorno": null,
      "respuesta": 0,
      "espera": 0,
      "bloqueado": 0,
      "inicio_bloqueo": 1,
      "bloqueo_transcurrido": 0,
      "bloqueo_restante": 9
    }
  ],
  "memoria_ocupada": 1,
  "total_trabajos": 1,
  "en_ejecucion": null,
  "en_espera": [],
  "terminados": []
}
```
