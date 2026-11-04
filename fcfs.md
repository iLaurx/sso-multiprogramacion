# De lotes a FCFS — Actividad 6

Vamos a adaptar el simulador que ya tenemos para la actividad 6 de **Sistemas Operativos**. Seguimos trabajando en el mismo proyecto: aprovecharemos el servidor, las operaciones, la comunicación con la API y buena parte de la pantalla.

Este archivo explica lo que vamos a integrar. **Es un plan; los cambios todavía no están implementados.** El alcance es únicamente la actividad 6.

## ¿Qué cambia?

Dejamos de organizar los procesos en lotes. Ahora usaremos **FCFS**: el primero en llegar a la cola de listos será el primero en usar la CPU. Un proceso seguirá ejecutándose hasta que termine, lo bloqueemos o lo terminemos por error.

Cada proceso estará en uno de estos cinco estados:

| Estado | Qué significa |
| --- | --- |
| Nuevo | Ya fue generado, pero espera espacio para entrar a memoria. |
| Listo | Está en memoria, esperando su turno para usar la CPU. |
| Ejecución | Está usando la CPU. Solo puede haber uno a la vez. |
| Bloqueado | Espera a que termine una solicitud de entrada/salida. |
| Terminado | Finalizó normalmente o salió por error. |

## Memoria: tres procesos como máximo

El límite de tres cuenta a los procesos **listos, en ejecución y bloqueados**. Los que no quepan se quedan en nuevos.

Cuando un proceso termina, entra el siguiente nuevo si hay alguno pendiente. Ya no hay que esperar a que termine un lote completo.

**Bloquear un proceso libera la CPU, pero no su espacio en memoria.** Por ejemplo, si hay uno en ejecución y dos bloqueados, los tres espacios siguen ocupados.

## Controles de la actividad 6

| Tecla | Acción |
| --- | --- |
| `I` | Mueve el proceso de CPU a bloqueados durante 10 segundos de simulación. Después vuelve al final de listos y conserva lo que ya ejecutó. |
| `E` | Termina el proceso actual por error y muestra `ERROR` como resultado. Libera un espacio en memoria. |
| `P` | Pausa toda la simulación, incluidos reloj, ejecución y bloqueos. |
| `C` | Continúa desde donde quedó. |

Actualmente, `I` devuelve el proceso directamente a la cola. Ese comportamiento se reemplazará por el bloqueo de 10 segundos.

El reloj debe seguir avanzando si la CPU está libre pero quedan procesos bloqueados. La simulación termina cuando todos los procesos hayan terminado, incluidos los que salgan por error.

## Tiempos que vamos a registrar

Además del TME, el tiempo ejecutado y el restante, necesitamos estos datos:

| Tiempo | Cómo lo vamos a interpretar |
| --- | --- |
| Llegada | Momento en que el proceso pasa de nuevos a memoria. |
| Finalización | Momento en que termina, normalmente o por error. |
| Retorno | Finalización menos llegada. |
| Respuesta | Tiempo desde su llegada hasta que usa la CPU por primera vez. |
| Espera | Tiempo acumulado en la cola de listos. |
| Servicio | Tiempo que realmente ha usado la CPU; corresponde a `ejecutado`. |

Estas definiciones de llegada y espera son el criterio que proponemos usar en el proyecto. El tiempo en nuevos queda fuera de esas mediciones y el bloqueo se cuenta aparte de la espera en listos.

Si un proceso termina por error, guardaremos lo que alcanzó a ejecutarse; no completaremos artificialmente su TME. Los tiempos que todavía no se conozcan quedarán sin valor, no en cero.

Al finalizar se mostrará una tabla con los datos de todos los procesos, sus resultados y los seis tiempos.

## Qué vamos a aprovechar de cada parte

### Backend

Aquí estará el cambio principal: reemplazar los lotes por las colas de nuevos, listos y bloqueados, controlar los tres espacios de memoria y calcular los tiempos.

Conservaremos las operaciones aritméticas, los identificadores únicos, el TME aleatorio de 7 a 18 segundos y, donde siga teniendo sentido, los métodos actuales para crear, avanzar, interrumpir, terminar por error, pausar, continuar y consultar la simulación.

### API

La idea es conservar las rutas actuales para crear la simulación, consultar su estado y aplicar acciones. La API seguirá conectando el motor con la pantalla y el servidor seguirá controlando el reloj.

Mantendremos los campos que todavía sirven, como `reloj`, `en_ejecucion`, `terminados`, `tme`, `ejecutado` y `restante`. También podemos conservar `en_espera` para la cola de listos. Agregaremos los datos de nuevos, bloqueados, memoria y tiempos; los campos de lotes se retirarán.

**Cuando el backend esté listo, prepararemos una guía con los cambios reales**, los métodos disponibles y ejemplos de los datos que devuelve. Con eso se ajustará la API sin tener que adivinar cómo quedó el motor. Este documento todavía no fija el contrato final.

### Frontend

Vamos a adaptar la pantalla actual, conservando su diseño, las peticiones a la API, la consulta periódica y los controles que sigan sirviendo.

| Parte actual | Adaptación prevista |
| --- | --- |
| Reloj y tarjeta de CPU | Se conservan y se ajustan a los datos de FCFS. |
| Cola de espera | Se muestra como cola de listos, respetando el orden recibido. |
| Lotes pendientes | Se reemplaza por la cantidad de procesos nuevos. |
| Lote actual | Se reemplaza por la ocupación de memoria. |
| Terminados | Se conserva, quitando la columna de lote. |
| Panel de bloqueados | Se agrega con ID y tiempo transcurrido en bloqueo. |
| Tabla final | Se amplía para mostrar los datos y tiempos de todos los procesos. |

Los tiempos se tomarán del servidor. La pantalla no llevará un reloj independiente ni calculará por su cuenta los tiempos de cada proceso.

## Cómo vamos a avanzar

1. Conservar la versión de lotes mediante el tag y la release que ya se crearon.
2. Trabajar en la rama compartida `feature/fcfs`, haciendo cambios pequeños y revisándolos por etapas.
3. Preparar los datos de los procesos y después adaptar el motor a FCFS.
4. Comprobar memoria, orden de ejecución, bloqueos, pausa, errores y tiempos.
5. Documentar cómo quedó el backend y conectar la API con esos datos.
6. Adaptar la pantalla y probar el recorrido completo.

La aplicación quedará con un solo motor: FCFS. La versión anterior seguirá disponible en Git; no vamos a mantener un modo de lotes dentro de la web.

Este archivo resume el cambio para que todos tengamos el mismo contexto. Los detalles de implementación se irán confirmando conforme terminemos y probemos cada parte.
