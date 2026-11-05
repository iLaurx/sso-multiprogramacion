# Estado del proyecto

Última actualización: 4 de noviembre de 2026.

## Situación actual

CPU 2D: se añadió una barra de avance con transición suave entre las actualizaciones del servidor y texto de segundos restantes/ejecutados. Cambios en `frontend/app.js` y `frontend/index.html`. La tarjeta se conserva mientras siga el mismo proceso para animar el avance; al cambiar de proceso se muestra su propio servicio acumulado. No hay reloj adicional: se usan `ejecutado`, `tme` y `restante`. Incluye atributos accesibles y respeta la preferencia de movimiento reducido. `node --check frontend/app.js` y `git diff --check` aprobados; no se ejecutó la suite ni se verificó en navegador en este paso. Contrato de API y motor intactos.

Preferencia visual aplicada: se retiró la vista 3D. `frontend/index.html` conserva las cinco columnas y tarjetas 2D de FCFS, sin panel, estilos ni scripts de Three.js; se eliminó `frontend/visualizacion.js` y su llamada desde `frontend/app.js`. Se respetaron los cambios locales previos. No cambian la API, los controles ni los tiempos. Sintaxis de `app.js` y `git diff --check` aprobados; búsqueda sin referencias restantes al visor en frontend. La suite pytest y la captura con Playwright se intentaron en esta revisión, pero no devolvieron resultados y se interrumpieron; no se acredita una nueva comprobación de navegador ni de la suite para este cambio.

**Actividad 6: motor, API y frontend FCFS integrados y comprobados localmente.** Rama actual: `codex/integracion-fcfs-frontend`. Al iniciar esta revisión la adaptación visual y el merge de integración ya existían; el único elemento local sin seguimiento era `output/`, que se conserva intacto.

La pantalla conserva el diseño y componentes existentes: creación de todos los procesos al inicio, cinco estados, orden FCFS, nuevos, memoria de tres residentes, reloj del servidor, CPU, bloqueo actual de 10 segundos y tabla de tiempos/resultados. `ERROR` depende del estado; servicio usa `ejecutado`. Se distinguen null y cero y solo `completed` detiene las consultas. No quedan referencias a campos de lotes en `frontend/`.

En este paso se modificaron:

- `frontend/app.js`: reserva inmediata de la petición para impedir creaciones y acciones duplicadas por pulsaciones rápidas; controles deshabilitados mientras hay una petición; un único punto para reprogramar consultas también después de errores; recuperación inicial protegida antes de permitir crear otra simulación. Los atajos ignoran campos de entrada, contenido editable y composición de texto. La comprobación de disponibilidad también valida el estado HTTP.
- `tests/browser_fcfs.py`: recorrido ampliado con latencia, creación/acciones simultáneas, atajos durante edición, recuperación lenta, error HTTP 422 y continuidad de consultas. También verifica regreso de bloqueados a listos y servicio positivo conservado al terminar por error.
- `estado.md`: situación y comprobaciones de esta revisión.

No cambió el contrato de datos ni los métodos para API/frontend. `simulation/`, `backend/`, tecnologías y diseño se conservaron. Solo actividad 6, sin creación durante ejecución ni controles de actividad 8.

## Comprobaciones

- Suite completa solicitada: **105 aprobadas**, con `.\.venv\Scripts\python.exe -m pytest -q`. Un aviso de deprecación Starlette/HTTPX; sin fallos.
- Sintaxis de `frontend/app.js` y `frontend/visualizacion.js`: `node --check` aprobada. `git diff --check`: sin errores de espacios.
- Chrome local sin interfaz visible contra Uvicorn en `127.0.0.1:8767`, con reloj automático real y sin endpoint de tick: creación de cuatro procesos, tres residentes y nuevos, I/E/P/C, CPU libre con tres bloqueados, pausa que congela reloj/bloqueos, continuación, desbloqueo tras 10 segundos simulados, admisión de nuevos, final normal/error y comparación de todas las celdas de la tabla final con la respuesta HTTP.
- Recarga en pausa y al finalizar, conflicto 409 provocado por otro cliente, pérdida de conexión durante recuperación con conservación del ID, reintento y 404 que permite crear otra simulación. Sin errores JavaScript.
- Recorrido adicional con respuestas demoradas: un solo POST ante dos solicitudes de creación o acción, ninguna petición API simultánea, Enter sin creación durante ejecución, atajos ignorados en input y contenido editable, error 422 con `detail` en lista y consultas que continúan sin repetir el POST.
- Capturas de escritorio, CPU libre pausada y viewport móvil de 390 px revisadas; sin desbordamiento horizontal del documento, con desplazamiento interno de la tabla. Evidencia local ignorada por Git en `tmp/fcfs-browser/`: capturas y `resultado.json` del motor real. El script requiere Playwright y Chrome local o Chromium, sin añadir dependencias al servidor.

## Pendientes y límites

Revisión puntual de las tarjetas: el HTML actual ya muestra «Memoria ocupada» con capacidad 3 y «Procesos nuevos»; `app.js` usa `memoria_ocupada` y `nuevos.length`, sin campos públicos de lotes. Sintaxis JavaScript comprobada con `node --check`. La consulta HTTP adicional con TestClient no terminó y se interrumpió; esta revisión no confirma qué versión está abierta en el navegador o publicada. No se modificó el frontend en esta comprobación.

Revisión del equipo antes de publicar o fusionar a otras ramas. No se hicieron commits, pushes, merges ni despliegues en este paso. No se comprobó el sitio remoto ni un teléfono físico. Las simulaciones se recuperan al recargar mientras siga vivo el servidor; no persisten después de reiniciarlo.

`fcfs.md` y las guías de entrega conservan descripciones de etapas anteriores que todavía señalan el frontend pendiente; el código revisado y este estado acreditan la integración local actual. El plan y el alcance no cambiaron.
