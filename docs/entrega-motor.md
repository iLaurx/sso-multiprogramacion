# Entrega del motor y siguientes integraciones — Actividad 6

Punto de partida para el desarrollador de API. Materia: **Sistemas Operativos**. Rama compartida: `feature/fcfs`. La entrega del motor se publicó hasta `383a46f`; esta actualización documental es posterior y permanece local hasta que el usuario solicite compartirla.

## Orden de lectura

[AGENTS.md](../AGENTS.md) → [estado.md](../estado.md) → este archivo → [contrato real del motor](cambios-backend-fcfs.md) → [contrato HTTP actual](contrato-api.md).

Antes de trabajar, comprobar `git status` y `git branch --show-current`. Actualizar la copia sin sobrescribir cambios locales y coordinar archivos compartidos. No hacer commit, push, merge ni despliegue sin la petición del usuario.

## Qué se recibe

| Área | Estado | Responsabilidad siguiente |
| --- | --- | --- |
| Motor `simulation/` | Terminado y revisado: FCFS, colas, tres residentes, I de 10 segundos, E, P/C, tiempos y snapshot. | Conservar el contrato; corregir solo fallos concretos reproducidos. |
| API `backend/routes.py`, `schemas.py` | Existen creación, consulta y acciones con validación y errores. | Verificar el esquema FCFS de extremo a extremo y documentarlo. |
| Servicio `backend/service.py` | Ya conserva motores, reloj, exclusión mutua e ID externo; transmite snapshot. | Probar tiempos, bloqueos y concurrencia a través del servicio. No duplicar el planificador. |
| Frontend `frontend/` | Todavía utiliza lotes y no representa FCFS correctamente. | Adaptar paneles, controles y tabla final después de fijar la integración HTTP. |
| Documentación y fixtures | Guías Markdown actualizadas. Los dos JSON antiguos siguen siendo de lotes. | API debe sustituir esos fixtures por salidas reproducibles FCFS y revisar consumidores. |

El import público sigue siendo `from simulation import SimulationEngine, SimulationStateError`. `create()` devuelve el motor; tick, interrupt, fail, pause y resume devuelven None. Consultar snapshot después de cada acción. Los métodos y cuatro ejemplos completos están en [cambios-backend-fcfs.md](cambios-backend-fcfs.md).

El modelo/generador conservan `lote` internamente por compatibilidad. No afecta FCFS ni aparece en la respuesta: no es un bloqueo para integrar API.

## Siguiente trabajo de API y servicio

1. Revisar el código existente y sus pruebas antes de añadir componentes. Conservar las rutas de creación, GET y actions de [contrato-api.md](contrato-api.md).
2. Comprobar que todas las respuestas mantienen las claves y valores del snapshot, añadiendo solo `simulacion_id`. Si se introducen modelos de respuesta, deben aceptar new/blocked, tiempos null, CPU null en running y los campos adicionales exclusivos de bloqueados.
3. Mantener el mapa de acciones: interrupt → interrupt(), error → fail(), pause → pause(), continue → resume(). Traducir SimulationStateError a 409 y conservar 404/422 para los casos documentados.
4. Mantener un único reloj del servidor y el mismo lock para tick, acciones y consultas. CPU null no es condición de parada: puede haber bloqueados. GET no avanza tiempo. El motor calcula tiempos y orden de colas.
5. Ampliar pruebas deterministas con `SimulationService(auto_clock=False)` y `await servicio.tick_once(id)`; complementar con pruebas de la tarea automática controlando el tiempo, sin esperas largas. No exponer tick como endpoint público.
6. Reemplazar o retirar de los consumidores `docs/contrato-api.json` y `docs/fixtures/motor-inicial.json`. Generar nuevos ejemplos desde el motor o servicio, indicar secuencia y comprobar su reproducción. No inventar IDs ni tiempos como evidencia.
7. Revisar con frontend los campos definitivos y anotar resultados en estado.md. No devolver campos ficticios de lotes para mantener la pantalla anterior.

## Criterios para cerrar API

Pendientes de comprobar explícitamente en el servicio/HTTP, aunque sus reglas ya pasan en el motor:

| Caso | Resultado esperado |
| --- | --- |
| Crear cuatro procesos con seed 123 | Memoria 3, uno en CPU, dos listos y uno nuevo; sin campos de lotes. |
| Terminar CPU normalmente o con error | Nuevo admitido al final de listos inmediatamente; memoria nunca supera 3; servicio real preservado por error. |
| Bloquear tres residentes | CPU null, estado running, memoria 3 y siguiente nuevo fuera de memoria. |
| Avanzar desde ese bloqueo | Sigue el reloj sin CPU; a los 9 segundos permanecen bloqueados y a los 10 regresan en orden. No consumen servicio en el tick de desbloqueo. |
| Pausar con CPU y/o bloqueados | Tras ticks del servicio no cambia reloj, servicio, espera ni bloqueo; continuar reanuda desde el mismo punto. |
| Consultar repetidamente | Mismos datos sin avanzar; null permanece null y las listas conservan orden. |
| Acciones inválidas para el estado | I/E sin CPU o en pausa: 409 sin cambios. P/C siguen disponibles con todos bloqueados. Tras completed se rechazan los controles. |
| Finalizar todos | completed, memoria 0, CPU null y todas las listas activas vacías; terminados y tiempos conservados. |
| Varias simulaciones y acceso concurrente | Sin cruces de IDs/tiempos ni ticks duplicados; acciones y consultas serializadas por simulación. |
| Cerrar el servicio | Tareas canceladas y registros liberados; sin tareas huérfanas. |

Usar casos de tiempos conocidos de `tests/test_times.py` para contrastar también la salida HTTP. Al terminar, registrar qué casos pasaron, qué archivos cambiaron y cualquier prueba que aún falte.

## Integración posterior de frontend

| Parte | Cambio pendiente |
| --- | --- |
| Lotes pendientes | Mostrar cantidad de nuevos con `nuevos.length`. |
| Lote actual | Mostrar `memoria_ocupada` de un máximo de 3. |
| Tabla del lote | Sustituir filtros por lote por CPU/listos; respetar `en_espera` como FCFS. |
| Bloqueados | Agregar ID y `bloqueo_transcurrido`/`bloqueo_restante` del servidor. No usar el acumulado como duración del bloqueo actual. |
| CPU libre | Mostrar que espera bloqueados sin tratarlo como completed ni detener las consultas. |
| Controles | I/E disponibles solo con running y CPU; P/C según estado. Actualizar textos y teclas I/E/P/C. |
| Terminados y tabla final | Quitar lote; mostrar resultado o ERROR, llegada, finalización, retorno, respuesta, espera y servicio desde ejecutado. Conservar null como dato desconocido. |
| Consulta y recuperación | Mantener ID en sessionStorage, serializar peticiones y recuperar el snapshot; tratar 404, 409, 422 y errores de red. |

No llevar un reloj ni recalcular tiempos en el navegador. Verificar el recorrido visual con nuevos, bloqueos, CPU libre, pausa, error, final normal y recarga. Registrar evidencia sin afirmar que ya funciona por existir el código.

## Diferenciar fallos y cambios de contrato

No son fallos del motor: campos de lotes ausentes, CPU null con bloqueados, resultado null por error, controles I/E rechazados sin CPU y espera que excluye nuevos y bloqueo. Son cambios documentados o estados válidos.

Si una prueba de integración detecta un fallo del motor, entregar la secuencia mínima de create/tick/acciones, snapshot real y esperado. Revisar la corrección con el responsable del motor antes de modificar otras áreas. No existe un fallo conocido que impida la entrega dentro de lo revisado.

## Verificación de referencia

En la revisión del motor: **79 pruebas del motor y 94 de la suite completa aprobadas**. Se comprobaron los cuatro ejemplos reales de snapshot, casos conocidos de tiempos, colas, memoria, bloqueos simultáneos/repetidos, controles y pausa. Comandos en [README](../README.md#pruebas).

La suite actual de API comprueba varios recorridos básicos, pero no sustituye todos los criterios anteriores. No se verificó el recorrido HTTP completo con reloj real ni la adaptación visual. La tarea automática sigue siendo parte de las verificaciones que debe cerrar el compañero de API.

Solo actividad 6. No agregar procesos durante ejecución, N, B, tabla BCP, bloqueo de 9 segundos, otro motor permanente ni un selector. No se propone cambiar tecnologías, añadir una base de datos o desplegar en este paso.
