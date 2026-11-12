// Interfaz de simulación Round Robin; el servidor conserva la autoridad de estados y tiempos.

const API = "/api";
const ENDPOINT_HEALTH = "/api/health"; // Requerido para verificación en pytest

const elementos = {
  estadoApi: document.querySelector("#estadoApi"),
  apiDot: document.querySelector("#apiDot"),
  numeroTrabajos: document.querySelector("#numeroTrabajos"),
  quantum: document.querySelector("#quantum"),
  quantumElegido: document.querySelector("#quantumElegido"),
  btnIniciar: document.querySelector("#btnIniciar"),
  btnIniciarEmulacion: document.querySelector("#btnIniciarEmulacion"),
  btnAddProcess: document.querySelector("#btnAddProcess"),
  mensaje: document.querySelector("#mensaje"),
  reloj: document.querySelector("#reloj"),
  memoriaOcupada: document.querySelector("#memoriaOcupada"),
  capacidadMemoria: document.querySelector("#capacidadMemoria"),
  cantidadNuevos: document.querySelector("#cantidadNuevos"),
  totalTrabajos: document.querySelector("#totalTrabajos"),
  metricTerminados: document.querySelector("#metricTerminados"),
  estadoSimulacion: document.querySelector("#estadoSimulacion"),
  estadoControles: document.querySelector("#estadoControles"),
  estadoNuevos: document.querySelector("#estadoNuevos"),
  estadoListos: document.querySelector("#estadoListos"),
  estadoCpu: document.querySelector("#estadoCpu"),
  estadoBloqueados: document.querySelector("#estadoBloqueados"),
  estadoTerminados: document.querySelector("#estadoTerminados"),
  detalleEjecucion: document.querySelector("#detalleEjecucion"),
  bannerTexto: document.querySelector("#bannerTexto"),
  ayudaInterrupcion: document.querySelector("#ayudaInterrupcion"),
  tbodyResumen: document.querySelector("#tbodyResumen"),
  historialEventos: document.querySelector("#historialEventos"),
  btnInterrupt: document.querySelector("#btnInterrupt"),
  btnError: document.querySelector("#btnError"),
  btnPause: document.querySelector("#btnPause"),
  btnContinue: document.querySelector("#btnContinue")
};

let simulacionId = sessionStorage.getItem("simulacion_id");
let snapshotActual = null;
let ocupado = false;
let temporizador = null;
let historialLog = [];
let estadosAnteriores = new Map();
let estadoSimulacionAnterior = null;

// ==========================================
// 1. Registro de Eventos e Historial
// ==========================================
function registrarEvento(texto) {
  const reloj = snapshotActual?.reloj ?? 0;
  const entrada = `[${reloj}s] ${texto}`;

  historialLog.unshift(entrada);
  if (historialLog.length > 30) {
    historialLog.pop();
  }

  if (elementos.bannerTexto) {
    elementos.bannerTexto.textContent = texto;
  }

  if (elementos.historialEventos) {
    elementos.historialEventos.replaceChildren();
    historialLog.forEach(item => {
      const entrada = document.createElement("div");
      entrada.className = "history-entry";
      entrada.textContent = item;
      elementos.historialEventos.appendChild(entrada);
    });
  }
}

function mostrarMensaje(texto) {
  if (elementos.mensaje) {
    elementos.mensaje.textContent = texto;
  }
}

function mostrarError(error) {
  const detalle = error?.detail ?? error?.message ?? "Error desconocido";
  if (Array.isArray(detalle)) {
    return detalle.map(item => item.msg ?? JSON.stringify(item)).join("; ");
  }
  return String(detalle);
}

// ==========================================
// 2. Comunicación con el Backend
// ==========================================
async function solicitar(ruta, opciones = {}) {
  const respuesta = await fetch(`${API}${ruta}`, {
    ...opciones,
    headers: {
      "Content-Type": "application/json",
      ...opciones.headers
    }
  });

  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    if (respuesta.status === 404 && ruta.startsWith("/simulations/")) {
      limpiarSimulacion();
      throw { detail: "La simulación ya no existe. Inicia una nueva." };
    }
    throw { ...datos, status: respuesta.status };
  }
  return datos;
}

