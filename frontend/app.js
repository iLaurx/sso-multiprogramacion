// Interfaz de simulación FCFS; el servidor conserva la autoridad de estados y tiempos.

const API = "/api";
const ENDPOINT_HEALTH = "/api/health"; // Requerido para verificación en pytest

const elementos = {
  estadoApi: document.querySelector("#estadoApi"),
  apiDot: document.querySelector("#apiDot"),
  numeroTrabajos: document.querySelector("#numeroTrabajos"),
  btnIniciar: document.querySelector("#btnIniciar"),
  btnIniciarEmulacion: document.querySelector("#btnIniciarEmulacion"),
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
let colaPeticiones = Promise.resolve();
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
    throw datos;
  }
  return datos;
}

async function comprobarApi() {
  try {
    const respuesta = await fetch(ENDPOINT_HEALTH);
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
  const listos = Array.isArray(snapshot.listos) ? snapshot.listos : (snapshot.en_espera || []);
  const cpu = snapshot.en_ejecucion ? [snapshot.en_ejecucion] : [];
  const bloqueados = Array.isArray(snapshot.bloqueados) ? snapshot.bloqueados : [];
  const terminados = Array.isArray(snapshot.terminados) ? snapshot.terminados : [];
  return { nuevos, listos, cpu, bloqueados, terminados };
}

function usaContratoFcfs(snapshot) {
  return Array.isArray(snapshot.nuevos) && Array.isArray(snapshot.listos) && Array.isArray(snapshot.bloqueados);
}

function mostrarValor(valor, unidad = "s") {
  return valor === null || valor === undefined ? "—" : `${valor}${unidad}`;
}

function textoEstado(proceso, estadoLista) {
  if (estadoLista === "finished" && (proceso.causa_terminacion === "error" || proceso.estado === "error")) return "Terminado · ERROR";
  return ({ new: "Nuevo", ready: "Listo", running: "En CPU", blocked: "Bloqueado", finished: "Terminado", error: "Terminado · ERROR" })[estadoLista] || estadoLista;
}

function dibujarColumna(contenedor, procesos, estado, vacio) {
  if (!contenedor) return;
  contenedor.replaceChildren();
  if (!procesos.length) {
    const mensaje = document.createElement("div");
    mensaje.className = "state-empty";
    mensaje.textContent = vacio;
    contenedor.appendChild(mensaje);
    return;
  }
  procesos.forEach(proceso => {
    const tarjeta = document.createElement("article");
    const esError = proceso.causa_terminacion === "error" || proceso.estado === "error";
    tarjeta.className = `state-process ${estado === "blocked" ? "blocked" : ""} ${estado === "finished" ? "finished" : ""} ${esError ? "error" : ""}`.trim();
    const restanteBloqueo = proceso.bloqueo_restante ?? (proceso.bloqueado_transcurrido == null
      ? null
      : Math.max(0, 10 - proceso.bloqueado_transcurrido));
    const detalle = estado === "blocked"
      ? `Bloqueado ${mostrarValor(proceso.bloqueado_transcurrido)} · faltan ${mostrarValor(restanteBloqueo)}`
      : estado === "finished"
        ? (esError ? "ERROR" : `Resultado: ${mostrarValor(proceso.resultado, "")}`)
        : estado === "running"
          ? `TME ${mostrarValor(proceso.tme)} · servicio ${mostrarValor(proceso.servicio ?? proceso.ejecutado)} · restante ${mostrarValor(proceso.restante)}`
          : `TME ${mostrarValor(proceso.tme)} · restante ${mostrarValor(proceso.restante)}`;
    tarjeta.textContent = `P${proceso.id} · ${formatearOperacion(proceso)} · ${detalle}`;
    contenedor.appendChild(tarjeta);
  });
}

function renderizarDiagrama(snapshot, listas) {
  const idle = snapshot.estado === "completed" ? "Todos los procesos terminaron." : listas.bloqueados.length ? "CPU libre; los bloqueos siguen avanzando." : "Esperando proceso listo.";
  dibujarColumna(elementos.estadoNuevos, listas.nuevos, "new", "Sin procesos nuevos.");
  dibujarColumna(elementos.estadoListos, listas.listos, "ready", "Sin procesos listos.");
  dibujarColumna(elementos.estadoCpu, listas.cpu, "running", listas.cpu.length ? "" : idle);
  dibujarColumna(elementos.estadoBloqueados, listas.bloqueados, "blocked", "Sin procesos bloqueados.");
  dibujarColumna(elementos.estadoTerminados, listas.terminados.slice(-8), "finished", "Sin procesos terminados.");

  if (elementos.detalleEjecucion) {
    const cpu = snapshot.en_ejecucion;
    elementos.detalleEjecucion.textContent = cpu
      ? `P${cpu.id} · ${formatearOperacion(cpu)} · TME ${mostrarValor(cpu.tme)} · servicio ${mostrarValor(cpu.servicio ?? cpu.ejecutado)} · restante ${mostrarValor(cpu.restante)}`
      : idle;
  }

  if (typeof window.dibujarProcesos === "function") {
    window.dibujarProcesos(listas);
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
  const procesos = todosLosProcesos(listas).sort((a, b) => Number(a.id) - Number(b.id));
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
  const campos = ["llegada", "primera_atencion", "finalizacion", "retorno", "respuesta", "espera", "servicio", "bloqueado_transcurrido", "bloqueo_acumulado"];
  procesos.forEach(proceso => {
    const fila = document.createElement("tr");
    const error = proceso.causa_terminacion === "error" || proceso.estado === "error";
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
    else if (antes === "running" && ahora === "blocked") registrarEvento(`${id} se bloquea por E/S durante 10 segundos simulados.`);
    else if (antes === "blocked" && ahora === "ready") registrarEvento(`${id} termina E/S y regresa al final de listos.`);
    else if (antes === "blocked" && ahora === "running") registrarEvento(`${id} termina E/S, regresa a listos y toma la CPU.`);
    else if (ahora === "finished" && antes !== "finished") {
      const error = proceso.causa_terminacion === "error" || proceso.estado === "error";
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
  const contratoFcfs = usaContratoFcfs(snapshot);
  snapshotActual = snapshot;
  const enMemoria = snapshot.memoria_ocupada ?? (listas.listos.length + listas.cpu.length + listas.bloqueados.length);
  const cantidadNuevos = contratoFcfs ? listas.nuevos.length : "—";
  if (elementos.reloj) elementos.reloj.textContent = mostrarValor(snapshot.reloj, "").replace("—", "0");
  if (elementos.memoriaOcupada) elementos.memoriaOcupada.textContent = enMemoria;
  if (elementos.capacidadMemoria) elementos.capacidadMemoria.textContent = snapshot.capacidad_memoria ?? 3;
  if (elementos.cantidadNuevos) elementos.cantidadNuevos.textContent = cantidadNuevos;
  if (elementos.totalTrabajos) elementos.totalTrabajos.textContent = snapshot.total_trabajos ?? "—";
  if (elementos.metricTerminados) elementos.metricTerminados.textContent = listas.terminados.length;
  if (elementos.estadoSimulacion) elementos.estadoSimulacion.textContent = snapshot.estado;
  if (elementos.ayudaInterrupcion) {
    elementos.ayudaInterrupcion.textContent = contratoFcfs
      ? "I: bloquea el proceso actual durante 10 segundos simulados por E/S. E: termina el proceso con ERROR."
      : "La API todavía envía el formato por lotes: I usa el comportamiento actual del servidor. El bloqueo FCFS requiere actualizar la API. E termina el proceso con ERROR.";
  }

  registrarTransiciones(snapshot, listas);
  renderizarDiagrama(snapshot, listas);
  renderizarTablaProcesos(listas);

  const isRunning = snapshot.estado === "running";
  const isPaused = snapshot.estado === "paused";
  const isCompleted = snapshot.estado === "completed";
  const hayCpu = Boolean(snapshot.en_ejecucion);
  elementos.btnInterrupt.disabled = !isRunning || !hayCpu;
  elementos.btnError.disabled = !isRunning || !hayCpu;
  elementos.btnPause.disabled = !isRunning;
  elementos.btnContinue.disabled = !isPaused;

  if (elementos.estadoControles) {
    if (isCompleted) elementos.estadoControles.textContent = "Simulación finalizada. El resumen queda disponible.";
    else if (isPaused) elementos.estadoControles.textContent = "Simulación pausada. Pulsa C para reanudar.";
    else if (isRunning && !hayCpu && listas.bloqueados.length) elementos.estadoControles.textContent = "CPU libre; el reloj atiende los bloqueos. P también pausa esta espera.";
    else if (isRunning && !contratoFcfs) elementos.estadoControles.textContent = "API en formato anterior; los estados FCFS aparecerán al actualizar el servidor.";
    else if (isRunning) elementos.estadoControles.textContent = "Usa I para bloqueo por E/S, E para error, P para pausar y C para continuar.";
    else elementos.estadoControles.textContent = "Inicia una simulación para habilitar los controles.";
  }
  actualizarBotonesInicio();
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
    estado: "sin iniciar", reloj: 0, total_trabajos: 0,
    nuevos: [], listos: [], en_ejecucion: null, bloqueados: [], terminados: []
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
    }).finally(() => {
      programarConsulta();
    });
  }, 1000);
}

function actualizarBotonesInicio() {
  const deshabilitado = ocupado || snapshotActual?.estado === "running" || snapshotActual?.estado === "paused";
  elementos.btnIniciar.disabled = deshabilitado;
  elementos.btnIniciarEmulacion.disabled = deshabilitado;
}

function ejecutarExclusivo(trabajo) {
  const tarea = colaPeticiones.then(async () => {
    ocupado = true;
    actualizarBotonesInicio();

    try {
      await trabajo();
    } finally {
      ocupado = false;
      actualizarBotonesInicio();
    }
  });
  colaPeticiones = tarea.catch(() => {});
  return tarea;
}

async function iniciarSimulacion() {
  const cantidad = Number(elementos.numeroTrabajos.value);

  if (
    elementos.numeroTrabajos.value.trim() === "" ||
    !Number.isSafeInteger(cantidad) ||
    cantidad <= 0
  ) {
    mostrarMensaje("Introduce un número entero positivo de trabajos.");
    return;
  }

  await ejecutarExclusivo(async () => {
    detenerConsultas();
    mostrarMensaje("Creando simulación...");

    const datos = await solicitar("/simulations", {
      method: "POST",
      body: JSON.stringify({ numero_trabajos: cantidad })
    });

    simulacionId = datos.simulacion_id;
    sessionStorage.setItem("simulacion_id", simulacionId);

    snapshotActual = null;
    estadosAnteriores = new Map();
    estadoSimulacionAnterior = null;
    historialLog = [];
    registrarEvento(`Simulación iniciada con ${cantidad} trabajos iniciales.`);

    renderizar(datos);
    mostrarMensaje("Simulación creada correctamente.");
  });

  programarConsulta();
}

async function ejecutarAccion(accion) {
  if (!simulacionId || !snapshotActual) {
    mostrarMensaje("Primero inicia una simulación.");
    return;
  }
  if ((accion === "interrupt" || accion === "error") &&
      (snapshotActual.estado !== "running" || !snapshotActual.en_ejecucion)) {
    mostrarMensaje("Esta acción requiere un proceso en la CPU.");
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
    error: `Acción E: proceso terminado por error.`,
    pause: `Acción P: Simulación pausada.`,
    continue: `Acción C: Simulación reanudada.`
  };

  await ejecutarExclusivo(async () => {
    if (!simulacionId || !snapshotActual) return;
    const datos = await solicitar(
      `/simulations/${encodeURIComponent(simulacionId)}/actions`,
      {
        method: "POST",
        body: JSON.stringify({ accion })
      }
    );

    renderizar(datos);
    if (descripcionesAccion[accion]) registrarEvento(descripcionesAccion[accion]);
    mostrarMensaje(descripcionesAccion[accion] || `Acción: ${accion}`);
  });

  programarConsulta();
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
  if (event.key === "Enter" && document.activeElement === elementos.numeroTrabajos) {
    event.preventDefault();
    iniciarSimulacion().catch(error => {
      mostrarMensaje(`Error: ${mostrarError(error)}`);
    });
    return;
  }

  // Si se está escribiendo en un input, ignorar teclas de control
  if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
    return;
  }

  const tecla = event.key.toLowerCase();

  // Barra Espaciadora: Alternar Pausa / Continuar
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
    i: "interrupt",
    e: "error",
    p: "pause",
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
    programarConsulta();
  } catch (error) {
    sessionStorage.removeItem("simulacion_id");
    simulacionId = null;
    mostrarMensaje(`No se pudo recuperar la simulación: ${mostrarError(error)}`);
  }
}

async function iniciarFrontend() {
  await comprobarApi();
  if (simulacionId) {
    await recuperarSimulacion();
  } else {
    renderizar({
      estado: "sin iniciar", reloj: 0, total_trabajos: 0,
      nuevos: [], listos: [], en_ejecucion: null, bloqueados: [], terminados: []
    });
  }
}

iniciarFrontend();
