# Simulador de planificación de procesos

Una herramienta educativa para observar cómo un sistema operativo organiza los procesos que necesitan utilizar la CPU. La simulación muestra sus cambios de estado, el uso de la memoria y los tiempos que acumula cada proceso.

## ¿Qué puedes observar?

Los procesos avanzan por cinco estados: **nuevos**, **listos**, **en ejecución**, **bloqueados** y **terminados**. Hasta tres procesos pueden permanecer en memoria al mismo tiempo; los demás esperan su ingreso. Un proceso bloqueado sigue ocupando su lugar hasta que regresa a la cola de listos.

Cada proceso realiza una operación aritmética y registra datos como su tiempo de llegada, espera, respuesta, ejecución y finalización. Puedes usar estos datos para comparar cómo cambia el recorrido de los procesos durante la simulación.

El proyecto se está adaptando a **Round Robin**, una forma de repartir la CPU por turnos. Cada turno tiene una duración máxima llamada *quantum*. Si un proceso no termina durante su turno, vuelve al final de la cola y continúa cuando le toque otra vez.

> **Estado actual:** el motor ya utiliza Round Robin con un quantum de un segundo por defecto. La pantalla y la comunicación con el motor aún están pendientes de adaptación y verificación: la interfaz todavía muestra textos de FCFS y no permite elegir ni visualizar el quantum.

## Cómo usar la simulación

Una vez abierta la aplicación, elige la cantidad inicial de procesos y selecciona **Iniciar emulación**. Durante la ejecución puedes usar los botones de la pantalla o sus teclas:

| Tecla | Acción |
| --- | --- |
| **N** | Agregar un proceso nuevo. |
| **E** | Bloquear el proceso en ejecución durante nueve segundos simulados. |
| **W** | Terminar el proceso en ejecución con error. |
| **B** | Pausar la simulación y mostrar la tabla de procesos. |
| **C** | Continuar la simulación. |

La barra espaciadora también permite alternar entre pausa y continuación. Los controles disponibles dependen del estado de la simulación y de si hay un proceso en ejecución.

## Abrir la aplicación en tu computadora

Necesitas **Python 3.12** y una terminal de PowerShell. Desde la carpeta del proyecto, ejecuta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Después abre [la aplicación en tu navegador](http://127.0.0.1:8000). Si ya preparaste el entorno anteriormente, solo necesitas ejecutar el último comando.

Las simulaciones se guardan temporalmente: al detener o reiniciar la aplicación se pierden sus datos.

## Sobre el proyecto

Este simulador forma parte de actividades de la materia **Sistemas Operativos**. Su propósito es ayudar a comprender, mediante una representación visual, cómo se comparten la CPU y la memoria y cómo afectan las interrupciones al recorrido de los procesos.