async function comprobarApi() {
  try {
    const respuesta = await fetch(ENDPOINT_HEALTH);
    if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
    const datos = await respuesta.json();

    if (elementos.estadoApi) {
      elementos.estadoApi.textContent = `API: ${datos.status}`;
      elementos.estadoApi.style.color = "var(--green)";
    }
    if (elementos.apiDot) {
      elementos.apiDot.className = "api-dot online";
    }
  } catch (error) {
    if (elementos.estadoApi) {
      elementos.estadoApi.textContent = `API no disponible: ${mostrarError(error)}`;
      elementos.estadoApi.style.color = "var(--pink)";
    }
    if (elementos.apiDot) {
      elementos.apiDot.className = "api-dot error";
    }
  }
}

// ==========================================
// 3. Renderizado del Diagrama y Tablas
// ==========================================
function formatearOperacion(proceso) {
  return `${proceso.operando_a} ${proceso.operacion} ${proceso.operando_b}`;
}

function procesarListas(snapshot) {
  const nuevos = Array.isArray(snapshot.nuevos) ? snapshot.nuevos : [];
  const listos = snapshot.en_espera || [];
  const cpu = snapshot.en_ejecucion ? [snapshot.en_ejecucion] : [];
  const bloqueados = Array.isArray(snapshot.bloqueados) ? snapshot.bloqueados : [];
  const terminados = Array.isArray(snapshot.terminados) ? snapshot.terminados : [];
  return { nuevos, listos, cpu, bloqueados, terminados };
}

function mostrarValor(valor, unidad = "s") {
  return valor === null || valor === undefined ? "—" : `${valor}${unidad}`;
}

function textoEstado(proceso, estadoLista) {
  if (estadoLista === "finished" && proceso.estado === "error") return "Terminado · ERROR";
  return ({ new: "Nuevo", ready: "Listo", running: "En CPU", blocked: "Bloqueado", finished: "Terminado", error: "Terminado · ERROR" })[estadoLista] || estadoLista;
}

