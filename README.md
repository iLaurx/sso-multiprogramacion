# SSO · FCFS — Actividad 6

Simulador educativo de **Sistemas Operativos**, en adaptación de la aplicación de lotes a FCFS. Se conserva Python, FastAPI y HTML/CSS/JavaScript.

**Estado actual:** motor y API/servicio FCFS comprobados; falta adaptar la interfaz que sigue mostrando lotes. Ver [estado.md](estado.md).

## Para el siguiente desarrollador

Trabajamos sobre `feature/fcfs`. Antes de editar, comprobar la rama y los cambios locales; respetar el trabajo de los demás.

1. [AGENTS.md](AGENTS.md): alcance y reglas de trabajo.
2. [estado.md](estado.md): qué quedó terminado y qué sigue.
3. [docs/entrega-motor.md](docs/entrega-motor.md): tareas de integración por área y criterios para comprobarlas.
4. [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md): métodos del motor, campos y snapshots reales.
5. [docs/contrato-api.md](docs/contrato-api.md): rutas existentes, respuesta HTTP y diferencias con el contrato anterior.

[fcfs.md](fcfs.md) conserva las reglas. `Manual-instructions.md` es el manual anterior; los dos JSON en docs ya son ejemplos FCFS reproducibles.

## Comportamiento del motor implementado

- FCFS con nuevos, listos, un proceso en CPU, bloqueados y terminados.
- Máximo tres residentes: listos + CPU + bloqueados. Los demás esperan en nuevos.
- Cuando termina un proceso, se admite al siguiente nuevo al final de listos.
- I bloquea durante 10 segundos simulados, conserva servicio y memoria y después vuelve al final de listos.
- E termina por error con el servicio real. P/C detienen y continúan todos los tiempos.
- El reloj y los bloqueos avanzan con CPU libre; solo termina cuando todos los procesos han terminado.
- Llegada al ingresar a memoria, primera atención, finalización, retorno, respuesta, espera, servicio y bloqueo separado. Los instantes desconocidos son null.
- Snapshot independiente y serializable, sin campos públicos de lotes. La pantalla debe utilizar esos datos sin recalcular tiempos.

Solo actividad 6. No agregar funciones de actividad 8 ni un selector entre motores.

## Ejecución local

Requiere Python 3.12. Desde la raíz, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Si ya existe un entorno instalado, basta con ejecutar Uvicorn. Aplicación: [http://127.0.0.1:8000](http://127.0.0.1:8000). Documentación HTTP: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). La interfaz actual todavía necesita los cambios FCFS indicados arriba.

No requiere base de datos ni Node.js. Las simulaciones viven en memoria y se pierden al reiniciar el servidor, incluido un reinicio por `--reload`. Usar un solo worker. El servicio controla el reloj y la exclusión mutua por simulación; el motor no es seguro para acceso concurrente por sí solo.

## Pruebas

Suite completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Motor y ejemplos documentados:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_engine.py tests/test_models.py tests/test_times.py tests/test_snapshot_fcfs.py tests/test_fcfs_handoff.py
```

Motor: 79 pruebas aprobadas; API/servicio: 23; suite completa: 105. La interfaz FCFS sigue pendiente. Ver [estado.md](estado.md).

## Estructura

| Carpeta | Responsabilidad |
| --- | --- |
| `simulation/` | Motor FCFS, modelo y generación. Entregado. |
| `backend/` | Rutas, validaciones, servicio y reloj. Integración por verificar. |
| `frontend/` | Interfaz y controles. Pendiente de adaptar a FCFS. |
| `tests/` | Pruebas de motor, API, servicio y archivos estáticos. |
| `docs/` | Contrato, entrega y ejemplos del motor. |

La entrega del motor hasta `383a46f` se publicó en `origin/feature/fcfs`. El [sitio existente en Render](https://sso-multiprogramacion.onrender.com/) es una referencia del despliegue anterior: no se verificó ni desplegó FCFS allí en esta entrega.
