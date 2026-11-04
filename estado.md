# Estado del proyecto

Última actualización: 3 de noviembre de 2026.

## Dónde estamos

Actividad 6 de **Sistemas Operativos**, rama comprobada `feature/fcfs`. El motor usa nuevos y listos con admisión continua, máximo tres residentes y bloqueo real de 10 segundos simulados. Se conservaron los cambios locales de la etapa anterior. Commit local autorizado por el usuario para los cambios de FCFS y bloqueo. No se hizo push ni despliegue.

## Qué quedó hecho

- `simulation/engine.py`: `interrupt()` mueve el proceso activo a bloqueados, registra `inicio_bloqueo` y despacha al siguiente listo sin avanzar el reloj. El bloqueado conserva `ejecutado`, llegada y su espacio en memoria.
- Cada tick suma servicio al proceso que ya estaba en CPU y un segundo de `bloqueado` a cada proceso en E/S. Al cumplirse 10 segundos desde `inicio_bloqueo`, vuelve al final de listos y limpia ese instante con `None`. El acumulado se conserva entre bloqueos repetidos.
- El reloj y los bloqueos avanzan también sin CPU activa. Los recién desbloqueados pueden ser despachados al cerrar el tick, pero empiezan a consumir servicio en el siguiente. Pausa congela reloj, CPU y bloqueos. La simulación no termina mientras queden bloqueados.
- Orden en un mismo instante: los desbloqueados se agregan detrás de los listos existentes, en orden de bloqueo; si también termina la CPU, el nuevo admitido se agrega después de esos desbloqueados. No se desaloja a la CPU activa.
- `simulation/models.py`: comentario actualizado para indicar que ya se acumula tiempo bloqueado; no cambió su estructura ni `Process.snapshot()`.
- `tests/test_engine.py`: adaptadas las pruebas de interrupción y las invariantes para incluir CPU ociosa; pruebas de duración exacta, retorno FCFS, memoria, CPU libre, pausa cerca del vencimiento, bloqueos repetidos, simultáneos y escalonados, y coincidencia de desbloqueo con finalización.
- `tests/test_api.py`: se ajustaron las expectativas de la prueba de acciones al nuevo comportamiento del motor; no se editaron archivos de API.

## Comprobaciones

- Se revisaron AGENTS.md, fcfs.md, estado anterior, README, modelo, motor y pruebas correspondientes.
- `.\.venv\Scripts\python.exe -m pytest -q`: **68 pruebas aprobadas**, incluidas API y servicio. Persisten avisos de deprecación Starlette/HTTPX y permisos de caché de pytest; no hubo fallos.
- Se comprobó que bloquear tres residentes no admite un cuarto nuevo, que el desbloqueo no consume servicio en ese mismo tick y que la pausa conserva también los datos internos del bloqueo.

## Datos y coordinación con API/frontend

- No se modificaron `backend/` ni `frontend/`. Se conservan métodos y claves del snapshot de la etapa anterior: `estado`, `reloj`, `nuevos`, `bloqueados`, `memoria_ocupada`, `total_trabajos`, `en_ejecucion`, `en_espera` y `terminados`.
- La API transmite directamente ese snapshot: `interrupt` ahora devuelve el proceso en `bloqueados` con estado `blocked`. Si todos están bloqueados, `en_ejecucion` es `None` y el estado sigue `running`; I/E sin CPU activa se rechazan, P/C siguen disponibles.
- `Process.snapshot()` todavía no expone llegada, inicio de bloqueo ni tiempos acumulados. `lote` permanece como metadato temporal y no participa en la planificación.
- La pantalla todavía espera los campos de lotes retirados en la etapa anterior y no representa correctamente FCFS ni bloqueados. Las pruebas aprobadas no son una validación visual.

## Qué sigue pendiente

- Registrar primera atención, finalización y espera; llegada, servicio y tiempo bloqueado ya se actualizan. Definir la exposición de tiempos de retorno y respuesta con las reglas de `fcfs.md`.
- Completar las pruebas de tiempos, preparar la guía real del backend y después adaptar API y pantalla. README y `docs/contrato-api.md` siguen describiendo lotes; `fcfs.md` es el plan, no el contrato final.

Solo actividad 6. No se implementó ni preparó actividad 8. Revisar rama y cambios locales antes de continuar.