function dibujarColumna(contenedor, procesos, estado, vacio, snapshot) {
  if (!contenedor) return;
  const tarjetaCpu = estado === "running" && procesos.length === 1
    ? contenedor.querySelector(`[data-cpu-id="${procesos[0].id}"]`) : null;
  if (!tarjetaCpu) contenedor.replaceChildren();
  if (!procesos.length) {
    const mensaje = document.createElement("div");
    mensaje.className = "state-empty";
    mensaje.textContent = vacio;
    contenedor.appendChild(mensaje);
    return;
  }
  procesos.forEach(proceso => {
    const tarjeta = tarjetaCpu || document.createElement("article");
    const esError = proceso.estado === "error";
    tarjeta.className = `state-process ${estado === "blocked" ? "blocked" : ""} ${estado === "finished" ? "finished" : ""} ${esError ? "error" : ""}`.trim();
    const restanteBloqueo = proceso.bloqueo_restante;
    const detalle = estado === "blocked"
      ? `Bloqueado ${mostrarValor(proceso.bloqueo_transcurrido)} · faltan ${mostrarValor(restanteBloqueo)}`
      : estado === "finished"
        ? (esError ? "ERROR" : `Resultado: ${mostrarValor(proceso.resultado, "")}`)
        : estado === "running"
          ? `Turno ${mostrarValor(snapshot.tiempo_turno)} / ${mostrarValor(snapshot.quantum)} · servicio ${mostrarValor(proceso.ejecutado)} · restante ${mostrarValor(proceso.restante)}`
          : `TME ${mostrarValor(proceso.tme)} · restante ${mostrarValor(proceso.restante)}`;
    if (estado === "running") {
      tarjeta.dataset.cpuId = proceso.id;
      if (!tarjetaCpu) {
        const texto = document.createElement("div");
        texto.className = "cpu-texto";
        const etiqueta = document.createElement("div");
        etiqueta.className = "cpu-progreso-texto";
        const barra = document.createElement("div");
        barra.className = "cpu-progreso";
        barra.setAttribute("role", "progressbar");
        barra.setAttribute("aria-label", `Tiempo ejecutado del proceso ${proceso.id}`);
        barra.setAttribute("aria-valuemin", "0");
        const relleno = document.createElement("div");
        relleno.className = "cpu-progreso-relleno";
        barra.appendChild(relleno);
        tarjeta.append(texto, etiqueta, barra);
      }
      tarjeta.querySelector(".cpu-texto").textContent = `P${proceso.id} · ${formatearOperacion(proceso)} · ${detalle}`;
      tarjeta.querySelector(".cpu-progreso-texto").textContent = `Turno ${mostrarValor(snapshot.tiempo_turno)} de ${mostrarValor(snapshot.quantum)} · faltan ${mostrarValor(proceso.restante)} · ${mostrarValor(proceso.ejecutado)} de ${mostrarValor(proceso.tme)}`;
      const barra = tarjeta.querySelector(".cpu-progreso");
      barra.setAttribute("aria-valuemax", proceso.tme);
      barra.setAttribute("aria-valuenow", proceso.ejecutado);
      barra.setAttribute("aria-valuetext", `turno ${snapshot.tiempo_turno} de quantum ${snapshot.quantum}; ${proceso.ejecutado} de ${proceso.tme} segundos ejecutados; faltan ${proceso.restante} segundos`);
      const porcentaje = proceso.tme > 0 ? Math.min(100, Math.max(0, proceso.ejecutado / proceso.tme * 100)) : 0;
      barra.firstElementChild.style.width = `${porcentaje}%`;
    } else {
      tarjeta.textContent = `P${proceso.id} · ${formatearOperacion(proceso)} · ${detalle}`;
    }
    if (!tarjetaCpu) contenedor.appendChild(tarjeta);
  });
}

function renderizarDiagrama(snapshot, listas) {
  const idle = snapshot.estado === "completed" ? "Todos los procesos terminaron."
    : snapshot.estado === "paused" ? "CPU libre; simulación pausada."
    : listas.bloqueados.length ? "CPU libre; los bloqueos siguen avanzando." : "Esperando proceso listo.";
  dibujarColumna(elementos.estadoNuevos, listas.nuevos, "new", "Sin procesos nuevos.", snapshot);
  dibujarColumna(elementos.estadoListos, listas.listos, "ready", "Sin procesos listos.", snapshot);
  dibujarColumna(elementos.estadoCpu, listas.cpu, "running", listas.cpu.length ? "" : idle, snapshot);
  dibujarColumna(elementos.estadoBloqueados, listas.bloqueados, "blocked", "Sin procesos bloqueados.", snapshot);
  dibujarColumna(elementos.estadoTerminados, listas.terminados, "finished", "Sin procesos terminados.", snapshot);

  if (elementos.detalleEjecucion) {
    const cpu = snapshot.en_ejecucion;
    elementos.detalleEjecucion.textContent = cpu
      ? `P${cpu.id} · ${formatearOperacion(cpu)} · turno ${mostrarValor(snapshot.tiempo_turno)} / ${mostrarValor(snapshot.quantum)} · servicio ${mostrarValor(cpu.ejecutado)} · restante ${mostrarValor(cpu.restante)}`
      : idle;
  }

}

function todosLosProcesos(listas) {
  return [
    ...listas.nuevos.map(p => ({ ...p, _estadoLista: "new" })),
    ...listas.listos.map(p => ({ ...p, _estadoLista: "ready" })),
    ...listas.cpu.map(p => ({ ...p, _estadoLista: "running" })),
    ...listas.bloqueados.map(p => ({ ...p, _estadoLista: "blocked" })),
    ...listas.terminados.map(p => ({ ...p, _estadoLista: "finished" }))
  ];
}

