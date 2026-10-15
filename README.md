# SSO · Multiprogramación por lotes

Simulador web educativo que permite observar cómo se organizan y ejecutan procesos por lotes. A través de una interfaz interactiva, muestra la cola de espera, el proceso en CPU, los tiempos de ejecución y los resultados de cada trabajo.

Desarrollado para la Actividad 4 / Programa 2 de Seminario de Sistemas Operativos.

**[Abrir el simulador](https://sso-multiprogramacion.onrender.com/)** · Desplegado en **Render** y disponible desde el navegador, sin instalación local.

## Acerca del proyecto

La simulación representa una CPU que atiende un proceso a la vez. Los trabajos se generan automáticamente y se agrupan en lotes de hasta **3 procesos**. Cada lote debe finalizar antes de que comience el siguiente.

Cada proceso cuenta con un identificador, una operación aritmética y un tiempo máximo estimado (TME) de **7 a 18 segundos**. Durante la ejecución es posible interrumpir un proceso, terminarlo por error o pausar la simulación para observar su estado.

## Características

- Visualización del recorrido de los procesos: cola de espera, CPU y trabajos terminados.
- Seguimiento del reloj global, lote actual y lotes pendientes.
- Consulta del tiempo utilizado y restante de cada proceso.
- Generación de operaciones de suma, resta, multiplicación, división y residuo.
- Controles mediante botones y atajos de teclado.
- Historial de movimientos y resultados al finalizar la simulación.

## Cómo utilizarlo

1. Abre el [simulador en línea](https://sso-multiprogramacion.onrender.com/).
2. Introduce la cantidad de trabajos que deseas simular.
3. Pulsa **Iniciar emulación** para generar los procesos y comenzar.
4. Observa el avance de los lotes y utiliza los controles durante la ejecución.
5. Consulta los resultados al terminar o inicia una nueva simulación.

| Tecla | Acción | Comportamiento |
| :---: | --- | --- |
| **I** | Interrumpir | Envía el proceso al final de la cola del lote actual y conserva su avance. |
| **E** | Error | Termina el proceso actual y registra `ERROR` como resultado. |
| **P** | Pausar | Detiene temporalmente la simulación. |
| **C** | Continuar | Reanuda la simulación pausada. |

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Motor de simulación | Python |
| API y reloj de la simulación | FastAPI y Uvicorn |
| Interfaz web | HTML, CSS y JavaScript |
| Pruebas automatizadas | pytest y HTTPX |
| Despliegue web | Render |

## Ejecución local

Requiere **Python 3.12**. Desde la raíz del repositorio, ejecuta los siguientes comandos en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000) en el navegador. La documentación interactiva de la API está disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

La aplicación no requiere una base de datos ni Node.js para ejecutarse.

## Estructura del repositorio

```text
sso-multiprogramacion/
├── backend/           API, servicio y reloj de la simulación
├── simulation/        Motor de procesos, lotes y eventos
├── frontend/          Interfaz web y controles
├── tests/             Pruebas del motor y la API
├── docs/              Documentación técnica y ejemplos
├── requirements.in    Dependencias directas
└── requirements.txt   Versiones de las dependencias
```

## Pruebas

Para ejecutar las pruebas automatizadas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

La suite incluye pruebas del motor, las validaciones y acciones de la API, el ciclo de vida del servicio y la entrega de archivos de la interfaz.

## Estado de las simulaciones

El servidor mantiene las simulaciones en memoria y utiliza un único proceso de servicio (worker). Al recargar la página en la misma pestaña, la interfaz puede recuperar la simulación activa mientras siga disponible en el servidor. Si el servicio se reinicia, las simulaciones se pierden y es necesario iniciar una nueva.
