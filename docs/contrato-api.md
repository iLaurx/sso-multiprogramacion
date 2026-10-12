# Contrato propuesto de simulación

Basado en las páginas 5 y 13-16 del manual. El equipo debe revisar cualquier
cambio entre los tres módulos. Solo `GET /api/health` está implementado en la
base actual; las demás rutas se implementan durante la fase de API.

## Motor → backend

El motor puro `SimulationEngine` expone:

- `create(numero_trabajos, seed=None)`: construye un motor en `running`, reloj 0.
- `tick()`: avanza exactamente un segundo simulado cuando está en `running`.
- `interrupt()`: reencola el actual al final del mismo lote y conserva su tiempo.
- `fail()`: termina el proceso actual por error.
- `pause()` y `resume()`: detienen y reanudan el avance.
- `snapshot()`: devuelve datos serializables sin modificar el estado.

El motor no importa FastAPI ni usa esperas reales. El backend adapta su snapshot
al JSON compartido y es la única autoridad del reloj. Un ciclo del servidor
avanza una vez por segundo; consultar el estado no avanza el tiempo. El servicio
protege los ticks, acciones y snapshots con el mismo bloqueo por simulación.

## Backend → frontend

| Método y ruta | Entrada | Respuesta correcta |
| --- | --- | --- |
| `GET /api/health` | Ninguna | 200: `{"status":"ok"}`. |
| `POST /api/simulations` | `{"numero_trabajos":4,"seed":123}`; seed opcional. | 201: snapshot inicial completo. |
| `GET /api/simulations/{id}` | ID de simulación. | 200: snapshot, sin avanzar el reloj. |
| `POST /api/simulations/{id}/actions` | `{"accion":"interrupt"}`. | 200: snapshot tras la acción. |

Acciones: `interrupt` (I), `error` (E), `pause` (P), `continue` (C).
No hay endpoint público de tick.

## Errores

- 422: cantidad no entera o no positiva, acción inválida o JSON inválido. La
  cantidad usa validación estricta: rechazar booleanos y decimales.
- 404: ID de simulación inexistente.
- 409: I/E sin proceso activo, durante pausa o después del final; C después
  de `completed`.
- P en `paused` y C en `running` devuelven el estado sin cambios.

Los errores controlados usan `{"detail":"Descripción del error"}`; la
validación puede devolver `detail` como lista. El frontend acepta ambos formatos.

## Snapshot compartido

El ejemplo completo está en [contrato-api.json](contrato-api.json). Es un fixture
ilustrativo con cuatro trabajos y reloj 2; no es una respuesta real ni la salida
garantizada de `seed=123`. El trabajo 4 pertenece al lote siguiente.

| Campo | Tipo y significado |
| --- | --- |
| `simulacion_id` | Cadena que identifica la simulación. |
| `estado` | `running`, `paused` o `completed`. |
| `reloj` | Entero, segundos simulados acumulados. |
| `lote_actual` | Número de lote, o `null` al finalizar. |
| `lotes_pendientes` | Entero; excluye el lote activo y vale 0 al finalizar. |
| `total_trabajos` | Entero positivo inicial. |
| `en_ejecucion` | Proceso actual, o `null`. |
| `en_espera` | Lista de procesos `ready` del lote actual, en orden de cola. |
| `terminados` | Procesos de todos los lotes en orden de terminación. |

Cada proceso incluye `id`, `lote`, `estado`, `operacion`, `operando_a`,
`operando_b`, `tme`, `ejecutado`, `restante` y `resultado`. IDs, lotes, operandos
y tiempos son enteros. Operaciones: `+`, `-`, `*`, `/`, `%`.

Estados de proceso: `ready`, `running`, `finished`, `error`. El resultado es
`null` mientras vive o si termina por error, y numérico al finalizar normalmente.
La pantalla muestra ERROR según el estado `error`. Para procesos vivos,
`restante = tme - ejecutado`; cualquier terminado tiene restante 0, sin alterar
artificialmente su ejecutado. En `completed`, el actual y lote son `null`, la
espera queda vacía y se conservan reloj y terminados.

## Reglas propuestas para coordinar

- IDs consecutivos desde 1, lotes de hasta 3 y TME aleatorio inclusivo de 7 a 18.
- Operandos enteros de -99 a 99, segundo operando distinto de 0 en `/` y `%`.
  División real y residuo de Python; mostrar hasta cuatro decimales sin cambiar
  el valor calculado.
- I mueve el actual al final del mismo lote, conservando ejecutado/restante.
  I/E no suman tiempo al reloj. En pausa solo C reanuda; al finalizar se crea
  otra simulación para volver a iniciar.
- El frontend guarda el ID en `sessionStorage`, consulta aproximadamente cada
  segundo y serializa consultas y acciones. No calcula tiempos por su cuenta.
- El servidor mantiene estado en memoria y usa un solo worker. Una recarga del
  navegador conserva el ID; reiniciar el servidor elimina las simulaciones.

El rango de operandos, formato de resultados y estas decisiones web son
propuestas del manual. Antes de la entrega se deben confirmar las condiciones
adicionales del Programa 1 con la docente.