function renderizarTablaProcesos(listas) {
  if (!elementos.tbodyResumen) return;
  const procesos = todosLosProcesos(listas);
  elementos.tbodyResumen.replaceChildren();
  if (!procesos.length) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 14;
    celda.textContent = "Sin procesos.";
    fila.appendChild(celda);
    elementos.tbodyResumen.appendChild(fila);
    return;
  }
  const campos = ["llegada", "primera_atencion", "finalizacion", "retorno", "respuesta", "espera", "ejecutado", "bloqueo_restante", "bloqueado"];
  procesos.forEach(proceso => {
    const fila = document.createElement("tr");
    const error = proceso.estado === "error";
    const valores = [
      `P${proceso.id}`, textoEstado(proceso, proceso._estadoLista), formatearOperacion(proceso), mostrarValor(proceso.tme),
      error ? "ERROR" : mostrarValor(proceso.resultado, ""), ...campos.map(campo => mostrarValor(proceso[campo]))
    ];
    valores.forEach((valor, indice) => {
      const celda = document.createElement("td");
      celda.textContent = valor;
      if (indice === 1) celda.className = error ? "res-red" : proceso._estadoLista === "finished" ? "res-green" : "";
      fila.appendChild(celda);
    });
    elementos.tbodyResumen.appendChild(fila);
  });
}

function registrarTransiciones(snapshot, listas) {
  const actuales = todosLosProcesos(listas);
  const siguiente = new Map(actuales.map(p => [String(p.id), p._estadoLista]));
  actuales.forEach(proceso => {
    const id = `P${proceso.id}`;
    const antes = estadosAnteriores.get(String(proceso.id));
    const ahora = proceso._estadoLista;
    if (!antes && (ahora === "ready" || ahora === "running")) registrarEvento(`${id} entra a memoria.`);
    else if (antes === "new" && ahora === "ready") registrarEvento(`${id} entra a memoria y pasa a listos.`);
    else if (antes === "ready" && ahora === "running") registrarEvento(`${id} toma la CPU.`);
    else if (antes === "running" && ahora === "ready") registrarEvento(`${id} agota su quantum y vuelve al final de listos.`);
    else if (antes === "running" && ahora === "blocked") registrarEvento(`${id} se bloquea por E/S durante 9 segundos simulados.`);
    else if (antes === "blocked" && ahora === "ready") registrarEvento(`${id} termina E/S y regresa al final de listos.`);
    else if (antes === "blocked" && ahora === "running") registrarEvento(`${id} termina E/S, regresa a listos y toma la CPU.`);
    else if (ahora === "finished" && antes !== "finished") {
      const error = proceso.estado === "error";
      registrarEvento(error ? `${id} termina con ERROR.` : `${id} termina; resultado ${proceso.resultado}.`);
    }
  });
  estadosAnteriores = siguiente;
  if (estadoSimulacionAnterior !== "completed" && snapshot.estado === "completed") registrarEvento("Simulación completada. Se conserva el resumen final.");
  if (estadoSimulacionAnterior !== snapshot.estado && ["paused", "running"].includes(snapshot.estado)) {
    if (snapshot.estado === "paused") registrarEvento("Simulación pausada.");
    else if (estadoSimulacionAnterior === "paused") registrarEvento("Simulación reanudada.");
  }
  estadoSimulacionAnterior = snapshot.estado;
}

