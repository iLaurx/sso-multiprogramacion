# Guía de integración frontend — Actividad 6

Revisión del 4 de noviembre de 2026 sobre `feature/fcfs`. Esta guía describe la API implementada; no acredita que la pantalla ya esté adaptada. Referencias: [contrato HTTP](contrato-api.md), [campos del motor](cambios-backend-fcfs.md) y [estado vigente](../estado.md).

## Peticiones y ciclo de pantalla

Enviar JSON con `Content-Type: application/json`. Las rutas son relativas al mismo servidor:

| Método y ruta | Cuerpo | Respuesta |
| --- | --- | --- |
| GET `/api/health` | Ninguno | 200, `{"status":"ok"}`. |
| POST `/api/simulations` | `{"numero_trabajos":4,"seed":123}` | 201, estado inicial completo. `seed` puede omitirse o ser null. |
| GET `/api/simulations/{simulacion_id}` | Ninguno | 200, estado completo actual. |
| POST `/api/simulations/{simulacion_id}/actions` | `{"accion":"interrupt"}` | 200, estado completo después de aplicar la acción. |

`numero_trabajos` debe ser entero positivo y `seed`, entero o null; no se aceptan booleanos, cadenas ni decimales como enteros. Guardar el ID que devuelve creación y usarlo en consultas y acciones. Cada respuesta correcta contiene el mismo esquema completo: reemplazar el estado mostrado con esa respuesta. Serializar peticiones desde la pantalla para evitar que una respuesta antigua sobrescriba otra más reciente.

El servidor lleva el único reloj, con una espera de un segundo entre ticks automáticos; no se garantiza sincronización exacta con el reloj de pared. GET no genera ticks, aunque dos consultas pueden diferir si el reloj del servidor avanzó entre ellas. No hay ruta pública de tick. `tick_once` se utiliza internamente en pruebas y en la reproducción de los ejemplos de esta guía.

Las simulaciones viven en memoria, requieren un solo worker y se pierden al reiniciar. Ante 404 al recuperar un ID, informar que ya no existe y permitir una nueva creación. No hay ruta de borrado ni persistencia implementada.

## Controles

| Tecla | `accion` | Efecto y disponibilidad |
| --- | --- | --- |
| I | `interrupt` | Con running y CPU presente: bloquea el proceso durante 10 segundos simulados. Conserva servicio y espacio de memoria. |
| E | `error` | Con running y CPU presente: termina por error, conserva servicio real y libera espacio para admitir nuevos. |
| P | `pause` | Pausa reloj, servicio, espera y bloqueos; también funciona con CPU libre. Repetir en paused es válido. |
| C | `continue` | Reanuda; repetir en running es válido. |

Las acciones no consumen segundos por sí mismas. Tras completed se rechazan las cuatro. No hay controles de actividad 8.

404 significa ID inexistente; 409, acción incompatible con el estado actual; 422, cuerpo inválido o acción desconocida. Los primeros dos devuelven `{"detail":"texto"}`; la validación puede devolver una lista en `detail`. No asumir que `detail` siempre es cadena. Al recibir 409, consultar el estado para actualizar controles; no modificar tiempos ni colas localmente. Manejar errores de red sin presentar la acción como aplicada.

## Estado y representación de procesos

| Campo superior | Representación |
| --- | --- |
| `simulacion_id` | Cadena UUID generada por el servicio; diferente en cada creación. |
| `estado` | `running`, `paused` o `completed`. |
| `reloj` | Segundos simulados enteros del servidor. |
| `total_trabajos` | Cantidad inicial fija. |
| `nuevos` | Lista de procesos con `estado: "new"`, fuera de memoria y en orden de admisión. Mostrar cantidad con `.length`. |
| `en_espera` | Lista de procesos `ready`, en orden FCFS. Mostrar como listos sin ordenar por ID. |
| `en_ejecucion` | Objeto `running` o null. En pausa el proceso puede conservar `estado: "running"`; la pausa pertenece al estado superior. |
| `bloqueados` | Lista de procesos `blocked`, en orden de bloqueo. Siguen ocupando memoria. |
| `terminados` | Lista de procesos `finished` o `error`, en orden de terminación. |
| `memoria_ocupada` | Entero de 0 a 3: CPU + listos + bloqueados. |

