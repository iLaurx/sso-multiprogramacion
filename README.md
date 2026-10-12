# sso-multiprogramacion

Simulación de multiprogramación por lotes para la Actividad 4 de Seminario de
Sistemas Operativos. Esta entrega corresponde al motor Python del integrante 1.

## Motor de lotes

- Genera trabajos con IDs consecutivos, TME de 7 a 18 y operaciones válidas.
- Forma lotes de máximo 3 procesos y ejecuta una unidad por `tick()`.
- I reencola en el mismo lote y conserva el tiempo ejecutado.
- E termina por error; P pausa y C continúa.
- Al finalizar, conserva el reloj y los procesos terminados.

El motor usa únicamente la biblioteca estándar de Python 3.12. No necesita
FastAPI ni un servidor para funcionar.

## Preparación y pruebas

Desde la raíz del proyecto, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

Si ya tienes un entorno Python 3.12 con pytest, ejecuta solo el último comando.
Las dependencias web y su archivo de versiones quedan a cargo del integrante 2.

## Uso desde Python

```python
from simulation import SimulationEngine

motor = SimulationEngine.create(4, seed=123)
motor.tick()
motor.tick()
motor.interrupt()
estado = motor.snapshot()
```

`seed` es opcional y sirve para repetir una simulación en pruebas. Cada tick
avanza un segundo simulado; consultar `snapshot()` no modifica el reloj.

## Continuación del integrante 2

Revisa [la guía de integración](docs/entrega-motor.md) y
[el estado inicial de ejemplo](docs/fixtures/motor-inicial.json).
Faltan la API, el reloj del servidor, los bloqueos y la interfaz. El motor no
captura teclas: la interfaz enviará las acciones a la API.

Las reglas se tomaron de `Manual-instructions.md`. El enunciado del Programa 1
debe revisarse antes de la entrega académica, como indica el manual.
