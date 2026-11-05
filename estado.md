# Estado del proyecto

Última actualización: 4 de noviembre de 2026.

## Situación actual

**Actividad 6: motor, API y frontend FCFS integrados y comprobados localmente.** Integración para revisión en `codex/integracion-fcfs-frontend`, creada desde `origin/feature/fcfs` (`1e63119`) y fusionada mediante merge con `origin/feature/i3-interfaz` (`5d8012c`). Referencias actualizadas con fetch antes de comparar; las ramas locales coincidían con las remotas. Base común: `ccfec11`.

- `feature/fcfs` aporta siete commits: reglas/documentación, modelo, colas, memoria, bloqueo, tiempos y snapshot, revisión del motor y API/servicio, ejemplos y pruebas FCFS.
- `feature/i3-interfaz` aporta un commit con cambios en los tres archivos de frontend: diseño de cinco estados, métricas, controles, tabla de tiempos, historial y visualización Three.js. Se conserva ese trabajo y su estilo.
- No hubo conflictos textuales de Git. Se revisaron también los tres archivos fusionados automáticamente y se resolvieron incompatibilidades de contenido: `en_espera` para listos, `ejecutado` para servicio, `bloqueo_transcurrido`/`bloqueo_restante` para el bloqueo actual y `bloqueado` para el acumulado. Retirada la detección incorrecta del contrato y los mensajes/fallbacks de lotes.
- Se conservan orden de listas/terminados, null y cero; no se calculan tiempos en pantalla. La tabla final toma todos los tiempos del servidor. Memoria viene de `memoria_ocupada`, máximo tres; CPU libre con bloqueados mantiene consultas y P/C, I/E quedan deshabilitados. Solo `completed` cierra las consultas.
- Se conservan API y componentes existentes. Ante 409 se consulta el estado real; ante fallo de red en recuperación se conserva el ID y se reintenta; 404 limpia la simulación y permite crear otra. Pausa con CPU libre muestra que la simulación está detenida. La tabla tiene desplazamiento horizontal interno en móvil.
- Archivos propios de esta integración: `frontend/app.js`, `frontend/index.html`, `frontend/visualizacion.js`, `tests/browser_fcfs.py`, `README.md` y este estado. `simulation/`, `backend/`, contratos y pruebas previas permanecen idénticos a FCFS. Sin funciones de actividad 8.

## Comprobaciones

- Suite completa: **105 aprobadas**, ejecutando `.\.venv\Scripts\python.exe -m pytest -q`. Persiste un aviso de deprecación Starlette/HTTPX; sin fallos.
- Sintaxis de ambos JavaScript: `node --check` aprobada. `git diff --check`: sin errores.
- Dos recorridos en Chrome sin interfaz visible, contra Uvicorn local en puerto 8766 con su reloj automático real, sin endpoint de tick ni sustitución del motor: creación de cuatro procesos, nuevos y tres residentes, I/E/P/C por teclado, tres bloqueados y CPU libre, pausa que congela reloj/bloqueos, continuación y desbloqueo tras 10 segundos simulados, error con servicio real y admisión de nuevo, terminación normal y tabla final comparada celda por celda con la respuesta HTTP. El segundo recorrido terminó en orden **2, 3, 4, 1**, conservado en la tabla. Sin errores JavaScript.
- Se comprobaron recarga en pausa y al terminar, conflicto HTTP 409 real provocado desde otro cliente, recuperación tras interrupción de red y 404 de ID inexistente. Comprobación adicional de móvil a 390 px sin desbordamiento del documento y Three.js cargado. Capturas de escritorio, CPU libre pausada y móvil revisadas.
- Recorrido reproducible: `tests/browser_fcfs.py`, requiere servidor local iniciado y Playwright con Chrome local o Chromium. Playwright se instaló solo en `.venv`; no se añadió a dependencias del servidor. Evidencia local ignorada por Git en `tmp/fcfs-browser/`: capturas y `resultado.json` con el snapshot final real.

## Entrega y límites

Se deja un commit de merge en la rama nueva para revisión. Sin push, despliegue ni fusiones hacia main o feature/fcfs. El PDF local ajeno `output/pdf/Actividad_8_cambios_y_equipos.pdf` y `tmp/pdfs/` se conservaron y no se incorporaron al commit (tmp queda ignorado por las reglas existentes de FCFS).

No se comprobó el despliegue remoto ni un teléfono físico; las comprobaciones visuales fueron Chrome local y viewport móvil. Las simulaciones siguen en memoria: se recuperan al recargar la página mientras viva el servidor, no después de reiniciarlo. Las guías de entrega conservan la evidencia histórica de sus etapas; este archivo es el estado vigente. Pendiente: revisión del equipo antes de autorizar publicación o fusión a otras ramas.
