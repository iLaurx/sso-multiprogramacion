# Estado del proyecto

Última actualización: 4 de noviembre de 2026.

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