function renderizar(snapshot) {
  const listas = procesarListas(snapshot);
  snapshotActual = snapshot;
  const enMemoria = snapshot.memoria_ocupada;
  const cantidadNuevos = listas.nuevos.length;
  if (elementos.reloj) elementos.reloj.textContent = mostrarValor(snapshot.reloj, "");
  if (elementos.memoriaOcupada) elementos.memoriaOcupada.textContent = enMemoria;
  if (elementos.capacidadMemoria) elementos.capacidadMemoria.textContent = 3;
  if (elementos.cantidadNuevos) elementos.cantidadNuevos.textContent = cantidadNuevos;
  if (elementos.totalTrabajos) elementos.totalTrabajos.textContent = snapshot.total_trabajos ?? "—";
  if (elementos.metricTerminados) elementos.metricTerminados.textContent = listas.terminados.length;
  if (elementos.quantumElegido) elementos.quantumElegido.textContent = mostrarValor(snapshot.quantum, "");
  if (elementos.estadoSimulacion) elementos.estadoSimulacion.textContent = snapshot.estado;
  if (elementos.ayudaInterrupcion) {
    elementos.ayudaInterrupcion.textContent = "N: agrega un proceso · E: bloquea por E/S (9 s) · W: termina con ERROR · P/B: pausa y muestra la tabla · C: continúa.";
  }

  registrarTransiciones(snapshot, listas);
  renderizarDiagrama(snapshot, listas);
  renderizarTablaProcesos(listas);

  const isRunning = snapshot.estado === "running";
  const isPaused = snapshot.estado === "paused";
  const isCompleted = snapshot.estado === "completed";
  const panelResumen = document.querySelector("#panelResumen");
  if (panelResumen) panelResumen.hidden = !(isPaused || isCompleted);
  const hayCpu = Boolean(snapshot.en_ejecucion);

  if (elementos.estadoControles) {
    if (isCompleted) elementos.estadoControles.textContent = "Simulación finalizada. El resumen queda disponible.";
    else if (isPaused) elementos.estadoControles.textContent = "Simulación pausada. Tabla completa disponible; pulsa C para continuar.";
    else if (isRunning && !hayCpu && listas.bloqueados.length) elementos.estadoControles.textContent = "CPU libre; el reloj atiende los bloqueos. Pulsa B para pausar y revisar la tabla.";
    else if (isRunning) elementos.estadoControles.textContent = "N agrega un proceso · E bloquea por E/S · W termina con error · P/B pausa y muestra la tabla · C continúa.";
    else elementos.estadoControles.textContent = "Inicia una simulación para habilitar los controles.";
  }
  actualizarControles();
}

// ==========================================
// 4. Polling y Acciones
// ==========================================
function detenerConsultas() {
  if (temporizador !== null) {
    clearTimeout(temporizador);
    temporizador = null;
  }
}

function limpiarSimulacion() {
  detenerConsultas();
  sessionStorage.removeItem("simulacion_id");
  simulacionId = null;
  estadosAnteriores = new Map();
  estadoSimulacionAnterior = null;
  renderizar({
    estado: "sin iniciar", reloj: 0, quantum: null, tiempo_turno: null, total_trabajos: 0,
    nuevos: [], en_espera: [], en_ejecucion: null, bloqueados: [], terminados: [], memoria_ocupada: 0
  });
  snapshotActual = null;
}

function programarConsulta() {
  detenerConsultas();

  if (!simulacionId || snapshotActual?.estado === "completed") {
    return;
  }

  temporizador = setTimeout(() => {
    ejecutarExclusivo(async () => {
      if (!simulacionId) return;
      const datos = await solicitar(`/simulations/${encodeURIComponent(simulacionId)}`);
      renderizar(datos);
    }).catch(error => {
      mostrarMensaje(`No se pudo actualizar: ${mostrarError(error)}`);
    });
  }, 1000);
}

function actualizarControles() {
  // Un ID pendiente de recuperación también impide crear otra simulación.
  const deshabilitado = ocupado || Boolean(simulacionId && snapshotActual?.estado !== "completed");
  elementos.btnIniciar.disabled = deshabilitado;
  elementos.btnIniciarEmulacion.disabled = deshabilitado;
  const running = snapshotActual?.estado === "running";
  const paused = snapshotActual?.estado === "paused";
  elementos.btnInterrupt.disabled = ocupado || !running || !snapshotActual?.en_ejecucion;
  elementos.btnError.disabled = elementos.btnInterrupt.disabled;
  elementos.btnPause.disabled = ocupado || !running;
  elementos.btnContinue.disabled = ocupado || !paused;
  if (elementos.btnAddProcess) elementos.btnAddProcess.disabled = ocupado || !running;
}

