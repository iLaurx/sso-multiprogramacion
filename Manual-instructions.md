**SSO / ACTIVIDAD 4 / MANUAL DEL EQUIPO**

**SEMINARIO DE SISTEMAS OPERATIVOS · ACTIVIDAD 4 · PROGRAMA 2**

# Manual de trabajo para equipo de tres

### Simulación de multiprogramación por lotes

Python para el motor, FastAPI para la API y HTML/CSS/JavaScript para la interfaz. Trabajo colaborativo con GitHub y pruebas con pytest.

**Objetivo:** que los tres integrantes puedan preparar su equipo, dividir el trabajo, integrar los módulos y comprobar una entrega fiel al enunciado.

## Cómo leer este manual

**Requisito del enunciado:** comportamiento solicitado en *actividad 4 SSO.pdf*, de dos páginas. **Decisión** **propuesta:** una elección de este manual para implementar el proyecto web; puede ajustarse de común acuerdo sin cambiar los requisitos.

Los nombres Integrante 1, 2 y 3 son roles. Sustitúyanlos por sus nombres en el repositorio y el reporte. Los comandos están escritos para **PowerShell en Windows** y se ejecutan desde la raíz del proyecto, salvo indicación distinta.

|Ruta de lectura|Páginas|
|---|---|
|Qué debe hacer el programa y qué falta confirmar|2-3|
|Arquitectura y responsabilidades|4-5|
|Instalación, repositorio e inicio ejecutable|6-10|
|Ramas, commits, PR, review, merge y actualización|11-12|
|Motor, API, JSON e interfaz|13-16|
|Fases, pruebas y entrega|17-19|
|Fuentes y alcance de la verificación|20|

## Primer acuerdo del equipo

Asignar los roles de la página 5. El Integrante 2 crea el repositorio y prepara la base mínima; los otros dos esperan su primer PR integrado antes de abrir sus ramas de desarrollo. Después trabajan en paralelo sobre el contrato JSON acordado.

Fecha de preparación: 8 de octubre de 2026.

Multiprogramación por lotes · Equipo de tres 1 / 20

**REQUISITOS DEL ENUNCIADO · PDF ORIGINAL, PÁGINA 1**

# 1. Requisitos de la simulación

|Referencia|Comportamiento que deben conservar|
|---|---|
|R1|Preguntar el número inicial de trabajos y formar lotes de máximo 3 procesos. El último lote puede contener 1 o 2.|
|R2|Generar internamente los datos de cada trabajo: ID único (puede ser consecutivo), TME aleatorio mayor que 0 en el rango 7 a 18, operación aleatoria y operandos válidos. Operaciones: +, -, *, / y residuo.|
|Nota de R2|Ya no se captura el nombre del programador. El usuario introduce la cantidad inicial, no los datos de cada proceso.|
|R3|Ejecutar los trabajos conforme a su ID asignado. La interrupción de R6 modifica la cola del lote actual.|
|R4-R5|El proceso en ejecución puede ser interrumpido por entrada/salida o terminado por error. Estas acciones se generan mediante teclas.|

## Teclas obligatorias (R6)

Tecla Efecto

I Sacar el proceso del procesador y colocarlo al final de la cola de procesos del **lote actual**. Conservar lo que ya ejecutó.

E Terminar por error al proceso en ejecución y mostrarlo en terminados con **ERROR** en lugar de un resultado.

P Detener momentáneamente la simulación.

C Reanudar la simulación pausada con P.

**Interpretación fiel de I:** el enunciado pide reencolar en el mismo lote. No establece una cola de bloqueados con espera fija, un quantum ni Round Robin. No agregarlos como requisitos de esta actividad.

TME significa Tiempo Máximo Estimado. En este manual se propone representarlo con segundos simulados enteros e incluir ambos extremos del rango 7-18.

Multiprogramación por lotes · Equipo de tres 2 / 20

**REQUISITOS DEL ENUNCIADO · PDF ORIGINAL, PÁGINAS 1-2**

# 2. Pantalla, cierre y puntos abiertos

|Referencia|Información o conducta obligatoria|
|---|---|
|R7a|Espera del lote actual: número de programa/ID, TME y tiempo restante. Sin ejecución previa, restante = TME; tras I, mostrar lo que falta; al terminar, restante = 0.|
|R7b|Cantidad de lotes pendientes por ejecutar. Cuando no existan, mostrar 0.|
|R7c|Proceso en ejecución: todos sus datos, tiempo ya ejecutado y tiempo restante.|
|R7d|Terminados: ID, operación y resultado; si se terminó con E, mostrar ERROR.|
|R7e|Reloj o contador general visible.|
|R8-R9|Al acabar el lote, continuar con el siguiente. Cuando terminen todos los lotes, detener/pausar la simulación y conservar la información final.|
|Reporte|Datos personales, datos de la materia, número de actividad, objetivo, notas del lenguaje utilizado, TDA o estructuras y conclusiones.|

## Límites de lo que se recibió

