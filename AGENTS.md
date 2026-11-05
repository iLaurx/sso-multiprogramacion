# Guía para trabajar en este proyecto

Este proyecto se está adaptando de multiprogramación por lotes a FCFS para la **actividad 6 de Sistemas Operativos**. Trabajamos por pasos sobre la misma aplicación.

## Antes de empezar

1. Lee [fcfs.md](fcfs.md): explica qué vamos a integrar y qué queremos conservar.
2. Lee [estado.md](estado.md): indica qué está hecho, qué falta y cuál es el siguiente paso.
   Para continuar la integración, lee también [docs/entrega-motor.md](docs/entrega-motor.md) y [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md).
3. Revisa la rama y los cambios locales con `git status` y `git branch --show-current`. La rama compartida prevista es `feature/fcfs`; no asumas que sigues en ella.
4. Revisa el código y las pruebas del área que vas a tocar. Consulta también el [README](README.md) para ejecutar el proyecto.

La petición actual del usuario define qué paso debes hacer. Leer los pendientes no significa que debas implementarlos todos. Si la documentación y el código no coinciden, señala la diferencia y comprueba qué funciona realmente antes de continuar.

## Alcance y acuerdos

- **Solo actividad 6. Está prohibido implementar o preparar funciones de la actividad 8.** No agregar creación de procesos durante la ejecución, tecla N, tabla BCP con tecla B ni bloqueo de 9 segundos.
- Los controles de esta actividad son I para bloquear durante 10 segundos de simulación, E para terminar por error y P/C para pausar y continuar.
- La materia se llama **Sistemas Operativos**. No usar “Seminario” en la documentación que preparemos.
- FCFS reemplazará al motor de lotes. No crear dos modos, dos motores permanentes ni un selector. El usuario indicó que ya guardó la versión anterior con un tag y una release.
- Aprovechar las rutas, métodos, campos y componentes actuales cuando sigan teniendo sentido. No hacer una reescritura completa ni cambiar tecnologías sin necesidad.
- Las definiciones de llegada y espera están explicadas en `fcfs.md`. Si algún cálculo necesita una decisión adicional, dejarla clara antes de aplicarla.

## Cómo repartir los cambios

- **Motor/backend:** lógica de procesos en `simulation/`, colas, memoria, bloqueos y tiempos.
- **API:** servicio, rutas y validaciones en `backend/`; conecta el motor con la pantalla.
- **Frontend:** interfaz y controles en `frontend/`.
- Las pruebas correspondientes están en `tests/`.

Estos límites ayudan a coordinarse. No cambies archivos de otra área por iniciativa propia si el paso solicitado no lo necesita. Si una corrección depende de otra parte, explica qué falta para conectarla.

El motor FCFS ya está terminado y revisado. Su contrato Python y los ejemplos reales están en [docs/cambios-backend-fcfs.md](docs/cambios-backend-fcfs.md). El siguiente trabajo corresponde a integración de API/servicio y después frontend, según [docs/entrega-motor.md](docs/entrega-motor.md). Las rutas y el servicio ya existen: revisarlos y completar las pruebas necesarias, sin reconstruirlos ni duplicar el motor.

[docs/contrato-api.md](docs/contrato-api.md) documenta las rutas y la respuesta FCFS validada. `docs/contrato-api.json` y `docs/fixtures/motor-inicial.json` son ejemplos FCFS reproducibles comprobados en las pruebas de API. `Manual-instructions.md` conserva el manual histórico de actividad 4; no rige actividad 6.

Al trabajar en API, preservar los tiempos que calcula el motor, el orden de las listas y los null. Una CPU libre no significa simulación terminada: puede haber bloqueados. No modificar `simulation/` salvo un fallo concreto reproducido y necesario para el paso solicitado.

## Al modificar y comprobar

- Haz cambios pequeños que se puedan explicar y revisar por separado.
- Respeta el trabajo local de los demás. No borres, reviertas ni sobrescribas cambios ajenos.
- No hagas commits, pushes, merges, tags, releases o despliegues salvo que el usuario los pida.
- Comprueba lo que cambiaste con las pruebas pertinentes. Para la suite actual: `.\.venv\Scripts\python.exe -m pytest -q` desde la raíz.
- No marques algo como funcionando solo porque está escrito. Indica qué comprobaste, el resultado y cualquier parte que no pudiste verificar.
- No incluyas contraseñas, tokens ni otros secretos en documentos o ejemplos.

## Al terminar un paso

Actualiza [estado.md](estado.md) con:

- Qué quedó hecho y qué archivos cambiaron.
- Qué pruebas o revisiones se hicieron y su resultado; si no hubo pruebas, dilo.
- Qué sigue pendiente y si hay algo que otro integrante debe conocer.
- Cualquier cambio en los datos o métodos que afecte a API o frontend.

Mantén el estado corto y vigente. No copies toda la conversación ni conviertas el archivo en un historial de cada edición. Si cambió el plan, actualiza también `fcfs.md`; si solo avanzó la implementación, basta con actualizar `estado.md`.

Escribe las explicaciones en español natural: qué cambió, para qué y qué falta. Usa los términos técnicos cuando ayuden a entender, sin frases de relleno.
