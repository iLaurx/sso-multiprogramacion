# SSO - Multiprogramación por lotes

Base común para la Actividad 4 / Programa 2. Por ahora sirve la página inicial
y `GET /api/health`; el motor y los controles de simulación están pendientes.

## Preparar el proyecto en Windows

Desde la carpeta raíz del repositorio, crear un entorno propio e instalar las
versiones compartidas:

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Usar Python 3.12.x; esta base se comprobó con Python 3.12.7.
Si `py -3.12` no encuentra la instalación, usar la ruta del ejecutable de
Python 3.12 en su lugar. En una instalación por usuario de Windows:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
```

Cada integrante crea su propia `.venv`; no se sube ni se copia entre equipos.
Al cambiar de versión de Python, detener el servidor y desactivar el entorno
antes de eliminar únicamente `.venv`, recrearla y reinstalar las dependencias.
Crear el entorno sobre una `.venv` anterior puede conservar dependencias
compiladas para otra versión y provocar errores de importación.

En VS Code, seleccionar `.venv\Scripts\python.exe` como intérprete de Python.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Abrir <http://127.0.0.1:8000/>: debe mostrar **API: ok**.
La comprobación de la API está en <http://127.0.0.1:8000/api/health>
y su documentación en <http://127.0.0.1:8000/docs>.
Mantener la terminal abierta; detener con `Ctrl+C`.

También se puede activar el entorno y usar el comando del manual:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
```

Si PowerShell bloquea la activación, usar el comando con la ruta completa de
Python; no hace falta cambiar la política del sistema. No abrir `index.html`
con doble clic. Para la demo final, omitir `--reload` y usar un solo worker.

## Comprobar la base

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas verifican la ruta health y que se sirvan la página y su JavaScript.
Todavía no prueban una simulación.

## Archivos y responsabilidades

| Ruta | Responsable y alcance |
| --- | --- |
| `simulation/` | Integrante 1: motor puro, lotes, tiempos y eventos. |
| `backend/` | Integrante 2: API, servicio y reloj del servidor. |
| `frontend/` | Integrante 3: pantalla, consultas y teclas. |
| `tests/` | Cada integrante agrega pruebas reales de su módulo. |
| `docs/contrato-api.md` | Contrato propuesto para coordinar los módulos. |
| `docs/contrato-api.json` | Ejemplo ilustrativo para construir la interfaz. |
| `requirements.in` | Dependencias directas. |
| `requirements.txt` | Versiones instalables compartidas, incluidas las indirectas. |

Los archivos del motor, rutas de simulación, estilos, evidencias y reporte se
agregan al implementar sus fases; no hacen falta archivos vacíos para el arranque.

## Trabajo con ramas

Integrar primero esta base en `main`, preferentemente mediante un PR revisado.
Después, cada integrante actualiza su copia y crea una rama para su tarea:

```powershell
git switch main
git pull --ff-only origin main
# Ejecutar solo la línea del módulo correspondiente:
git switch -c feature/i1-motor-lotes
git switch -c feature/i2-api-simulacion
git switch -c feature/i3-interfaz
```

Después de recibir cambios que modifiquen dependencias, volver a instalar
`requirements.txt` y ejecutar las pruebas. Si se agregan dependencias, actualizar
`requirements.in` y regenerar la lista desde un entorno limpio:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.in
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 requirements.txt
```

## Alcance pendiente

La futura simulación usará lotes de hasta tres trabajos y teclas **I**
(interrumpir), **E** (error), **P** (pausar) y **C** (continuar).
Estas funciones aún no están implementadas. El diseño propuesto conserva el
estado en memoria: reiniciar el servidor lo borrará. No requiere base de datos
ni Node.js.