R1 remite a los requisitos del **Programa 1**, pero ese documento no está adjunto. Este manual cubre lo explícito del Programa 2; antes de entregar, revisar el Programa 1 con la docente por si contiene condiciones adicionales.

El PDF no fija rango de operandos, precisión de resultados, unidad del reloj, tamaño máximo de entrada ni conducta de I/E mientras está pausado. Las siguientes reglas son propuestas para que los módulos coincidan:

**Entrada:** entero positivo. **Operandos:** enteros entre -99 y 99; regenerar el segundo operando si es 0 en división o residuo. Usar / como división real y % como residuo de Python; explicar su comportamiento con negativos. Mostrar división con hasta 4 decimales sin modificar el valor calculado.

**Control:** mientras está pausado, solo C reanuda; I/E se rechazan. Al finalizar, C no reinicia. Un reinicio requiere crear una simulación nueva. Si la docente define otra regla para estos puntos, actualizar el contrato y sus pruebas.

Multiprogramación por lotes · Equipo de tres 3 / 20

**DECISIÓN PROPUESTA / GUÍA DE TRABAJO**

# 3. Stack y arquitectura

|Tecnología|Uso y límite|
|---|---|
|Python 3.12.x|Versión propuesta común para los tres. El motor usa biblioteca estándar: dataclasses, collections.deque, random y operaciones explícitas.|
|FastAPI + Uvicorn|API HTTP, validación con modelos Pydantic, estado en memoria y reloj de la simulación en el servidor.|
|HTML / CSS / JS|Formulario, paneles y teclas. JavaScript consulta la API con fetch y representa el JSON recibido.|
|pytest + httpx|Pruebas del motor y de endpoints con TestClient. httpx permite usar el cliente de pruebas de FastAPI.|
|Git + GitHub / VS Code|Historial y colaboración / edición, terminal e intérprete .venv.|

Navegador: HTML + CSS + JavaScript | HTTP: fetch, solicitudes/respuestas JSON v FastAPI: rutas -> servicio de simulación | llamadas Python, sin HTTP interno v Motor puro: procesos, lotes, colas, tick y eventos

## Quién conserva el estado y avanza el tiempo

El **backend** es la única autoridad. Una tarea periódica del servidor llama a **engine.tick()** una vez por segundo real para avanzar un segundo simulado. La tarea solo avanza simulaciones running; en paused o completed no modifica tiempos.

La interfaz consulta el estado aproximadamente cada segundo. **GET no avanza el reloj** y el navegador no suma tiempos. Así una recarga o dos consultas no duplican la ejecución.

Cada simulación tiene un ID, su motor y un bloqueo de exclusión mutua. El servicio serializa tick y acciones para evitar cambios simultáneos. El motor no importa FastAPI, no hace sleep y no conoce el navegador.

Alcance propuesto: aplicación local con estado en memoria y **un solo proceso servidor**. No hace falta base de datos, Node.js, React ni Docker. Reiniciar el servidor o usar --reload borra las simulaciones. Recargar el navegador no las borra; conservar el ID en sessionStorage y consultar su estado.

Referencia técnica: FastAPI, primeros pasos y archivos estáticos; fuentes enlazadas en página 20.

Multiprogramación por lotes · Equipo de tres 4 / 20

# 4. Responsabilidades precisas

Integrante Entrega y archivos propios

