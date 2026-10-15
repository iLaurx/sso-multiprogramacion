let escena;
let camara;
let renderizador;
let cubosProcesos = [];
let animacionActiva = false;

function iniciarVisualizacion() {
  const contenedor = document.getElementById("escena");

  if (!contenedor) {
    console.error("No se encontró el contenedor #escena");
    return;
  }

  // Evita crear la escena varias veces
  if (renderizador) return;

  escena = new THREE.Scene();
  escena.background = new THREE.Color(0x111827);

  camara = new THREE.PerspectiveCamera(
    60,
    contenedor.clientWidth / Math.max(contenedor.clientHeight, 1),
    0.1,
    1000
  );

  camara.position.set(0, 5, 12);
  camara.lookAt(0, 0, 0);

  renderizador = new THREE.WebGLRenderer({ antialias: true });
  renderizador.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderizador.setSize(
    contenedor.clientWidth,
    Math.max(contenedor.clientHeight, 300)
  );

  contenedor.replaceChildren(renderizador.domElement);

  escena.add(new THREE.AmbientLight(0xffffff, 2));

  const luz = new THREE.DirectionalLight(0xffffff, 2);
  luz.position.set(5, 10, 7);
  escena.add(luz);

  const piso = new THREE.GridHelper(16, 16, 0x38bdf8, 0x334155);
  escena.add(piso);

  animacionActiva = true;
  dibujarProcesos([]);
  animar();
  

  window.addEventListener("resize", ajustarTamano);
}

function dibujarProcesos(procesos) {
  if (!escena) return;

  cubosProcesos.forEach(cubo => {
    escena.remove(cubo);
    cubo.geometry.dispose();
    cubo.material.dispose();
  });

  cubosProcesos = [];

  procesos.forEach((proceso, indice) => {
    const geometria = new THREE.BoxGeometry(1.2, 1.2, 1.2);

    let color = 0x38bdf8; // Azul: espera

if (
  proceso.estado === "running" ||
  proceso.estado === "ejecutando"
) {
  color = 0x22c55e; // Verde: ejecutándose
}

if (proceso.estado === "error") {
  color = 0xef4444; // Rojo: error
}

if (
  proceso.estado === "finished" ||
  proceso.estado === "terminado"
) {
  color = 0xa78bfa; // Morado: terminado
}

    const material = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.4,
      metalness: 0.15
    });

    const cubo = new THREE.Mesh(geometria, material);

    cubo.position.set((indice - (procesos.length - 1) / 2) * 1.8, 0.8, 0);

    escena.add(cubo);
    cubosProcesos.push(cubo);
  });
}

function animar() {
  if (!animacionActiva) return;

  requestAnimationFrame(animar);

  cubosProcesos.forEach((cubo, indice) => {
    cubo.rotation.y += 0.008;
    cubo.position.y = 0.8 + Math.sin(Date.now() * 0.002 + indice) * 0.12;
  });

  renderizador.render(escena, camara);
}

function ajustarTamano() {
  const contenedor = document.getElementById("escena");
  if (!contenedor || !renderizador || !camara) return;

  camara.aspect =
    contenedor.clientWidth / Math.max(contenedor.clientHeight, 1);
  camara.updateProjectionMatrix();

  renderizador.setSize(
    contenedor.clientWidth,
    Math.max(contenedor.clientHeight, 300)
  );
}

// Permite actualizar los cubos desde app.js
window.dibujarProcesos = dibujarProcesos;

window.addEventListener("DOMContentLoaded", iniciarVisualizacion);
