# Estado del proyecto

Última actualización: 3 de noviembre de 2026.

## Dónde estamos

Actividad 6 de **Sistemas Operativos**, rama comprobada `feature/fcfs`. Motor FCFS con tres residentes, bloqueo de 10 segundos, tiempos y salida pública preparados para revisar la integración. Se conservaron los cambios locales de tiempos de la etapa anterior. Commit local autorizado por el usuario para todos los cambios pendientes de tiempos, snapshot y guía FCFS. No se hizo push ni despliegue.

## Qué quedó hecho

- `simulation/models.py`: `Process.snapshot()` expone llegada, primera atención, finalización, retorno, respuesta, espera, bloqueo acumulado e inicio del bloqueo actual. Conserva identidad, operación, operandos, TME, ejecutado como servicio real, restante, resultado y estado. Elimina `lote` de la salida; permanece internamente por compatibilidad con el constructor y generador, sin uso en la planificación.
- `simulation/engine.py`: snapshot con nuevos, listos mediante `en_espera`, CPU, bloqueados, terminados y memoria ocupada. No devuelve campos de lotes. Las entradas de bloqueados agregan `bloqueo_transcurrido` y `bloqueo_restante` del bloqueo actual, calculados desde el reloj sin modificar el motor. `bloqueado` sigue siendo el acumulado entre bloqueos.
- Se conservan los tiempos ya implementados: llegada al admitir, primera atención solo al primer despacho, finalización normal o por error, espera solo en listos, servicio real y bloqueo separado. Retorno/respuesta se calculan sin contadores duplicados; instantes desconocidos se devuelven como null.
- `docs/cambios-backend-fcfs.md`: guía de métodos, campos conservados/agregados/eliminados, reglas de reloj, errores, cuatro ejemplos completos generados por el motor y pendientes de integración.
- `tests/test_models.py` y `tests/test_times.py`: contrato adaptado a los tiempos públicos y eliminación de lote. `tests/test_snapshot_fcfs.py`: bloqueos repetidos, pausa, copias independientes, tiempos finales conocidos y reproducción exacta de los JSON de la guía. Se mantienen las pruebas de tiempos de la etapa anterior.

## Comprobaciones

- Se revisaron AGENTS.md, fcfs.md, estado previo, README, motor, modelo, generador, servicio y contrato anterior.
- `.\.venv\Scripts\python.exe -m pytest -q`: **79 pruebas aprobadas**, incluidas API y servicio. Avisos de deprecación Starlette/HTTPX y permisos de caché de pytest; sin fallos.
- Se comprobaron JSON serializable, ausencia de campos de lotes, copias que no alteran el motor, consultas sin avance, pausa de datos internos y públicos, bloqueo actual separado del acumulado y tiempos de casos conocidos. Los cuatro ejemplos documentados coinciden con el motor usando seed 123.

## Coordinación y siguiente paso

- No se editaron `backend/` ni `frontend/`. El servicio existente ya llama al motor, agrega `simulacion_id` y transmite el snapshot: sus respuestas reflejan automáticamente este esquema. `contrato-api.md` está desactualizado, incluso al afirmar que solo health está implementado.
- Revisar la integración y documentación de API con [la guía nueva](docs/cambios-backend-fcfs.md); después adaptar la pantalla y comprobar el recorrido visual. La pantalla sigue esperando lote, lote_actual y lotes_pendientes; todavía no representa correctamente FCFS. README y ejemplos anteriores también requieren actualización en su etapa.
- No queda una función del motor solicitada en este paso pendiente. La integración formal y validación visual no se dan por terminadas con las pruebas automatizadas.
- Se mantiene el plan de `fcfs.md`; solo actividad 6, sin implementar ni preparar actividad 8.
