# Estado del proyecto

Última actualización: 3 de noviembre de 2026.

## Situación actual

**Motor FCFS de la actividad 6 de Sistemas Operativos terminado y entregado. Siguiente responsable: API/integración.** Rama comprobada: `feature/fcfs`. La entrega hasta `383a46f` se subió y verificó en `origin/feature/fcfs`. Esta actualización posterior solo modifica Markdown y se guarda en un commit local autorizado por el usuario, sin push. No se desplegó.

| Área | Estado vigente |
| --- | --- |
| Motor | FCFS, tres residentes, nuevos/listos/bloqueados, I de 10 segundos, E, P/C, tiempos y snapshot completos. Sin fallos conocidos en los casos revisados. |
| API y servicio | Rutas, validaciones, reloj y locks existentes; ya transmiten el snapshot del motor. Falta cerrar las pruebas de integración FCFS y sustituir fixtures de lotes. |
| Frontend | Sigue esperando lotes. Pendiente de paneles FCFS, bloqueados, controles, tiempos y tabla final. |
| Documentación | Guías Markdown actualizadas. Los JSON antiguos de contrato y fixture siguen siendo de lotes y están señalados como pendientes. |

## Por dónde empieza el siguiente dev

1. Leer [AGENTS.md](AGENTS.md) y [docs/entrega-motor.md](docs/entrega-motor.md). La entrega enumera tareas por área y criterios concretos para cerrar API.
2. Revisar [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md): métodos, tipos, campos y cuatro snapshots reales reproducibles. Usar [docs/contrato-api.md](docs/contrato-api.md) para la envoltura HTTP y errores existentes.
3. Completar pruebas del servicio/HTTP con memoria, CPU libre, bloqueo exacto, pausa, errores, consultas sin avance, tiempos null, concurrencia y cierre. No duplicar reloj, tiempos ni planificación. No reconstruir las rutas actuales.
4. Reemplazar o retirar de consumidores `docs/contrato-api.json` y `docs/fixtures/motor-inicial.json`: no usarlos como FCFS. Después coordinar frontend con el contrato validado.

Reglas que debe conservar API: llegada al admitir a memoria; primera atención solo al primer despacho; finalización normal o por error; retorno/respuesta calculados; espera solo en listos; ejecutado como servicio real; bloqueo separado. CPU null con running es válido si quedan bloqueados. Se eliminaron los campos públicos de lotes. El `lote` interno temporal no impide integrar snapshot.

## Comprobaciones

- Revisión de entrega anterior: **79 pruebas del motor y 94 de la suite completa aprobadas**, incluidos los cuatro ejemplos reales de la guía. Se verificaron memoria, FCFS, tiempos conocidos, bloqueo simultáneo/escalonado/repetido, pausa, rechazo de controles y snapshots independientes.
- Esta actualización documental se contrastó con rutas, esquemas, servicio, pruebas existentes y dependencias de lotes de la pantalla. Se comprobaron 41 enlaces locales sin rutas rotas y los bloques de código de las guías.
- Prueba de reproducción de los cuatro snapshots documentados: **1 aprobada**, con el aviso existente de permisos de caché de pytest. `git diff --check` sin errores; solo cambiaron ocho archivos Markdown. No se repitió la suite completa porque no se cambió código.
- Pendiente de acreditar: recorrido HTTP completo con reloj real y validación visual FCFS. Las pruebas básicas existentes de API no cubren por sí solas todos los criterios de la entrega.

## Archivos documentales actualizados

`AGENTS.md`, `README.md`, `fcfs.md`, `docs/entrega-motor.md`, `docs/contrato-api.md`, `docs/cambios-backend-fcfs.md` y este archivo. `Manual-instructions.md` conserva el contenido histórico de actividad 4 con un aviso inicial que remite a las instrucciones vigentes.

No se modificaron motor, API, servicio ni frontend en este paso. Solo actividad 6; prohibido implementar o preparar actividad 8. Al cerrar la integración, actualizar este estado con archivos, pruebas, resultados y pendientes reales.
