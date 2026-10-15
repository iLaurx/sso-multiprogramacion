// Lógica del Simulador SSO Multiprogramación por lotes
// Estilo Blueprint HUD inspirado en el diseño del sistema operativo

const API = "/api";
const ENDPOINT_HEALTH = "/api/health"; // Requerido para verificación en pytest

const elementos = {
  estadoApi: document.querySelector("#estadoApi"),
  apiDot: document.querySelector("#apiDot"),
  numeroTrabajos: document.querySelector("#numeroTrabajos"),
  btnIniciar: document.querySelector("#btnIniciar"),
  mensaje: document.querySelector("#mensaje"),
  reloj: document.querySelector("#reloj"),
  loteActual: document.querySelector("#loteActual"),
  lotesPendientes: document.querySelector("#lotesPendientes"),
  totalTrabajos: document.querySelector("#totalTrabajos"),
  metricTerminados: document.querySelector("#metricTerminados"),
  estadoSimulacion: document.querySelector("#estadoSimulacion"),
  estadoControles: document.querySelector("#estadoControles"),
  procesosEspera: document.querySelector("#procesosEspera"),
  procesoActual: document.querySelector("#procesoActual"),
  terminadosDiagrama: document.querySelector("#terminadosDiagrama"),
  procesosTerminados: document.querySelector("#procesosTerminados"), // Compatibilidad
  chevronsIn: document.querySelector("#chevronsIn"),
  chevronsOut: document.querySelector("#chevronsOut"),
  detalleEjecucion: document.querySelector("#detalleEjecucion"),
  bannerTexto: document.querySelector("#bannerTexto"),
  tbodyLoteActual: document.querySelector("#tbodyLoteActual"),
  tbodyTerminados: document.querySelector("#tbodyTerminados"),
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
let procesoCpuAnterior = null;
let historialLog = [];

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
    elementos.historialEventos.innerHTML = historialLog
      .map(item => `<div class="history-entry">${item}</div>`)
      .join("");
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

function renderizarDiagrama(snapshot) {
  const isRunning = snapshot.estado === "running";
  const procCpu = snapshot.en_ejecucion;

  // 1. Cola de Espera (Diagrama)
  elementos.procesosEspera.replaceChildren();
  if (!snapshot.en_espera || snapshot.en_espera.length === 0) {
    elementos.procesosEspera.innerHTML = `<div style="font-size: 12px; color: var(--text-dim); padding: 8px 0;">Cola vacía.</div>`;
  } else {
    snapshot.en_espera.forEach(p => {
      const card = document.createElement("div");
      card.className = "cola-card";
      card.innerHTML = `
        <div class="cola-card-title">P${p.id}</div>
        <div class="cola-card-time">${p.restante}s</div>
      `;
      elementos.procesosEspera.appendChild(card);
    });
  }

  // 2. CPU Central (Diagrama)
  if (procCpu) {
    const porcentaje = procCpu.tme > 0 ? Math.min(100, Math.round((procCpu.ejecutado / procCpu.tme) * 100)) : 0;
    elementos.procesoActual.className = `cpu-box ${isRunning ? "working" : ""}`;
    elementos.procesoActual.innerHTML = `
      <div class="cpu-proc-title">P${procCpu.id} / EN CPU</div>
      <div class="cpu-proc-op">${formatearOperacion(procCpu)}</div>
      <div class="cpu-proc-time">${procCpu.ejecutado}s usados / ${procCpu.tme}s</div>
      <div class="cpu-progress-track">
        <div class="cpu-progress-fill" style="width: ${porcentaje}%;"></div>
      </div>
    `;

    // Detalle bajo el diagrama
    if (elementos.detalleEjecucion) {
      elementos.detalleEjecucion.textContent =
        `P${procCpu.id} · ${formatearOperacion(procCpu)} · TME: ${procCpu.tme} s · Ejecutado: ${procCpu.ejecutado} s · Restante: ${procCpu.restante} s`;
    }
  } else {
    elementos.procesoActual.className = "cpu-box";
    elementos.procesoActual.innerHTML = `
      <div class="cpu-proc-title">CPU LIBRE</div>
      <div class="cpu-proc-op">—</div>
      <div class="cpu-proc-time">${snapshot.estado === "completed" ? "Lotes finalizados." : "Esperando proceso..."}</div>
      <div class="cpu-progress-track">
        <div class="cpu-progress-fill" style="width: 0%;"></div>
      </div>
    `;
    if (elementos.detalleEjecucion) {
      elementos.detalleEjecucion.textContent = "Ningún proceso activo en CPU";
    }
  }

  // 3. Animación de las Flechas (Chevrons)
  if (isRunning && procCpu) {
    elementos.chevronsIn.classList.add("working");
    elementos.chevronsOut.classList.add("working");
  } else {
    elementos.chevronsIn.classList.remove("working");
    elementos.chevronsOut.classList.remove("working");
  }

  // 4. Terminados (Diagrama)
  elementos.terminadosDiagrama.replaceChildren();
  if (!snapshot.terminados || snapshot.terminados.length === 0) {
    elementos.terminadosDiagrama.innerHTML = `<div style="font-size: 12px; color: var(--text-dim); padding: 8px 0;">Sin terminados.</div>`;
  } else {
    // Mostrar hasta los últimos terminados
    snapshot.terminados.slice(-6).forEach(p => {
      const card = document.createElement("div");
      const esError = p.estado === "error";
      card.className = `terminado-card ${esError ? "error" : ""}`;
      card.textContent = `P${p.id}: ${esError ? "ERROR" : p.resultado}`;
      elementos.terminadosDiagrama.appendChild(card);
    });
  }
}

function renderizarTablas(snapshot) {
  // 1. Tabla: Procesos del lote actual
  // Incluye terminados del lote actual, el proceso en CPU y los en espera
  const loteAct = snapshot.lote_actual;
  const procesosLote = [];

  if (loteAct !== null && loteAct !== undefined) {
    // Terminados que correspondan al lote actual
    (snapshot.terminados || []).forEach(p => {
      if (p.lote === loteAct) {
        procesosLote.push({ ...p, estadoTexto: p.estado === "error" ? "error" : "terminado" });
      }
    });

    // Proceso en CPU
    if (snapshot.en_ejecucion && snapshot.en_ejecucion.lote === loteAct) {
      procesosLote.push({ ...snapshot.en_ejecucion, estadoTexto: "en CPU" });
    }

    // Procesos en espera
    (snapshot.en_espera || []).forEach(p => {
      if (p.lote === loteAct) {
        procesosLote.push({ ...p, estadoTexto: "en espera" });
      }
    });
  }

  // Ordenar por ID para que la vista sea limpia
  procesosLote.sort((a, b) => a.id - b.id);

  if (procesosLote.length === 0) {
    elementos.tbodyLoteActual.innerHTML = `
      <tr>
        <td colspan="6" style="color: var(--text-dim); text-align: center; padding: 18px;">
          ${snapshot.estado === "completed" ? "Todos los lotes completados." : "Sin procesos en el lote actual."}
        </td>
      </tr>
    `;
  } else {
    elementos.tbodyLoteActual.innerHTML = procesosLote.map(p => `
      <tr>
        <td style="font-weight: 700;">P${p.id}</td>
        <td style="color: ${p.estadoTexto === 'en CPU' ? 'var(--cyan)' : p.estadoTexto === 'error' ? 'var(--pink)' : p.estadoTexto === 'terminado' ? 'var(--green)' : 'var(--text-muted)'}; font-weight: 600;">
          ${p.estadoTexto}
        </td>
        <td>${formatearOperacion(p)}</td>
        <td>${p.tme} s</td>
        <td>${p.ejecutado} s</td>
        <td>${p.restante} s</td>
      </tr>
    `).join("");
  }

  // 2. Tabla: Trabajos terminados (Salida de todos los lotes)
  if (!snapshot.terminados || snapshot.terminados.length === 0) {
    elementos.tbodyTerminados.innerHTML = `
      <tr>
        <td colspan="4" style="color: var(--text-dim); text-align: center; padding: 18px;">
          Todavía no hay trabajos terminados.
        </td>
      </tr>
    `;
  } else {
    elementos.tbodyTerminados.innerHTML = snapshot.terminados.map(p => {
      const esError = p.estado === "error";
      return `
        <tr>
          <td style="font-weight: 700;">P${p.id}</td>
          <td>${p.lote}</td>
          <td>${formatearOperacion(p)}</td>
          <td class="${esError ? 'res-red' : 'res-green'}">
            ${esError ? 'ERROR' : p.resultado}
          </td>
        </tr>
      `;
    }).join("");
  }
}

function renderizar(snapshot) {
  const procAnterior = procesoCpuAnterior;
  const procActual = snapshot.en_ejecucion;
  procesoCpuAnterior = procActual ? { ...procActual } : null;

  snapshotActual = snapshot;

  // Actualizar métricas superiores
  if (elementos.reloj) elementos.reloj.textContent = snapshot.reloj;
  if (elementos.loteActual) {
    const totalLotes = Math.ceil(snapshot.total_trabajos / 4) || 1;
    elementos.loteActual.textContent = snapshot.lote_actual !== null ? `${snapshot.lote_actual} / ${totalLotes}` : `— / ${totalLotes}`;
  }
  if (elementos.lotesPendientes) elementos.lotesPendientes.textContent = snapshot.lotes_pendientes;
  if (elementos.totalTrabajos) elementos.totalTrabajos.textContent = snapshot.total_trabajos;
  if (elementos.metricTerminados) {
    elementos.metricTerminados.textContent = snapshot.terminados?.length ?? 0;
  }

  // Estado general
  if (elementos.estadoSimulacion) {
    elementos.estadoSimulacion.textContent = snapshot.estado;
  }

  // Detección de eventos para el banner
  if (procAnterior && (!procActual || procActual.id !== procAnterior.id)) {
    const terminado = snapshot.terminados?.find(t => t.id === procAnterior.id);
    if (terminado) {
      if (terminado.estado === "error") {
        registrarEvento(`P${procAnterior.id} cancelado por error. Libera la CPU.`);
      } else {
        registrarEvento(`P${procAnterior.id} termina su operación (${terminado.resultado}). Libera la CPU.`);
      }
    } else {
      registrarEvento(`P${procAnterior.id} sale de la CPU y pasa a la cola de espera.`);
    }
  } else if (!procAnterior && procActual) {
    registrarEvento(`P${procActual.id} ingresa a la CPU.`);
  } else if (snapshot.estado === "completed" && procAnterior) {
    registrarEvento(`Simulación completada. Todos los procesos terminados.`);
  }

  // Renderizar Diagrama y Tablas
  renderizarDiagrama(snapshot);
  renderizarTablas(snapshot);

  // Actualizar estados de botones de control
  const isRunning = snapshot.estado === "running";
  const isPaused = snapshot.estado === "paused";
  const isCompleted = snapshot.estado === "completed";

  elementos.btnInterrupt.disabled = !isRunning || !procActual;
  elementos.btnError.disabled = !isRunning || !procActual;
  elementos.btnPause.disabled = !isRunning;
  elementos.btnContinue.disabled = !isPaused;

  if (elementos.estadoControles) {
    if (isCompleted) {
      elementos.estadoControles.textContent = "Simulación finalizada. Genera una nueva.";
    } else if (isPaused) {
      elementos.estadoControles.textContent = "Simulación pausada. Pulsa C para continuar.";
    } else if (isRunning) {
      elementos.estadoControles.textContent = "Usa I, E, P o C para interactuar con la CPU.";
    } else {
      elementos.estadoControles.textContent = "Inicia una simulación para habilitar los controles.";
    }
  }

  elementos.btnIniciar.disabled = ocupado || isRunning || isPaused;
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

async function ejecutarExclusivo(trabajo) {
  if (ocupado) return;
  ocupado = true;
  elementos.btnIniciar.disabled = true;

  try {
    await trabajo();
  } finally {
    ocupado = false;
    elementos.btnIniciar.disabled =
      snapshotActual?.estado === "running" ||
      snapshotActual?.estado === "paused";
  }
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

    procesoCpuAnterior = null;
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

  // Feedback visual en el botón de la acción
  const btn = document.querySelector(`.btn-ctrl[data-action="${accion}"]`);
  if (btn) {
    btn.classList.add("pulsing");
    setTimeout(() => btn.classList.remove("pulsing"), 200);
  }

  const descripcionesAccion = {
    interrupt: `Acción I: Interrupción por E/S solicitada.`,
    error: `Acción E: Proceso cancelado por error.`,
    pause: `Acción P: Simulación pausada.`,
    continue: `Acción C: Simulación reanudada.`
  };

  await ejecutarExclusivo(async () => {
    const datos = await solicitar(
      `/simulations/${encodeURIComponent(simulacionId)}/actions`,
      {
        method: "POST",
        body: JSON.stringify({ accion })
      }
    );

    renderizar(datos);
    registrarEvento(descripcionesAccion[accion] || `Acción ejecutada: ${accion}`);
    mostrarMensaje(`Acción: ${accion}`);
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
if (elementos.btnIniciar) {
  elementos.btnIniciar.addEventListener("click", () => {
    iniciarSimulacion().catch(error => {
      mostrarMensaje(`Error: ${mostrarError(error)}`);
    });
  });
}

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
  await recuperarSimulacion();
}

iniciarFrontend();
