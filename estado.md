# Estado del proyecto

Última actualización: 3 de noviembre de 2026.

## Dónde estamos

**Estamos preparando la adaptación a FCFS. Todavía no se han implementado los cambios de la actividad 6.** El código revisado conserva el modelo y el motor de lotes.

- Rama comprobada al preparar este archivo: `feature/fcfs`. Verificarla de nuevo al comenzar otra sesión.
- El usuario confirmó que creó un tag y una release para conservar la versión anterior. No se verificaron aquí sus nombres ni su publicación.
- Se trabajará únicamente en la actividad 6 de **Sistemas Operativos**.

## Qué está listo

- [fcfs.md](fcfs.md): explicación general del cambio, las reglas y las partes que vamos a aprovechar.
- [AGENTS.md](AGENTS.md): instrucciones para que los agentes lean el contexto y trabajen por etapas.
- [Plan en PDF](output/pdf/Plan_adaptacion_Actividad_6_FCFS.pdf): adaptaciones y reparto detallado por área. Es un plan, no evidencia de que ya se implementó.
- Se preparó en el chat un primer prompt para adaptar los datos de los procesos. Ese trabajo todavía no se ejecutó.

Estos documentos están creados localmente. No se ha hecho commit ni push desde esta sesión. Cada integrante debe tenerlos en su copia para que su agente pueda leerlos.

## Avance por área

| Área | Situación actual | Próximo cambio |
| --- | --- | --- |
| Motor/backend | Sigue funcionando con lotes. El modelo todavía tiene `lote` y no contempla nuevos ni bloqueados. | Preparar los datos del proceso, sin cambiar aún la ejecución ni la respuesta pública. |
| API | Conserva las rutas y respuestas de lotes. | Esperar la explicación del backend terminado y ajustar la conexión con sus datos reales. |
| Frontend | Conserva la pantalla de lotes. | Adaptarla cuando estén definidos los datos del motor y la API. |

## Siguiente paso: preparar el modelo de proceso

El primer cambio previsto se concentra en los datos, antes de reescribir el motor:

1. Revisar el modelo, el generador, el motor y las pruebas que los usan.
2. Agregar los estados nuevo y bloqueado, y los datos necesarios para llegada, primera atención, finalización, espera y bloqueo.
3. Conservar `ejecutado` como tiempo de servicio y evitar contadores duplicados.
4. Usar `None` para instantes que todavía no ocurrieron, como primera atención y finalización.
5. Mantener compatible el motor actual durante este paso. `lote` puede quedarse temporalmente hasta reemplazar su lógica.
6. No cambiar todavía el contenido público de `snapshot()`, las rutas ni el frontend. Los datos nuevos se expondrán cuando el motor pueda actualizarlos correctamente.
7. Verificar los valores iniciales nuevos y que las pruebas existentes sigan pasando.

Este apartado describe el siguiente paso; no indica que ya se haya hecho ni autoriza a implementar todo el plan de una vez.

## Lo que vendrá después

- Reemplazar lotes por nuevos, listos, ejecución, bloqueados y terminados, con tres procesos como máximo en memoria.
- Implementar FCFS, bloqueo de 10 segundos, admisión al liberarse memoria y tiempos de la actividad 6.
- Probar pausa completa, CPU libre con bloqueados, errores y finalización.
- Preparar una guía de cambios reales del backend para conectar la API.
- Adaptar la pantalla y revisar el funcionamiento completo.

No se desarrollará ni se preparará nada de la actividad 8.

## Comprobaciones y pendientes de coordinación

- Para preparar estos archivos se revisaron la rama, el estado de Git, `fcfs.md` y el modelo actual. No se modificó código de la aplicación ni se ejecutaron pruebas en este paso de documentación.
- No hay un bloqueo conocido para empezar con el modelo. El contrato final para API sigue pendiente del backend; no debe darse por implementado lo propuesto en el plan.
- Antes de editar en la rama compartida, revisar cambios de los compañeros y evitar tocar los mismos archivos a la vez. Coordinar también las actualizaciones de este archivo.

## Cómo mantener este archivo

Al terminar un paso, actualizar el resumen y la tabla de avance con lo que realmente quedó hecho. Añadir los archivos afectados, las comprobaciones y su resultado, y reemplazar “Siguiente paso” por lo que corresponda. No registrar una tarea como terminada si aún depende de código o pruebas pendientes.
