# De lotes a FCFS — Actividad 6

Vamos a adaptar el simulador que ya tenemos para la actividad 6 de **Sistemas Operativos**. Seguimos trabajando en el mismo proyecto: aprovecharemos el servidor, las operaciones, la comunicación con la API y buena parte de la pantalla.

Este archivo recoge las reglas y el plan de la actividad 6. **El motor FCFS ya está implementado y revisado; falta completar la integración y adaptar la pantalla.** El alcance es únicamente la actividad 6. El estado vigente está en [estado.md](estado.md), el contrato real del motor en [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md) y el trabajo por integrar en [docs/entrega-motor.md](docs/entrega-motor.md).

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

En el motor actual, `I` ya bloquea durante 10 segundos simulados. El reencolado inmediato correspondía a la versión anterior de lotes.

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

Estas definiciones de llegada y espera ya se aplican en el motor. El tiempo en nuevos queda fuera de esas mediciones y el bloqueo se cuenta aparte de la espera en listos.

Si un proceso termina por error, guardaremos lo que alcanzó a ejecutarse; no completaremos artificialmente su TME. Los tiempos que todavía no se conozcan quedarán sin valor, no en cero.

Al finalizar se mostrará una tabla con los datos de todos los procesos, sus resultados y los seis tiempos.

## Qué vamos a aprovechar de cada parte

### Backend

El motor ya reemplazó la planificación por lotes con las colas de nuevos, listos y bloqueados, controla los tres espacios de memoria y calcula los tiempos. `lote` permanece como metadato interno temporal por compatibilidad del constructor; no se usa para planificar ni se expone en snapshot.

Conservaremos las operaciones aritméticas, los identificadores únicos, el TME aleatorio de 7 a 18 segundos y, donde siga teniendo sentido, los métodos actuales para crear, avanzar, interrumpir, terminar por error, pausar, continuar y consultar la simulación.

### API

Las rutas actuales para crear la simulación, consultar su estado y aplicar acciones ya existen. El servicio transmite el snapshot del motor y agrega `simulacion_id`. La siguiente etapa debe verificar ese recorrido con el esquema FCFS, completar sus pruebas y mantener el reloj en el servidor.

El snapshot conserva `reloj`, `en_ejecucion`, `terminados`, `tme`, `ejecutado`, `restante` y `en_espera` para la cola de listos. Ya incluye nuevos, bloqueados, memoria y tiempos; los campos públicos de lotes están retirados.

La guía real ya está en [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md), con métodos y cuatro snapshots reproducibles. [docs/contrato-api.md](docs/contrato-api.md) describe la envoltura HTTP actual; los criterios de integración pendientes están en [docs/entrega-motor.md](docs/entrega-motor.md). Este plan no sustituye esos contratos.

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
3. Modelo y motor FCFS: terminados.
4. Memoria, orden de ejecución, bloqueos, pausa, errores, tiempos y snapshot: revisados con pruebas del motor.
5. Guía del motor: terminada. Siguiente paso: verificar la integración de API/servicio, ampliar sus pruebas y reemplazar los fixtures de lotes.
6. Pendiente: adaptar la pantalla y probar el recorrido completo con reloj real y evidencia.

El único motor actual es FCFS. La versión anterior se conserva en Git; no se mantendrá un modo de lotes dentro de la web. La pantalla todavía representa la versión anterior y necesita adaptación.

Este archivo resume el cambio para que todos tengamos el mismo contexto. Los detalles de implementación se irán confirmando conforme terminemos y probemos cada parte.
