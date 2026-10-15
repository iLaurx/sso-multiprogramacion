
const API = "/api";

const elementos = {
  estadoApi: document.querySelector("#estadoApi"),
  numeroTrabajos: document.querySelector("#numeroTrabajos"),
  btnIniciar: document.querySelector("#btnIniciar"),
  mensaje: document.querySelector("#mensaje"),
  estadoSimulacion: document.querySelector("#estadoSimulacion"),
  reloj: document.querySelector("#reloj"),
  loteActual: document.querySelector("#loteActual"),
  lotesPendientes: document.querySelector("#lotesPendientes"),
  totalTrabajos: document.querySelector("#totalTrabajos"),
  estadoControles: document.querySelector("#estadoControles"),
  procesoActual: document.querySelector("#procesoActual"),
  procesosEspera: document.querySelector("#procesosEspera"),
  procesosTerminados: document.querySelector("#procesosTerminados")
};

let simulacionId = sessionStorage.getItem("simulacion_id");
let snapshotActual = null;
let ocupado = false;
let temporizador = null;

function mostrarMensaje(texto) {
  elementos.mensaje.textContent = texto;
}

function mostrarError(error) {
  const detalle = error?.detail ?? error?.message ?? "Error desconocido";

  if (Array.isArray(detalle)) {
    return detalle.map(item => item.msg ?? JSON.stringify(item)).join("; ");
  }

  return String(detalle);
}

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
    const datos = await solicitar("/health");

    elementos.estadoApi.textContent = `API: ${datos.status}`;
    elementos.estadoApi.style.color = "green";
  } catch (error) {
    elementos.estadoApi.textContent = `API no disponible: ${mostrarError(error)}`;
    elementos.estadoApi.style.color = "crimson";
  }
}

function crearTarjetaProceso(proceso) {
  const tarjeta = document.createElement("div");
  tarjeta.className = "proceso";

  const titulo = document.createElement("strong");
  titulo.textContent = `Proceso ${proceso.id}`;

  const detalles = document.createElement("p");
  detalles.textContent =
    `Lote: ${proceso.lote} | Estado: ${proceso.estado}`;

  const operacion = document.createElement("p");
  operacion.textContent =
    `Operación: ${proceso.operando_a} ${proceso.operacion} ${proceso.operando_b}`;

  const tiempos = document.createElement("p");
  tiempos.textContent =
    `TME: ${proceso.tme} s | Ejecutado: ${proceso.ejecutado} s | Restante: ${proceso.restante} s`;

  tarjeta.append(titulo, detalles, operacion, tiempos);

  if (proceso.estado === "error") {
    const error = document.createElement("p");
    error.textContent = "Resultado: ERROR";
    tarjeta.append(error);
  } else if (proceso.resultado !== null) {
    const resultado = document.createElement("p");
    resultado.textContent = `Resultado: ${proceso.resultado}`;
    tarjeta.append(resultado);
  }

  return tarjeta;
}

function renderizar(snapshot) {
  snapshotActual = snapshot;

  elementos.estadoSimulacion.textContent = snapshot.estado;
  elementos.reloj.textContent = snapshot.reloj;
  elementos.loteActual.textContent = snapshot.lote_actual ?? "—";
  elementos.lotesPendientes.textContent = snapshot.lotes_pendientes;
  elementos.totalTrabajos.textContent = snapshot.total_trabajos;

  elementos.procesoActual.replaceChildren();

  if (snapshot.en_ejecucion) {
    elementos.procesoActual.append(
      crearTarjetaProceso(snapshot.en_ejecucion)
    );
  } else {
    elementos.procesoActual.textContent =
      "No hay procesos en ejecución.";
  }

  elementos.procesosEspera.replaceChildren();

  if (snapshot.en_espera.length === 0) {
    elementos.procesosEspera.textContent =
      "No hay procesos en espera.";
  } else {
    snapshot.en_espera.forEach(proceso => {
      elementos.procesosEspera.append(
        crearTarjetaProceso(proceso)
      );
    });
  }

  elementos.procesosTerminados.replaceChildren();

  if (snapshot.terminados.length === 0) {
    elementos.procesosTerminados.textContent =
      "Todavía no hay procesos terminados.";
  } else {
    snapshot.terminados.forEach(proceso => {
      elementos.procesosTerminados.append(
        crearTarjetaProceso(proceso)
      );
    });
  }

  elementos.estadoControles.textContent =
    snapshot.estado === "completed"
      ? "Simulación terminada. Inicia otra para continuar."
      : snapshot.estado === "paused"
        ? "Simulación pausada. Pulsa C para continuar."
        : "Utiliza I, E, P o C para controlar la simulación.";

 
  elementos.btnIniciar.disabled =
    ocupado || snapshot.estado === "running" ||
    snapshot.estado === "paused";

  // Actualizar la visualización 3D
  const procesos3D = [
    ...(snapshot.en_ejecucion ? [snapshot.en_ejecucion] : []),
    ...(snapshot.en_espera || []),
    ...(snapshot.terminados || [])
  ];

  if (typeof window.dibujarProcesos === "function") {
    window.dibujarProcesos(procesos3D);
  }
}


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

      const datos = await solicitar(
        `/simulations/${encodeURIComponent(simulacionId)}`
      );

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
      body: JSON.stringify({
        numero_trabajos: cantidad
      })
    });

    simulacionId = datos.simulacion_id;
    sessionStorage.setItem("simulacion_id", simulacionId);

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

  await ejecutarExclusivo(async () => {
    const datos = await solicitar(
      `/simulations/${encodeURIComponent(simulacionId)}/actions`,
      {
        method: "POST",
        body: JSON.stringify({ accion })
      }
    );

    renderizar(datos);
    mostrarMensaje(`Acción ejecutada: ${accion}`);
  });

  programarConsulta();
}

document.addEventListener("keydown", event => {
  if (
    event.ctrlKey ||
    event.altKey ||
    event.metaKey ||
    event.repeat ||
    ["INPUT", "TEXTAREA", "SELECT"].includes(
      document.activeElement?.tagName
    )
  ) {
    return;
  }

  const tecla = event.key.toLowerCase();

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

elementos.btnIniciar.addEventListener("click", () => {
  iniciarSimulacion().catch(error => {
    mostrarMensaje(`Error: ${mostrarError(error)}`);
  });
});

async function recuperarSimulacion() {
  if (!simulacionId) return;

  try {
    const datos = await solicitar(
      `/simulations/${encodeURIComponent(simulacionId)}`
    );

    renderizar(datos);
    mostrarMensaje("Se recuperó la simulación anterior.");
    programarConsulta();
  } catch (error) {
    sessionStorage.removeItem("simulacion_id");
    simulacionId = null;

    mostrarMensaje(
      `No se pudo recuperar la simulación: ${mostrarError(error)}`
    );
  }
}

async function iniciarFrontend() {
  await comprobarApi();
  await recuperarSimulacion();
}

iniciarFrontend();
