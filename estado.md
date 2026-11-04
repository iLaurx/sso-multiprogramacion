# Estado del proyecto

Última actualización: 3 de noviembre de 2026.

## Dónde estamos

Primer paso de la actividad 6 de **Sistemas Operativos** terminado: el modelo tiene los datos para FCFS. El motor sigue funcionando por lotes; todavía no registra los tiempos nuevos.

- Rama comprobada: `feature/fcfs`. El árbol estaba limpio al comenzar.
- El usuario confirmó que conservó la versión anterior con un tag y una release; sus nombres y publicación no se verificaron aquí.
- Alcance exclusivo de actividad 6. No se implementó ni preparó actividad 8.

## Qué quedó hecho

- `simulation/models.py`: se agregaron los estados `new` y `blocked`, conservando los anteriores y `ready` como valor inicial para mantener compatible el motor actual.
- Instantes `llegada`, `primera_atencion`, `finalizacion` e `inicio_bloqueo`: comienzan en `None`; cero es un instante válido. Llegada corresponde al ingreso a memoria.
- Duraciones `espera` y `bloqueado`: comienzan en cero. Espera acumulará solo el tiempo en listos; bloqueado, el tiempo total de E/S entre bloqueos. `inicio_bloqueo` permitirá medir el bloqueo actual y deberá volver a `None` al salir de él.
- `ejecutado` conserva el tiempo de servicio, sin un contador duplicado. `lote` permanece temporalmente.
- `tests/test_models.py`: pruebas de valores iniciales del generador, estados nuevos, conservación de servicio y restante, instante cero y contrato de `Process.snapshot()`.

## Comprobaciones

- Se revisaron modelo, generador, motor, README y pruebas existentes.
- `.\.venv\Scripts\python.exe -m pytest -q`: **60 pruebas aprobadas**. Avisos de deprecación de Starlette/HTTPX y de permisos al escribir la caché de pytest; no hubo fallos.
- No se cambiaron colas, motor, generador, `snapshot()`, API ni frontend. Los datos nuevos son internos y aún no se actualizan durante la simulación.
- Commit local autorizado por el usuario. No se hizo push ni despliegue.

## Siguiente paso y coordinación

| Área | Situación actual | Pendiente |
| --- | --- | --- |
| Motor/backend | Modelo preparado; ejecución todavía por lotes. | Adaptar a FCFS con nuevos, listos y bloqueados, máximo tres procesos en memoria, bloqueo de 10 segundos y actualización de tiempos. |
| API | Sin cambios en rutas ni respuestas. | Esperar el motor terminado y una guía con métodos, campos y ejemplos reales. |
| Frontend | Conserva la pantalla de lotes. | Adaptar después de definir los datos del motor y la API. |

Falta comprobar las transiciones FCFS, admisión, pausa completa, CPU libre con bloqueados, errores y tiempos cuando se implemente el motor. Los nuevos campos no son todavía parte del contrato público. `docs/contrato-api.md` describe la versión anterior; `fcfs.md` sigue siendo el plan, no el contrato final. Revisar rama y cambios ajenos antes de continuar.