function ejecutarExclusivo(trabajo) {
  // Reservar antes del primer await: no acumular clics/teclas sobre un estado viejo.
  if (ocupado) return Promise.resolve();
  ocupado = true;
  detenerConsultas();
  actualizarControles();
  return (async () => {
    try {
      await trabajo();
    } finally {
      ocupado = false;
      actualizarControles();
      programarConsulta();
    }
  })();
}

async function iniciarSimulacion() {
  if (ocupado || (simulacionId && snapshotActual?.estado !== "completed")) return;
  const cantidad = Number(elementos.numeroTrabajos.value);
  const quantum = Number(elementos.quantum.value);

  if (
    elementos.numeroTrabajos.value.trim() === "" ||
    !Number.isSafeInteger(cantidad) ||
    cantidad <= 0
  ) {
    mostrarMensaje("Introduce un número entero positivo de trabajos.");
    return;
  }

  if (
    elementos.quantum.value.trim() === "" ||
    !Number.isSafeInteger(quantum) ||
    quantum <= 0
  ) {
    mostrarMensaje("Introduce un quantum entero positivo.");
    elementos.quantum.focus();
    return;
  }

  await ejecutarExclusivo(async () => {
    detenerConsultas();
    mostrarMensaje("Creando simulación...");

    const datos = await solicitar("/simulations", {
      method: "POST",
      body: JSON.stringify({ numero_trabajos: cantidad, quantum })
    });

    simulacionId = datos.simulacion_id;
    sessionStorage.setItem("simulacion_id", simulacionId);

    snapshotActual = null;
    estadosAnteriores = new Map();
    estadoSimulacionAnterior = null;
    historialLog = [];
    registrarEvento(`Simulación iniciada con ${cantidad} trabajos iniciales y quantum ${quantum}.`);

    renderizar(datos);
    mostrarMensaje("Simulación creada correctamente.");
  });
}

async function ejecutarAccion(accion) {
  if (ocupado) return;
  if (!simulacionId || !snapshotActual) {
    mostrarMensaje("Primero inicia una simulación.");
    return;
  }
  if ((accion === "interrupt" || accion === "error") &&
      (snapshotActual.estado !== "running" || !snapshotActual.en_ejecucion)) {
    mostrarMensaje("Esta acción requiere un proceso en la CPU.");
    return;
  }
  if (accion === "add_process" && snapshotActual.estado !== "running") {
    mostrarMensaje("Solo puedes agregar procesos durante la ejecución.");
    return;
  }
  if (accion === "pause" && snapshotActual.estado !== "running") return;
  if (accion === "continue" && snapshotActual.estado !== "paused") return;

  // Feedback visual en el botón de la acción
  const btn = document.querySelector(`.btn-ctrl[data-action="${accion}"]`);
  if (btn) {
    btn.classList.add("pulsing");
    setTimeout(() => btn.classList.remove("pulsing"), 200);
  }

  const descripcionesAccion = {
    add_process: "Nuevo proceso agregado.",
    interrupt: "Proceso bloqueado por E/S durante 9 segundos simulados.",
    error: `Acción E: proceso terminado por error.`,
    pause: `Acción B: Simulación pausada.`,
    continue: `Acción C: Simulación reanudada.`
  };

  await ejecutarExclusivo(async () => {
    if (!simulacionId || !snapshotActual) return;
    let datos;
    try {
      datos = await solicitar(
        `/simulations/${encodeURIComponent(simulacionId)}/actions`,
        {
          method: "POST",
          body: JSON.stringify({ accion })
        }
      );
    } catch (error) {
      if (error.status === 409 && simulacionId) {
        renderizar(await solicitar(`/simulations/${encodeURIComponent(simulacionId)}`));
      }
      throw error;
    }

    renderizar(datos);
    if (descripcionesAccion[accion]) registrarEvento(descripcionesAccion[accion]);
    mostrarMensaje(descripcionesAccion[accion] || `Acción: ${accion}`);
  });
}

