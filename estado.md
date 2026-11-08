# Estado del proyecto

## Actividad 10: motor Round Robin

En `feature/round-robin`, `simulation/engine.py` acepta un quantum entero
positivo, conserva el servicio entre turnos y expone `quantum` y `tiempo_turno`
en el snapshot (este último es null con CPU libre). El quantum predeterminado
es 1; corresponde al equipo de API decidir si lo exige al crear la simulación.
Si coinciden desbloqueo y vencimiento, el desbloqueado entra antes que el
proceso desalojado. La finalización tiene prioridad sobre el fin del turno.

Se actualizaron `tests/conftest.py`, `tests/test_engine.py`,
`tests/test_snapshot_fcfs.py`, `tests/test_times.py` y se agregó
`tests/test_round_robin.py`. La entrega y cuatro ejemplos reproducibles están
en `docs/entrega-motor-round-robin.md`. Las 114 pruebas del motor aprobaron y
`git diff --check` no señaló errores. Se intentó la suite completa, pero no
produjo salida y se interrumpió; no se acredita su resultado.

Queda integrar y verificar API, servicio y frontend: el servicio todavía no
recibe el quantum elegido y utiliza el valor predeterminado. No se modificaron
esas áreas. Los apartados anteriores de actividad 8 se conservan como contexto
histórico y no describen la planificación actual.

Última actualización: 8 de noviembre de 2026.

El 8 de noviembre se agregó `docs/actividad-10-round-robin.md`, versión Markdown del PDF de planificación de la actividad 10. Es documentación de los cambios propuestos; en este paso no se modificó la aplicación ni se ejecutaron pruebas.

También se agregó `docs/prompts-backend-round-robin.md`, con un prompt inicial para un orquestador de subagentes y cuatro pasos secuenciales para el motor. Son instrucciones propuestas; todavía no acreditan cambios ni pruebas del backend.

## Actividad 8: motor listo para integrar

Autorización de esta tarea: se reemplazó el límite anterior a actividad 6 solo
para adaptar el motor. Rama comprobada: `feature/fcfs-procesos-dinamicos`.
Se leyó la consigna original `C:/Users/ele/Downloads/Actividad 8 SSO.pdf`.

- `simulation/engine.py`: `add_process()` genera un proceso en running con ID
  único, actualiza el total, respeta nuevos FIFO y tres residentes. Bloqueo y
  restante cambian a 9 segundos. `processes_snapshot()` consulta todos los
  procesos por ID, con tiempos y copias independientes. El cierre incluye todas
  las altas; no se reabre completed y se rechazan altas en pausa.
- `simulation/generator.py`: generación individual compartida con la inicial y
  azar privado por simulación; conserva rangos válidos y semilla reproducible.
- Pruebas del motor: actualizadas `tests/test_engine.py`, `tests/test_times.py`,
  `tests/test_snapshot_fcfs.py`, `tests/test_fcfs_handoff.py` y fixture en
  `tests/conftest.py`; añadida `tests/test_dynamic_processes.py`.
- Documentación: contrato vigente en `docs/motor-actividad-8.md`; ejemplos
  reproducibles de `docs/cambios-backend-fcfs.md` ajustados a 9 segundos;
  `fcfs.md` señala el alcance autorizado y el contexto histórico de actividad 6.

## Comprobaciones

**92 pruebas del motor aprobadas** (79 existentes actualizadas y 13 nuevas):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_engine.py tests/test_models.py tests/test_times.py tests/test_snapshot_fcfs.py tests/test_fcfs_handoff.py tests/test_dynamic_processes.py
```

Se probaron 2000 altas reproducibles, datos válidos, IDs después de terminar
procesos, memoria llena/libre, CPU libre con bloqueados, orden de nuevos, pausa,
rechazos sin cambios, bloqueos repetidos y simultáneos, copias serializables,
partición de tiempos y cierre con altas en secuencias mixtas. Los cuatro JSON
actualizados de la guía coinciden con el motor real. `git diff --check` aprobado.

Se intentó la suite completa con `-m pytest -q --tb=short`, pero no devolvió
salida y se interrumpió. No se acredita una comprobación nueva de API/servicio
ni de navegador. Sus pruebas/fixtures de actividad 6 no se modificaron.

## Qué sigue para API

Conectar N a `add_process()` y consultar después el snapshot. Para B, pausar y
consultar `processes_snapshot()` bajo la misma exclusión mutua del servicio;
C continúa. Revisar acciones, contratos, fixtures y pruebas HTTP para actividad
8. E corresponde a `interrupt()` y W a `fail()`; el motor no interpreta teclas.
`total_trabajos` ya es acumulado. Preservar orden, tiempos y null; CPU libre no
significa final. Llegada sigue siendo admisión a memoria y espera solo listos.
Para nuevos, la presentación de campos nulos del BCP no debe borrar sus datos.

API, servicio y frontend no se modificaron. Su integración y verificación visual
con actividad 8 quedan pendientes; la integración local previa de actividad 6
no prueba las nuevas funciones. No se hizo commit, push, merge ni despliegue.

## Trabajo previo conservado

Se preparó `output/Texto_cambios_actividad_6.txt` para el reporte, con una explicación general del cambio de lotes a FCFS. En este paso solo se redactó el texto; no se modificó la aplicación ni se ejecutaron pruebas.

Se conservaron los archivos previos de `output/` sin modificarlos.