No existen `lote`, `lote_actual` ni `lotes_pendientes` en la respuesta. Todos los procesos están representados entre esas listas y CPU. Al terminar uno se admite el siguiente nuevo al final de listos. Al desbloquearse vuelve al final de listos; no recibe servicio en el tick de desbloqueo. Respetar el orden recibido también en terminados.

**CPU null no significa finalización.** Con running y bloqueados presentes deben continuar las consultas y P/C. Solo completed indica cierre: nuevos, listos y bloqueados vacíos, CPU null y memoria 0; terminados y reloj permanecen disponibles.

## Datos y tiempos de cada proceso

| Campo | Tipo y significado |
| --- | --- |
| `id` | Entero único dentro de la simulación. |
| `estado` | `new`, `ready`, `running`, `blocked`, `finished` o `error`. |
| `operacion` | `+`, `-`, `*`, `/` o `%`. |
| `operando_a`, `operando_b` | Enteros de la operación. |
| `tme` | Entero de 7 a 18, tiempo máximo estimado. |
| `ejecutado` | Entero: servicio real acumulado de CPU. No hay otro campo `servicio`. |
| `restante` | TME menos servicio mientras vive; cero al terminar, también por error. |
| `resultado` | Número en finished; null mientras vive o en error. Mostrar ERROR según estado, no según ausencia de resultado. |
| `llegada` | Instante de admisión a memoria; null en nuevos. No es el instante de creación. |
| `primera_atencion` | Instante del primer despacho; null hasta recibir CPU. No se reinicia al desbloquearse. |
| `finalizacion` | Instante de terminación normal o por error; null antes. |
| `retorno` | Finalización menos llegada; null hasta terminar. |
| `respuesta` | Primera atención menos llegada; null hasta el primer despacho. |
| `espera` | Acumulado solo en listos. Excluye nuevos, CPU y bloqueo. |
| `bloqueado` | Acumulado de todos los bloqueos, incluido el actual. |
| `inicio_bloqueo` | Instante del bloqueo actual; null fuera de blocked. |
| `bloqueo_transcurrido` | Solo en objetos de `bloqueados`: segundos del bloqueo actual. |
| `bloqueo_restante` | Solo en objetos de `bloqueados`: segundos para completar los 10 del bloqueo actual. |

Todos los tiempos son segundos simulados enteros, salvo los instantes o duraciones derivadas desconocidos que se envían como null. Cero es válido: usar `valor === null` o `valor ?? "—"`, evitando `valor || "—"`. En un terminado se cumple `retorno = espera + ejecutado + bloqueado`. La pantalla recibe los cálculos hechos: no debe recalcularlos ni completar servicio hasta TME cuando ocurre error.

## Comprobaciones y pendientes

En esta revisión se repitieron las pruebas de API/servicio y la suite completa; resultados y comandos en [estado.md](../estado.md). Los tests HTTP usan `TestClient`, con reloj automático desactivado y ticks internos deterministas. La tarea automática se prueba aparte con pulsos controlados de su espera. Esto comprueba lógica y transporte HTTP en proceso, sin acreditar un despliegue ni un recorrido de navegador con segundos reales.

Falta adaptar y verificar visualmente paneles, controles I/E/P/C, nuevos, memoria, orden FCFS, bloqueo, CPU libre, pausa, error, tabla final y recuperación del ID tras recarga. No se modificaron motor, frontend ni implementación de API/servicio en esta revisión documental.

## Respuestas HTTP reales

Las respuestas siguientes se capturan con `TestClient(create_app(auto_clock=False))`, sin reemplazar el generador. Los UUID son reales de esa ejecución y cambiarán al reproducirla. Los avances indicados se hacen con `tick_once` desde la prueba, nunca mediante una ruta pública. Cada bloque muestra la respuesta completa.

### 1. Nuevos y listos al crear

POST `/api/simulations`, cuerpo `{"numero_trabajos":4,"seed":123}`.

HTTP 201