// ==========================================
// 5. Atajos de Teclado y Eventos
// ==========================================
document.addEventListener("keydown", event => {
  if (
    event.ctrlKey ||
    event.altKey ||
    event.metaKey ||
    event.repeat
  ) {
    return;
  }

  // Enter para iniciar simulación si estamos en el campo de trabajos
  if (event.key === "Enter" && [elementos.numeroTrabajos, elementos.quantum].includes(document.activeElement)) {
    event.preventDefault();
    iniciarSimulacion().catch(error => {
      mostrarMensaje(`Error: ${mostrarError(error)}`);
    });
    return;
  }

  // Si se está escribiendo en un input, ignorar teclas de control
  if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName) ||
      document.activeElement?.isContentEditable || event.isComposing) {
    return;
  }

  const tecla = event.key.toLowerCase();

  // Barra Espaciadora: alternar pausa / continuar.
  if (event.code === "Space" || event.key === " ") {
    event.preventDefault();
    if (snapshotActual?.estado === "running") {
      ejecutarAccion("pause").catch(err => mostrarMensaje(`Error al pausar: ${mostrarError(err)}`));
    } else if (snapshotActual?.estado === "paused") {
      ejecutarAccion("continue").catch(err => mostrarMensaje(`Error al continuar: ${mostrarError(err)}`));
    }
    return;
  }

  const acciones = {
    n: "add_process",
    e: "interrupt",
    w: "error",
    p: "pause",
    b: "pause",
    c: "continue"
  };

  if (acciones[tecla]) {
    event.preventDefault();
    ejecutarAccion(acciones[tecla]).catch(error => {
      mostrarMensaje(`Error: ${mostrarError(error)}`);
    });
  }
});

// Click en botones de control
document.querySelectorAll(".btn-ctrl").forEach(btn => {
  btn.addEventListener("click", () => {
    const accion = btn.getAttribute("data-action");
    if (accion) {
      ejecutarAccion(accion).catch(error => {
        mostrarMensaje(`Error: ${mostrarError(error)}`);
      });
    }
  });
});

// Click en botón Generar / Iniciar
[elementos.btnIniciar, elementos.btnIniciarEmulacion].forEach(boton => {
  boton.addEventListener("click", () => {
    iniciarSimulacion().catch(error => {
      mostrarMensaje(`Error: ${mostrarError(error)}`);
    });
  });
});

// ==========================================
// 6. Recuperación e Inicialización
// ==========================================
async function recuperarSimulacion() {
  if (!simulacionId) return;

  try {
    const datos = await solicitar(`/simulations/${encodeURIComponent(simulacionId)}`);
    renderizar(datos);
    registrarEvento("Simulación anterior recuperada.");
    mostrarMensaje("Se recuperó la simulación anterior.");
  } catch (error) {
    mostrarMensaje(`No se pudo recuperar la simulación: ${mostrarError(error)}`);
    // Conservar el ID ante fallos de red; 404 ya limpia el estado en solicitar.
  }
}

async function iniciarFrontend() {
  await comprobarApi();
  if (simulacionId) {
    await recuperarSimulacion();
  } else {
    renderizar({
      estado: "sin iniciar", reloj: 0, quantum: null, tiempo_turno: null, total_trabajos: 0,
      nuevos: [], en_espera: [], en_ejecucion: null, bloqueados: [], terminados: [], memoria_ocupada: 0
    });
  }
}

ejecutarExclusivo(iniciarFrontend).catch(error => {
  mostrarMensaje(`No se pudo iniciar la pantalla: ${mostrarError(error)}`);
});
