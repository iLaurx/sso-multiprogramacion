# Estado del proyecto

Última actualización: 3 de noviembre de 2026.

## Entrega del motor

**Motor FCFS de la actividad 6 de Sistemas Operativos terminado para entregar a API en el alcance revisado.** Rama comprobada: `feature/fcfs`; árbol limpio al comenzar. No se encontraron fallos funcionales en los casos comprobados. Commit de la entrega autorizado por el usuario. El push a origin/feature/fcfs requiere verificación del destino por revisión automática. No se hizo despliegue.

Quedaron comprobados procesos y operaciones, nuevos y listos FCFS, admisión continua, máximo tres residentes contando CPU y bloqueados, I de 10 segundos, E con servicio real, pausa completa, reloj con CPU libre y cierre solo al terminar todos. Llegada se registra al admitir a memoria; primera atención no se reinicia; finalización, retorno, respuesta y espera respetan `fcfs.md`. Servicio y bloqueo se cuentan por separado.

`snapshot()` devuelve colas, CPU, terminados, memoria y tiempos, sin campos de lotes. Se verificaron null para instantes desconocidos, JSON serializable, copias independientes y consultas sin avance. Los bloqueados incluyen duración actual y restante además del acumulado.

## Qué se cambió en esta revisión

- `tests/test_fcfs_handoff.py`: 15 secuencias mixtas reproducibles que comprueban identidad y conservación de procesos, capacidad, estados, partición de tiempos, primera atención estable, pausas, controles rechazados y finalización.
- `simulation/__init__.py`: descripción corregida de lotes a FCFS. No fue necesario cambiar la lógica ni el snapshot del motor.
- `docs/cambios-backend-fcfs.md`: entrega con métodos, esquema, cuatro ejemplos reales verificados, resultados de pruebas, punto de entrada para API y distinción entre fallos de motor e incompatibilidades del contrato anterior.
- Este archivo: estado vigente de la entrega.

## Comprobaciones

- Pruebas específicas de motor (`test_engine.py`, `test_models.py`, `test_times.py`, `test_snapshot_fcfs.py` y `test_fcfs_handoff.py`): **79 aprobadas**.
- Suite completa `.\.venv\Scripts\python.exe -m pytest -q`: **94 aprobadas**, incluidas las pruebas existentes de API/servicio.
- Los cuatro snapshots de la guía coinciden exactamente con las secuencias ejecutadas en el motor con seed 123. Las pruebas de casos conocidos y bloqueos simultáneos, escalonados y repetidos siguen pasando.
- Persisten avisos de permisos de caché de pytest y de deprecación Starlette/HTTPX en la suite completa. No hubo fallos. La validación visual y el recorrido HTTP completo con reloj real no se realizaron en esta revisión.

## Por dónde empieza el compañero de API

1. Leer [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md), especialmente los métodos, el esquema y los ejemplos. No tomar `docs/contrato-api.md` ni su JSON anterior como contrato FCFS.
2. Revisar el recorrido ya conectado en rutas y servicio: este agrega `simulacion_id` y transmite snapshot. Actualizar documentación y consumidores que todavía dependan de campos de lotes; admitir estados new/blocked, tiempos null y CPU null con running.
3. Verificar mapeo interrupt/error/pause/continue a interrupt/fail/pause/resume, conflictos I/E sin CPU y reloj que continúa con bloqueados pero se congela en pausa. No recalcular tiempos ni planificar en API.
4. Después coordinar frontend y probar el recorrido completo. La pantalla todavía espera lotes; no se considera adaptada por pasar la suite.

No queda un fallo conocido del motor que impida esta entrega. La permanencia interna de `lote` en Process/generador es compatibilidad temporal sin uso en FCFS ni exposición pública. README y contrato anterior siguen pendientes de actualización por sus áreas.

No se modificaron API, servicio ni frontend. No se cambió el plan de `fcfs.md` ni se implementó o preparó actividad 8.