```json
{
  "simulacion_id": "799645e2-3a1d-4474-99e0-67f6f49bcc07",
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

### 2. CPU libre y proceso bloqueado

Nueva simulacion de un proceso con seed 123; dos ticks internos, POST actions `{"accion":"interrupt"}`, tres ticks internos y GET del ID creado.

HTTP 200

```json
{
  "simulacion_id": "42c814fa-a370-4dbe-8552-9b7b267cbf9e",
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

### 3. Terminado por error con servicio real

Continuar el ejemplo 2 con siete ticks internos (desbloqueo en reloj 12) y POST actions `{"accion":"error"}`.

HTTP 200

```json
{
  "simulacion_id": "42c814fa-a370-4dbe-8552-9b7b267cbf9e",
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

### 4. Terminado normalmente

Nueva simulacion de un proceso con seed 123, siete ticks internos y GET del ID creado.

HTTP 200

```json
{
  "simulacion_id": "60e2d0ef-c986-4bda-9ef8-3830be8e22df",
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
## Contrato API Actualizado (Procesos Dinámicos y BCP)

### 1. Rutas y Acciones (`POST /api/simulations/{simulacion_id}/actions`)
El cuerpo de la petición recibe `{"accion": "<nombre>"}` con las siguientes acciones válidas:
- `"add_process"` (Tecla **N** en interfaz): Crea un nuevo proceso dinámicamente bajo el bloqueo del servidor y devuelve el snapshot actualizado.
  - Si `memoria_ocupada < 3`, entra directamente a `en_espera` (o `en_ejecucion` si la CPU estaba libre) con `llegada = reloj`.
  - Si `memoria_ocupada == 3` (memoria llena), se conserva en `nuevos` con `estado: "new"` y sus tiempos (`llegada`, `primera_atencion`, `finalizacion`, `retorno`, `respuesta`) en `null`.
- `"pause"` (Teclas **P** o **B** en interfaz): Pausa el reloj de forma atómica bajo el mismo candado (`lock`) y devuelve el snapshot congelado para construir la tabla **BCP** reuniendo `nuevos`, `en_espera`, `en_ejecucion`, `bloqueados` y `terminados`.
- `"continue"` (Tecla **C** en interfaz): Reanuda la simulación desde el estado pausado.
- `"interrupt"` (Tecla **E** en interfaz): Envía el proceso en CPU a `bloqueados` durante 9 segundos simulados (`bloqueo_transcurrido` y `bloqueo_restante` incluidos en cada proceso bloqueado).
- `"error"` (Tecla **W** en interfaz): Termina el proceso activo por error (`estado: "error"`, `resultado: null`, `finalizacion = reloj`).

### 2. Reglas de Validación y Errores HTTP
- **HTTP 200 / 201**: Operación exitosa; devuelve el snapshot completo con `simulacion_id`.
- **HTTP 404**: `simulacion_id` no existe.
- **HTTP 409 (`SimulationStateError`)**: Acción incompatible con el estado actual:
  - Intentar `"add_process"`, `"interrupt"` o `"error"` cuando la simulación está en `"paused"`.
  - Intentar `"interrupt"` o `"error"` cuando `en_ejecucion` es `null` (todos los residentes bloqueados).
  - Intentar cualquier acción cuando la simulación está en `"completed"`.
- **HTTP 422**: Cuerpo JSON inválido o nombre de acción desconocido.

### 3. Ejemplos Reales de Estado en el Snapshot
- **Proceso nuevo (memoria llena)**:
  `{"id": 5, "operacion": "+", "operando_a": 4, "operando_b": 2, "tme": 8, "estado": "new", "resultado": null, "llegada": null, "primera_atencion": null, "finalizacion": null, "retorno": null, "respuesta": null, "espera": 0, "ejecutado": 0, "bloqueado": 0}`
- **Proceso bloqueado**:
  `{"id": 1, "estado": "blocked", "llegada": 0, "primera_atencion": 0, "finalizacion": null, "retorno": null, "respuesta": 0, "espera": 0, "ejecutado": 2, "bloqueado": 3, "bloqueo_transcurrido": 3, "bloqueo_restante": 6}`
- **Proceso terminado normal / error**:
  `{"id": 2, "estado": "finished", "resultado": 12, "llegada": 0, "primera_atencion": 2, "finalizacion": 9, "retorno": 9, "respuesta": 2, "espera": 2, "ejecutado": 7, "bloqueado": 0}`
  *(En terminación por `"error"`, `estado` es `"error"` y `resultado` es `null`).*