1 · Motor Python **simulation/**: modelos, generador aleatorio, lotes de 3, cola, tick, I/E/P/C, cambio de lote y fin. **tests/test_engine.py** y fixtures del motor. Entrega un motor usable sin servidor.

2 · API e integración **backend/**: schemas, rutas, servicio, reloj y exclusión mutua. Sirve frontend. **tests/test_api.py**, requirements y base del repositorio. Mantiene docs/contrato-api.md y coordina integración.

3 · Frontend y evidencia **frontend/**: formulario, paneles, fetch, teclas, errores de red y estado visual. Mantiene docs/evidencias/ y borrador del reporte. Verifica todos los controles en navegador.

## Contrato entre 1 y 2

El Integrante 1 publica **SimulationEngine** con create(numero_trabajos, seed=None), tick(), interrupt(), fail(), pause(), resume() y snapshot(). create construye un motor running en tiempo 0; tick avanza exactamente una unidad. snapshot devuelve datos simples serializables; no modifica el estado. El Integrante 2 adapta snapshot al JSON de la página 15.

## Contrato entre 2 y 3

El Integrante 2 acuerda primero rutas, acciones, campos, estados y códigos de error de las páginas 14-15. El Integrante 3 puede usar un fixture JSON temporal, marcado como prueba visual, hasta conectar la API. Los cambios del contrato se revisan con ambos compañeros.

## Revisiones cruzadas y trabajo compartido

**PR del motor:** revisa 2. **PR de API:** revisa 1. **PR de interfaz:** revisa 2; 1 confirma que los datos y acciones respetan el motor. Si 2 es autor, otro integrante aprueba; nadie aprueba su propio PR.

Cada integrante escribe sus pruebas y la sección del reporte sobre su módulo. El Integrante 3 integra el texto, 2 comprueba instrucciones de ejecución y 1 valida el comportamiento. Los tres revisan la entrega completa.

Evitar editar archivos ajenos sin avisar. requirements.txt, README.md y contrato-api.md tienen coordinación del Integrante 2. Un responsable por archivo reduce conflictos; todos pueden proponer cambios mediante PR.

Multiprogramación por lotes · Equipo de tres 5 / 20

# 5. Preparar Windows y VS Code

**Lo hace cada integrante una vez.** Necesitan conexión para descargar herramientas y dependencias; después la simulación se ejecuta localmente.

**1.** Crear o usar una cuenta de GitHub. **2.** Instalar Git for Windows desde git-scm.com/install/windows; permitir su uso en la terminal y conservar el administrador de credenciales incluido.
**3.** Instalar Python 3.12.x de 64 bits con instalador oficial para Windows. Elegir la misma versión menor los tres, incluir pip y habilitar PATH si el instalador ofrece esa opción. Obtenerlo desde python.org/downloads/windows. No instalar Python en una carpeta del repositorio.
**4.** Instalar VS Code desde code.visualstudio.com. En Extensions instalar **Python de Microsoft** y comprobar Pylance. Habilitar el comando code en PATH si el instalador lo ofrece.
**5.** Cerrar y volver a abrir terminales para que reconozcan las instalaciones. En PowerShell comprobar: git --version py -3.12 --version py -3.12 -m pip --version code --version Si py no existe, probar python --version y confirmar que corresponde a 3.12. En ese caso usar python en lugar de py -3.12 para crear .venv. Si code no existe, abrir VS Code desde Inicio y usar File > Open Folder.
## Identificar los commits

Reemplazar los textos de ejemplo por el nombre y el correo asociado a GitHub; también pueden usar su correo privado noreply indicado por GitHub.

git config --global user.name "Tu Nombre" git config --global user.email "tu-correo-de-github" git config --global --get user.name git config --global --get user.email

Al hacer el primer push por HTTPS, completar el acceso en el navegador si Git lo solicita. La contraseña normal de GitHub no funciona como contraseña de Git por HTTPS. No colocar credenciales en archivos o en la URL del repositorio.

Multiprogramación por lotes · Equipo de tres 6 / 20

# 6. GitHub, clone y ramas

## El Integrante 2 crea el repositorio

**1.** En GitHub, New repository: nombre propuesto **sso-multiprogramacion**. Elegir visibilidad según la entrega y habilitar README. No hace falta crear otro repositorio por integrante.
**2.** Confirmar que la rama principal se llama **main**. En Settings > Collaborators (o Manage access), invitar a los otros dos usuarios; deben aceptar la invitación. Configurar PR y una aprobación requerida si el plan y la visibilidad lo permiten; si no, mantener esa regla por acuerdo.
**3.** En Code > HTTPS copiar la URL real. Todos la usan. En los comandos siguientes, cambiar **USUARIO** por el propietario real del repositorio. New-Item -ItemType Directory -Force "$HOME\Documents\Proyectos" Set-Location "$HOME\Documents\Proyectos" git clone [https://github.com/USUARIO/sso-multiprogramacion.git](https://github.com/USUARIO/sso-multiprogramacion.git) Set-Location sso-multiprogramacion git remote -v git branch --show-current code.
## Preparar primero la base común

El Integrante 2 crea la rama de preparación y agrega los archivos de las páginas 7-10 y la prueba health de la página 18. Publica su PR; el Integrante 1 lo revisa y se integra en main. Solo entonces los tres abren sus ramas de módulos.

git switch main git pull --ff-only origin main git switch -c feature/i2-base-proyecto

## Rama inicial de cada módulo

Después del merge de la base, ejecutar switch main y pull como arriba. Luego cada integrante ejecuta **solo** **su comando**:

# Integrante 1 git switch -c feature/i1-motor-lotes # Integrante 2 git switch -c feature/i2-api-simulacion # Integrante 3 git switch -c feature/i3-interfaz

main reúne lo probado. Una rama feature contiene una tarea concreta. Al terminarla, crear otra rama desde main actualizado; no mantener una única rama por persona durante todo el proyecto.

Multiprogramación por lotes · Equipo de tres 7 / 20

# 7. Carpetas e inicialización

El Integrante 2 crea esta base en su rama. simulation/ y backend/ son paquetes Python gracias a sus archivos __init__.py vacíos.

sso-multiprogramacion/ simulation/ __init__.py models.py # procesos y estados generator.py # trabajos aleatorios válidos engine.py # lotes, cola, tick y eventos backend/ __init__.py main.py # app y archivos estáticos schemas.py # entrada/salida JSON routes.py # endpoints /api service.py # motores, reloj y bloqueos frontend/ index.html styles.css app.js tests/ test_health.py # prueba de arranque test_engine.py test_api.py docs/ contrato-api.md evidencias/ reporte.md .gitignore requirements.in # dependencias directas requirements.txt # versiones resueltas README.md .venv/ # local; nunca se sube

Crear directorios y paquetes desde la raíz. Los archivos de módulos se agregan al implementar cada fase; no generar pruebas vacías como si fueran pruebas aprobadas.

New-Item -ItemType Directory -Force simulation,backend,frontend New-Item -ItemType Directory -Force tests,docs,docs/evidencias New-Item -ItemType File simulation/__init__.py New-Item -ItemType File backend/__init__.py py -3.12 -m venv .venv .\.venv\Scripts\Activate.ps1 python -c "import sys; print(sys.executable)"

El último comando debe señalar .venv\Scripts\python.exe. En VS Code: Ctrl+Shift+P > Python: Select Interpreter > ese intérprete. Si PowerShell bloquea Activate.ps1, usar directamente .\.venv\Scripts\python.exe en todos los comandos; no es necesario cambiar la política del sistema.

Multiprogramación por lotes · Equipo de tres 8 / 20

# 8. Dependencias y backend mínimo

## Archivos de preparación

Crear **.gitignore** con este contenido antes de agregar archivos a Git:

.venv/ __pycache__/ *.py[cod] .pytest_cache/ .coverage htmlcov/ .env .vscode/

Crear **requirements.in**. No se inventan versiones exactas: el Integrante 2 resolverá y guardará las de la instalación común en requirements.txt.

fastapi uvicorn[standard] pytest httpx

Solo el Integrante 2 genera la primera lista fija en un entorno nuevo:

python -m pip install --upgrade pip python -m pip install -r requirements.in python -m pip freeze > requirements.txt

Los otros dos, tras actualizar main, crean su propia .venv y ejecutan **python -m pip install -r** **requirements.txt**. No copiar .venv entre equipos. Si cambian dependencias, actualizar ambas listas y revisarlas en un PR.

## Crear backend/main.py

from pathlib import Path from fastapi import FastAPI from fastapi.staticfiles import StaticFiles

app = FastAPI(title="SSO-Multiprogramacion")

@app.get("/api/health") def health(): return {"status": "ok"}

frontend = Path(__file__).resolve().parents[1] / "frontend" app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")

Esta base prueba que Python sirve una página y una ruta. **Todavía no simula procesos.** Al agregar la API, registrar sus rutas /api y el ciclo de vida del servicio **antes** de montar /; el montaje raíz debe quedar al final.

Multiprogramación por lotes · Equipo de tres 9 / 20

# 9. Primera ejecución local

## Crear frontend/index.html

<!doctype html> <html lang="es"> <head> <meta charset="utf-8"> <meta name="viewport" content="width=device-width, initial-scale=1"> <title>SSO-Multiprogramación</title> </head> <body> <h1>Simulación por lotes</h1> <p id="estado">Comprobando API...</p> <script src="/app.js"></script> </body> </html>

## Crear frontend/app.js

async function comprobarApi() { const salida = document.querySelector("#estado"); try { const respuesta = await fetch("/api/health"); if (!respuesta.ok) throw new Error("API no disponible"); const datos = await respuesta.json(); salida.textContent = `API: ${datos.status}`; } catch (error) { salida.textContent = error.message; } } comprobarApi();

## Arrancar y comprobar

python -m uvicorn backend.main:app --reload # Detener el servidor con Ctrl+C en esta terminal.

Abrir **[http://127.0.0.1:8000/**:](http://127.0.0.1:8000/**:) debe aparecer API: ok. Abrir **[http://127.0.0.1:8000/api/health**:](http://127.0.0.1:8000/api/health**:) debe devolver {"status":"ok"}. La documentación de rutas está en **[http://127.0.0.1:8000/docs**](http://127.0.0.1:8000/docs**). Mantener la terminal del servidor abierta.

No abrir index.html mediante doble clic. FastAPI sirve interfaz y API desde el mismo origen, así fetch usa rutas relativas y no se necesita configurar CORS para este diseño. --reload es útil al desarrollar; para la demo final ejecutar el mismo comando sin --reload y sin varios workers.

Multiprogramación por lotes · Equipo de tres 10 / 20

# 10. Commits, push y pull request

## Rutina en una rama feature

Ejemplo del Integrante 1, cuando engine.py y sus pruebas ya existen. Los otros integrantes sustituyen la rama y las rutas por las de su tarea.

git branch --show-current git status python -m pytest -q git diff git add simulation/ tests/test_engine.py git diff --cached git commit -m "feat: formar lotes y conservar tiempo al interrumpir" git push -u origin feature/i1-motor-lotes

**Commit:** guarda una unidad de cambio en la computadora. **Push:** publica los commits de la rama en GitHub. -u vincula la rama local con la remota; después basta con git push. Revisar lo preparado antes de confirmar, especialmente que no incluya .venv.

En el PR de la base, el Integrante 2 agrega backend/main.py, frontend/index.html, frontend/app.js, tests/test_health.py, los __init__.py, .gitignore, requirements.in, requirements.txt y README.md; publica feature/i2-base-proyecto con la misma secuencia.

## Abrir el PR en GitHub

**1.** Ir al repositorio > Pull requests > New pull request (o Compare & pull request). **2.** Seleccionar base: **main** y compare: la rama feature. **3.** Comprobar los archivos y describir qué cambia, por qué y cómo se probó. **4.** Seleccionar al revisor de la página 5 y crear el PR.
### Descripción sugerida:

Problema: al interrumpir se perdía el tiempo acumulado. Cambio: el proceso vuelve al final de la cola del lote y conserva ejecutado/restante. Verificación: prueba con 3 procesos, tick de 2 segundos, I y reanudación; indicar el resultado real de pytest.

## Atender la revisión

El revisor lee Files changed y ejecuta las pruebas en su equipo. Con cambios correctos: Review changes > Approve > Submit review. Si encuentra fallos, pide ajustes. El autor modifica su misma rama, hace otro commit y git push; el PR se actualiza. Volver a revisar cambios posteriores a la aprobación.

Para probar el PR del motor, el revisor usa su copia con cambios locales guardados y un nombre de rama de revisión nuevo:

git fetch origin git switch -c review/i1-motor origin/feature/i1-motor-lotes python -m pip install -r requirements.txt python -m pytest -q git switch main

Regla del equipo: los commits van a feature; la integración a main se hace por PR con revisión. No hacer push directo a main.

Multiprogramación por lotes · Equipo de tres 11 / 20

# 11. Merge, actualización y conflictos

## Integrar y recuperar main

Con aprobación, pruebas aprobadas y sin conflictos, el Integrante 2 coordina el merge en GitHub: **Merge** **pull request > Confirm merge**. Usar Create a merge commit de forma consistente. Si él es autor, otro integrante comprueba y realiza la integración. Después se puede eliminar la rama remota integrada.

# Cada integrante, con sus cambios guardados en commits: git status git switch main git pull --ff-only origin main python -m pip install -r requirements.txt python -m pytest -q # Para otra tarea, elegir un nombre NUEVO: git switch -c feature/i1-pruebas-interrupcion

## Actualizar una feature que sigue en desarrollo

Ejemplo: la rama del motor sigue abierta y ya entró un PR de la API. No basta con actualizar main: hay que integrar esos cambios en la feature.

# En feature/i1-motor-lotes; primero guardar el trabajo: git status git fetch origin git merge origin/main python -m pip install -r requirements.txt python -m pytest -q git push

## Si el merge reporta conflicto

**1.** git status muestra los archivos. **2.** Abrirlos en VS Code y usar el editor de conflictos para combinar lo necesario. No elegir automáticamente todo un lado. **3.** Quitar marcadores <<<<<<<, ======= y >>>>>>>, guardar y comprobar el comportamiento. **4.** Preparar solo las rutas resueltas: git add backend/schemas.py # La ruta anterior es un ejemplo; usar la del conflicto. python -m pytest -q git commit -m "merge: integrar main y resolver contrato" git push Si no está claro cómo resolverlo, git merge --abort cancela ese merge antes de confirmarlo; acordar la solución con el autor. No usar reset --hard o push --force para actualizar la rama. Si pull --ff-only falla en main, inspeccionar git status y git log --oneline --all --graph antes de corregir la divergencia.
Multiprogramación por lotes · Equipo de tres 12 / 20

# 12. Construir el motor puro

## Orden de implementación del Integrante 1

**1. Modelos.** Process: id, lote, operacion, operando_a, operando_b, tme, ejecutado, estado y resultado. Estados: ready, running, finished, error. Motor: clock, status, lotes, cola actual, proceso actual y lista de terminados.
**2. Generación.** Validar cantidad como entero positivo, asignar IDs 1..N, elegir TME con randint(7,18), operación y operandos. Crear un random.Random(seed) propio para repetir pruebas sin afectar el generador global. Dividir en grupos consecutivos de máximo 3; inicialmente ordenar por ID.
**3. Inicio.** Activar el primer lote y sacar su primer proceso de la cola. create deja clock=0 y ejecutado=0. Lotes pendientes excluye el lote activo: al inicio es ceil(N/3)-1. Para N=4: lote 1 contiene 1,2,3; lote 2 contiene 4; pendientes=1.
**4. tick().** Si status no es running, no cambiar nada. Si está ejecutando, sumar 1 a clock y a ejecutado. Al alcanzar TME, calcular el resultado con funciones de operación explícitas, marcar finished y mover a terminados. Despachar el siguiente sin gastar un segundo adicional.
**5. I.** Reencolar el actual al final del mismo lote, conservar ejecutado y despachar el siguiente. Con un solo proceso vivo, vuelve a ejecutarse él mismo. I no suma tiempo al reloj.
**6. E.** Marcar error, resultado=null y mover a terminados; la interfaz muestra ERROR. Conservar ejecutado real aunque sea menor que TME. Despachar el siguiente. E tampoco agrega un tick.
**7. Cambio y fin.** Si no hay actual ni cola, cargar el siguiente lote. Si no queda ninguno, status=completed, actual=null y pendientes=0; mantener reloj y terminados. P cambia a paused y C vuelve a running solo desde paused. **Invariantes:** IDs únicos; un solo proceso running; ningún proceso aparece en dos ubicaciones; 0 ≤ ejecutado ≤ TME; restante = TME-ejecutado para procesos vivos y **0 para cualquier terminado**, incluido error. No aumentar ejecutado artificialmente hasta TME al aplicar E. Cada lote permanece activo hasta que todos sus procesos terminan normalmente o por error. Proponer restantes en snapshot como valor derivado para evitar inconsistencias. No usar eval para calcular operaciones.
Multiprogramación por lotes · Equipo de tres 13 / 20

# 13. Endpoints propuestos

El Integrante 2 implementa estas rutas después del arranque mínimo. Todas las rutas /api trabajan con JSON. **No son exigencias del PDF**: son el contrato propuesto del proyecto web.

Método y ruta Entrada / salida

GET /api/health 200: {"status":"ok"}. Comprueba que la aplicación está disponible.

POST /api/simulations Entrada: {"numero_trabajos":4,"seed":123}. seed es opcional y se omite en el uso normal. 201: snapshot inicial completo, con simulacion_id; inicia en running y tiempo 0.

GET /api/simulations/{id} 200: snapshot. Solo lee; no llama tick. 404 si el ID no existe.

POST /api/simulations/{id}/actions Entrada: {"accion":"interrupt"}. Valores: interrupt, error, pause, continue. 200: snapshot después de aplicar la acción. No hay endpoint público de tick.

## Errores del contrato

**422:** cantidad no entera/positiva, acción fuera del enum o JSON inválido. Usar validación estricta para no aceptar true o 2.5 como cantidad entera. **404:** simulación inexistente. **409:** I/E sin proceso activo, en pausa o tras finalizar; C tras completed. P estando paused y C estando running pueden devolver el estado sin cambios como acciones idempotentes propuestas.

Respuesta controlada de ejemplo: {"detail":"La simulación está pausada"}. Los errores 422 de Pydantic pueden devolver detail como lista: la interfaz debe poder mostrar ambos formatos. No confundir un error HTTP con un proceso terminado por E.

## Servicio y ciclo de vida

service.py conserva motores por ID. En el lifespan de FastAPI, iniciar la tarea del reloj y cancelarla al apagar el servidor. tick y actions adquieren el mismo bloqueo por simulación. Serializar el snapshot dentro del bloqueo para no devolver datos a mitad de una transición.

Usar un solo worker: varios procesos tendrían memorias y relojes distintos. Para pruebas de la API, permitir desactivar el reloj automático y avanzar manualmente desde el servicio de pruebas. No exponer ese control en la interfaz final.

Si hay un límite de cantidad por rendimiento, acordarlo y documentarlo como decisión adicional; no atribuir al enunciado un máximo que no especifica.

Multiprogramación por lotes · Equipo de tres 14 / 20

# 14. JSON compartido por los tres

Guardar este esquema de ejemplo en docs/contrato-api.md. Es un **fixture ilustrativo** con 4 trabajos y 2 segundos ejecutados; no es la salida garantizada de seed=123. El futuro lote 2 contiene el ID 4 y no aparece en la cola del lote 1.

{ "simulacion_id": "demo-001", "estado": "running", "reloj": 2, "lote_actual": 1, "lotes_pendientes": 1, "total_trabajos": 4, "en_ejecucion": { "id": 1, "lote": 1, "estado": "running", "operacion": "+", "operando_a": 8, "operando_b": 3, "tme": 7, "ejecutado": 2, "restante": 5, "resultado": null }, "en_espera": [ { "id": 2, "lote": 1, "estado": "ready", "operacion": "*", "operando_a": 4, "operando_b": 2, "tme": 10, "ejecutado": 0, "restante": 10, "resultado": null }, { "id": 3, "lote": 1, "estado": "ready", "operacion": "%", "operando_a": 9, "operando_b": 4, "tme": 8, "ejecutado": 0, "restante": 8, "resultado": null }], "terminados": [] }

## Reglas de campos

**estado de simulación:** running, paused o completed. **en_ejecucion:** objeto o null. **en_espera:** solo procesos ready del lote actual, en orden real de cola. **terminados:** acumulados de todos los lotes, en orden de terminación. En completed, lote_actual=null, en_espera=[] y en_ejecucion=null.

Proceso finished: resultado numérico y restante=0. Proceso error: resultado=null y restante=0; mostrar ERROR por su estado, no por la ausencia de un número. Antes de terminar, resultado=null. / devuelve resultado real; % representa residuo. Tiempos enteros, IDs de procesos enteros y simulacion_id cadena.

Multiprogramación por lotes · Equipo de tres 15 / 20

# 15. Interfaz y comunicación

## Diseño de pantalla del Integrante 3

**Antes de iniciar:** campo de cantidad entera positiva y botón Iniciar. No solicitar nombre del programador, operación, operandos ni TME. **Durante:** reloj, estado, lote actual y lotes pendientes; tabla de espera; panel completo del proceso actual; tabla de terminados. Mantener las teclas I/E/P/C y mostrarlas como ayuda visible.

Crear con POST /api/simulations. Guardar el simulacion_id y dibujar la respuesta. Consultar GET periódicamente; tras una acción, dibujar su respuesta. Usar textContent para datos del servidor y formatar resultados al mostrar. Los botones equivalentes a las teclas son una ayuda propuesta, no reemplazan el teclado.

## Envío de una acción: ejemplo

async function enviarAccion(id, accion) { const respuesta = await fetch( `/api/simulations/${id}/actions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ accion }) }); const datos = await respuesta.json(); if (!respuesta.ok) { const detalle = typeof datos.detail === "string" ? datos.detail : JSON.stringify(datos.detail); throw new Error(detalle || "No se pudo aplicar la acción"); } return datos; }

## Reglas para evitar errores de integración

**Teclado:** normalizar event.key a mayúscula; I→interrupt, E→error, P→pause, C→continue. Ignorar event.repeat y eventos originados en input, textarea o elementos editables. Capturar teclas solo con una simulación seleccionada.

**Solicitudes:** serializar acciones y consultas en una sola cola o control de petición en curso. Pausar nuevas consultas mientras se envía una acción; descartar respuestas antiguas. Programar el siguiente GET al terminar el anterior con setTimeout para evitar solapamientos.

**Pausa y fin:** P no detiene la consulta de estado, detiene el motor. En completed detener la consulta periódica y conservar la pantalla. Un fallo de red se muestra con opción de reintentar; no recalcular el motor en JavaScript. Dos pestañas no duplican el reloj, pero pueden enviar controles: usar una pestaña de control para la demo.

Multiprogramación por lotes · Equipo de tres 16 / 20

# 16. Plan de trabajo por fases

No se fija una fecha de entrega que el enunciado no proporciona. Avanzar por resultados verificables; cada fase termina con una revisión y un PR integrado cuando corresponda.

|Fase|Quién hace qué|Criterio de salida|
|---|---|---|
|0 · Acuerdos|Los tres leen el PDF, asignan roles y revisan la referencia al Programa 1. 2 escribe el contrato con 1 y 3.|Reglas ambiguas y campos JSON documentados; cada uno entiende su módulo.|
|1 · Base|2 crea repo, estructura, dependencias y arranque mínimo. 1 revisa; 3 prueba clone y ejecución.|main puede clonarse; página muestra API: ok; prueba health aprobada.|
|2 · Motor|1 implementa y prueba el motor. 2 prepara schemas y servicio. 3 construye paneles con fixture.|Motor prueba lotes, I/E/P/C, tiempos y cierre; interfaz representa el contrato.|
|3 · API|2 integra motor, rutas, reloj y bloqueos. 1 revisa integración; 3 reemplaza fixture por fetch.|Crear, consultar y controlar funciona desde /docs; GET no avanza tiempo.|
|4 · Integración|3 conecta pantalla y teclas; 1 compara con casos esperados; 2 resuelve problemas de contrato.|Recorrido completo en navegador; campos fieles y sin tiempos duplicados.|
|5 · Entrega|Los tres prueban un clone limpio. 3 reúne evidencias y reporte; 1 y 2 revisan.|Pruebas y checklist aprobados; README y reporte reflejan la versión final.|

## Coordinación diaria breve

Cada integrante informa qué terminó, cuál es su siguiente tarea y si depende de otro módulo. Abrir una issue por tarea con criterio de aceptación y responsable. Enlazar la issue en el PR. Integrar cambios pequeños para no acumular tres módulos incompatibles al final.

Prioridad: funcionamiento correcto del motor, después contrato/API y después acabado visual. El frontend puede progresar con un fixture; la integración definitiva requiere pruebas contra el motor real.

Multiprogramación por lotes · Equipo de tres 17 / 20

# 17. Pruebas y evidencia

## Primera prueba ejecutable: tests/test_health.py

from fastapi.testclient import TestClient from backend.main import app

def test_health(): with TestClient(app) as client: respuesta = client.get("/api/health") assert respuesta.status_code == 200 assert respuesta.json() == {"status": "ok"}

python -m pytest -q python -m pytest tests/test_engine.py -q python -m pytest tests/test_api.py -q

El primer comando sirve desde la base. Los otros se usan cuando existan esas pruebas. Ninguna prueba recolectada o un fallo no cuenta como aprobación. Para lógica, inyectar trabajos conocidos o seed; no depender de esperar segundos reales.

|Responsable|Casos mínimos y resultado esperado|
|---|---|
|1 · Motor|N=1,3,4,7: tamaños ≤3 y pendientes correctos. IDs únicos. TME 7-18. Divisor de / y % nunca 0. Orden inicial por ID y operaciones correctas.|
|1 · Motor|Tras 2 ticks con TME=7: ejecutado=2, restante=5. I conserva ambos y coloca al final; con cola [2,3], sigue 2 y espera [3,1]. I con único vivo no lo pierde.|
|1 · Motor|E crea error sin resultado y restante=0. P congela reloj/ejecutado aunque se invoquen ticks; C continúa. Siguiente lote y completed tras agotar todos, con reloj estable.|
|2 · API|201 al crear; 200 al consultar/actuar; 422 entradas inválidas; 404 ID ausente; 409 control incompatible. GET repetido no avanza reloj con scheduler desactivado. Dos solicitudes no corrompen el estado.|
|3 · Navegador|Probar I/E/P/C reales, sin repetición por mantener tecla; cifras y columnas completas; ERROR visible; pausa estable; refresh recupera ID; aviso por API caída y final conservado.|

Guardar evidencias reales de la pantalla inicial, interrupción con restante conservado, terminación ERROR, pausa/continuación, cambio de lote y final. Registrar también el resultado de pytest y el commit probado. Una captura aislada no reemplaza el recorrido.

Multiprogramación por lotes · Equipo de tres 18 / 20

# 18. Checklist de entrega y reporte

## Programa y repositorio

[] Entrada de cantidad; generación interna válida; sin nombre del programador. [] Lotes ≤3; IDs únicos; orden inicial y reencolado I correctos. [] E muestra ERROR; P congela; C continúa; final detenido. [] Espera con ID/TME/restante; ejecución con todos los datos y tiempos. [] Lotes pendientes, terminados y reloj siempre visibles y correctos. [] Motor sin dependencias web; API y frontend respetan el JSON acordado. [] main contiene los PR revisados; no faltan archivos ni dependencias. [] README incluye instalación, ejecución, teclas, pruebas y limitaciones. [] .venv, cachés y credenciales fuera del repositorio.

## Comprobación desde una copia limpia

Usar otra carpeta o computadora y clonar el repositorio final. Ejecutar la secuencia siguiente. No reutilizar la .venv del autor ni modificar archivos para que funcione.

git clone [https://github.com/USUARIO/sso-multiprogramacion.git](https://github.com/USUARIO/sso-multiprogramacion.git) Set-Location sso-multiprogramacion py -3.12 -m venv .venv .\.venv\Scripts\python.exe -m pip install -r requirements.txt .\.venv\Scripts\python.exe -m pytest -q .\.venv\Scripts\python.exe -m uvicorn backend.main:app # En otra terminal, registrar la versión entregada: git rev-parse HEAD

## Reporte obligatorio, con extensión propuesta

**Exigido:** datos personales de los tres, datos de la materia, Actividad de Aprendizaje 4 / Programa 2, objetivo, notas del lenguaje, TDA/estructuras y conclusiones. No inventar nombres, grupo, códigos ni fecha de entrega.

**Propuesta de organización:** portada; objetivo; explicación breve de Python y del stack; estructuras usadas (proceso, lista de lotes, deque y estado); funcionamiento con teclas; pruebas y evidencias; conclusiones. Añadir enlace al repositorio y commit de entrega para reproducirla. Cada integrante explica su aportación.

Este manual es una guía para construir el programa. **No sustituye el reporte final ni certifica un** **software todavía no implementado.** Antes de entregar, revisar también las condiciones adicionales del Programa 1 y el medio/formato de entrega indicado por la docente.

Multiprogramación por lotes · Equipo de tres 19 / 20

# 19. Fuentes y alcance

## Fuente académica principal

**actividad 4 SSO.pdf**, 2 páginas. Centro Universitario de Ciencias Exactas e Ingenierías; Seminario de Sistemas Operativos; Actividad de Aprendizaje 4, Programa 2. Docente indicada: M. en C. Violeta del Rocío Becerra Velázquez. Se recuperó el adjunto de la conversación *Planeación Tech Lead Web*.

Las páginas 2-3 de este manual identifican los requisitos explícitos. El stack, los roles, carpetas, comandos, contrato HTTP/JSON, scheduler y fases son propuestas de implementación basadas en la solicitud del equipo. No se contó con el enunciado del Programa 1 ni con el texto de las respuestas anteriores, que el acceso a la conversación devolvió como referencias sin contenido.

## Documentación técnica oficial

Python: instalación para Windows Python: entornos virtuales y ejecución sin activarlos Git: instalación para Windows VS Code: soporte de Python GitHub: crear un repositorio GitHub: clone, fetch, merge y pull GitHub: crear pull requests GitHub: revisión y aprobación GitHub: resolver conflictos FastAPI: primeros pasos FastAPI: servir archivos estáticos FastAPI: pruebas con TestClient y httpx pytest: comenzar y ejecutar pruebas Enlaces consultados para preparar esta guía. Son clicables en el PDF; las versiones exactas del proyecto quedarán en requirements.txt.

## Qué se verifica en esta entrega

Se coteja el manual con las dos páginas del enunciado, se revisan los ejemplos y la consistencia entre roles, rutas y JSON, y se comprueban texto, paginación y representación visual del PDF. La ejecución funcional del proyecto corresponde a las fases y pruebas descritas, cuando el equipo lo implemente.

Multiprogramación por lotes · Equipo de tres 20 / 20
