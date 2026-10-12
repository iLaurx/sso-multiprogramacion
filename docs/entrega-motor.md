# Entrega del integrante 1: motor de lotes

## Archivos

| Archivo | Función |
| --- | --- |
| `simulation/models.py` | Proceso, estados, tiempo restante y operaciones. |
| `simulation/generator.py` | Datos aleatorios válidos y semilla local. |
| `simulation/engine.py` | Lotes, cola, ticks y controles. |
| `simulation/__init__.py` | Importación pública del motor y su excepción. |
| `tests/conftest.py` | Trabajos conocidos para las pruebas. |
| `tests/test_engine.py` | Pruebas de las reglas del motor. |
| `docs/fixtures/motor-inicial.json` | Snapshot real de 4 trabajos con seed=123. |

## Contrato Python para el integrante 2

```python
from simulation import SimulationEngine, SimulationStateError

motor = SimulationEngine.create(numero_trabajos=4, seed=123)
estado = motor.snapshot()
```

`create()` devuelve un motor en `running`, con reloj cero y el primer proceso
despachado. La cantidad debe ser un entero positivo: rechaza booleanos,
decimales y cadenas. La semilla acepta un entero o `None`.
Las entradas inválidas generan `ValueError`.

| Llamada | Efecto |
| --- | --- |
| `tick()` | Suma una unidad al reloj y al proceso actual cuando está running. |
| `interrupt()` | I: coloca el actual al final del lote y despacha el siguiente. |
| `fail()` | E: termina el actual por error y despacha el siguiente. |
| `pause()` | P: cambia a paused. Repetir P en paused no modifica nada. |
| `resume()` | C: continúa desde paused. Repetir C en running no modifica nada. |
| `snapshot()` | Devuelve una copia con datos simples y listas, serializable a JSON. |

Los métodos de control y `tick()` devuelven `None`. Después de una acción,
llama a `snapshot()` para obtener el estado de respuesta.

I/E en pausa o al finalizar generan `SimulationStateError`. P/C al finalizar
también generan esa excepción; C no reinicia el motor. Los ticks en paused o
completed no cambian el estado. Para reiniciar, crea otro motor.

Las acciones no consumen tiempo. Un proceso terminado por E conserva lo que
ejecutó, tiene `resultado=null` y `restante=0`. Debe mostrarse ERROR según su
estado. Un proceso finished conserva el resultado numérico completo.
La división es real y el residuo sigue las reglas de Python: `-8 % 3 = 1` y
`8 % -3 = -1`. El redondeo de la división a un máximo de 4 decimales corresponde
a la presentación; no cambia el resultado guardado.

## Adaptación a la API

El snapshot usa los campos de la página 15 del manual:
`estado`, `reloj`, `lote_actual`, `lotes_pendientes`, `total_trabajos`,
`en_ejecucion`, `en_espera` y `terminados`. Cada proceso incluye ID, lote,
estado, operación, operandos, TME, ejecutado, restante y resultado.

`en_espera` contiene solo el lote activo. Los lotes pendientes excluyen ese
lote. Al terminar: `lote_actual=null`, `en_ejecucion=null`, `en_espera=[]` y
`lotes_pendientes=0`. Los terminados se conservan en orden de terminación.

El servicio agrega el ID externo sin modificar el motor:

```python
respuesta = {"simulacion_id": simulacion_id, **motor.snapshot()}
```

El integrante 2 debe implementar:

1. Modelos de entrada estrictos y rutas create, GET y actions del manual.
2. Almacenamiento de motores por ID, con un bloqueo por simulación.
3. Un reloj del servidor que invoque `tick()` una vez por segundo real.
4. El mismo bloqueo para tick, acciones y lectura del snapshot.
5. Respuestas 422 para entradas inválidas, 404 para IDs ausentes y 409 para
   `SimulationStateError`, usando su mensaje como `detail`.
6. Pruebas de API con el reloj automático desactivable desde el servicio.

Mapa de acciones: `interrupt → interrupt()`, `error → fail()`,
`pause → pause()`, `continue → resume()`.

GET únicamente consulta; no debe llamar a tick. El motor no es seguro para
acceso concurrente por sí solo: la exclusión mutua pertenece al servicio.
Usar un proceso servidor y conservar el estado en memoria, conforme al manual.
No exponer un endpoint público de tick.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_engine.py -q
```

Verificado con Python 3.12.7: **41 pruebas aprobadas**. Incluyen N=1,3,4,7,
operaciones y generación válida, interrupciones con tiempo conservado,
errores, pausa, cambio de lote, final estable y snapshots independientes.
Las pruebas usan tiempo simulado; no requieren esperar segundos reales.

El motor y las pruebas pueden integrarse en la rama del integrante 2 mediante
el PR de `feature/i1-motor-lotes`, después de su revisión. No se ha realizado
commit, push ni merge como parte de esta entrega local.
