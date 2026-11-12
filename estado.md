# Estado del proyecto

Última actualización: 11 de noviembre de 2026.

## Actividad 10: interfaz Round Robin

Trabajo realizado en la rama `round-robin` (seguimiento: `origin/feature/round-robin`).
`frontend/index.html` y `frontend/app.js` ahora solicitan un quantum entero positivo,
lo envían al crear la simulación y muestran el quantum y `tiempo_turno` recibidos
del servidor junto al servicio acumulado y el restante. La cola de listos conserva
el orden de la API; el historial anuncia cuándo un proceso agota su turno. Se
actualizó la tabla para mostrar el tiempo restante de bloqueo, además de los
controles, textos y README para Round Robin.

El backend de esta rama ya recibe `quantum` al crear y lo incluye en el snapshot.
No se modificaron motor ni API. No se ejecutaron pruebas ni una revisión en
navegador en este paso.

## Pendiente

Revisar visualmente el recorrido con varios procesos y quantum 1, incluidos los
cambios de turno, E/W/P/B/C/N, CPU libre por bloqueos y la tabla al pausar y al
terminar. Comprobar el flujo completo con el reloj real del servidor.
