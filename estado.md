# Estado del proyecto

Última actualización: 4 de noviembre de 2026.

## Situación actual

**Motor y API/servicio FCFS de actividad 6 comprobados en las pruebas descritas abajo. Sigue frontend.** Rama comprobada: `feature/fcfs`. Esta revisión comenzó con cambios locales de la integración anterior y los conservó. Sin commit, push ni despliegue.

- Motor: no se modificó `simulation/`; no se encontró un fallo que requiriera corregirlo.
- API: conserva las rutas, validaciones y acciones existentes. Devuelve el snapshot completo agregando únicamente `simulacion_id`, con orden y null intactos. GET no llama tick.
- Servicio (`backend/service.py`): conserva reloj y lock por simulación. Termina la tarea automática al completar el último tick y rechaza acciones desconocidas en llamadas internas con ValueError (HTTP sigue devolviendo 422 por validación).
- Ejemplos: `docs/contrato-api.json` y `docs/fixtures/motor-inicial.json` reemplazados por salidas reales FCFS con cuatro procesos y seed 123. UUID HTTP generado realmente y variable; reproducción comprobada excluyendo solo ese ID.
- Documentación actualizada: `docs/contrato-api.md`, `docs/entrega-motor.md`, `docs/cambios-backend-fcfs.md`, `README.md`, `AGENTS.md` y este estado. Las revisiones anteriores de la guía del motor son evidencia histórica; este archivo contiene la situación vigente.

## Comprobaciones

En esta revisión solo se editaron documentos. Se contrastaron rutas, esquemas, servicio y pruebas. Se añadió [la guía de frontend](docs/guia-frontend-fcfs.md), con rutas, controles, campos, tiempos, errores y cuatro respuestas HTTP completas capturadas con TestClient y comparadas contra el motor real. Se actualizaron contrato y entrega para distinguir lo comprobado de los pendientes visuales.

`tests/test_api_fcfs.py` agrega recorridos HTTP completos contrastados contra el motor, tiempos conocidos, memoria/admisión normal y por error, orden de colas, null/cero, tres bloqueados, CPU libre, límite exacto de 10 segundos, pausa con CPU y con todos bloqueados, controles rechazados sin cambios, consultas repetidas, finalización, aislamiento/concurrencia y copias independientes. También comprueba la tarea automática con pulsos controlados de su espera y reproducción de ambos JSON.

- API/servicio: 23 pruebas aprobadas al repetir `.\.venv\Scripts\python.exe -m pytest -q tests/test_api.py tests/test_service.py tests/test_api_fcfs.py`.
- Suite completa: **105 aprobadas** con `.\.venv\Scripts\python.exe -m pytest -q`.
- `git diff --check`: sin errores.
- Avisos existentes: deprecación Starlette/HTTPX y permisos de caché pytest; no fallos de pruebas.
- No se verificó el recorrido de navegador con reloj real ni la interfaz FCFS. No se modificó frontend.

## Para el compañero de frontend

Empezar por [guia-frontend-fcfs.md](docs/guia-frontend-fcfs.md), que incluye las respuestas completas y sus secuencias de reproducción.

Usar [contrato-api.md](docs/contrato-api.md) y sus ejemplos FCFS. Se mantienen rutas y acciones interrupt/error/pause/continue. `en_espera` es listos en orden FCFS; mostrar nuevos desde `nuevos.length`, memoria desde `memoria_ocupada` (máximo 3) y bloqueos actuales desde `bloqueo_transcurrido`/`bloqueo_restante`. `bloqueado` es acumulado, `ejecutado` es servicio y error se presenta como ERROR aunque resultado sea null.

CPU null con running y bloqueados es válido: continuar consultando hasta completed. Tomar todos los tiempos del servidor y distinguir null de cero. No usar lote/lote_actual/lotes_pendientes ni recalcular tiempos. Falta adaptar paneles, controles I/E/P/C y tabla final, y comprobar visualmente nuevos, bloqueo, CPU libre, pausa, error, final normal y recarga. Solo actividad 6; nada de actividad 8.
