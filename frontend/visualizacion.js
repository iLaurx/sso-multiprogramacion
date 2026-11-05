let escena;
let camara;
let renderizador;
let objetosProcesos = [];
let animacionActiva = false;
let listasActuales = {};
let observadorTamano;

const columnasEstado = [
  { nombre: "nuevos", x: -4, color: 0x94a3b8 },
  { nombre: "listos", x: -2, color: 0x38bdf8 },
  { nombre: "cpu", x: 0, color: 0x22c55e },
  { nombre: "bloqueados", x: 2, color: 0xfbbf24 },
  { nombre: "terminados", x: 4, color: 0xa78bfa }
];

function iniciarVisualizacion() {
  const contenedor = document.querySelector("#escena");
  if (!contenedor) return;
  if (!window.THREE) {
    contenedor.textContent = "No se pudo cargar Three.js. La vista de estados sigue disponible arriba.";
    return;
  }

  escena = new THREE.Scene();
  escena.background = new THREE.Color(0x080c16);
  camara = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
  camara.position.set(0, 6.5, 12);
  camara.lookAt(0, 0.6, 0);

  renderizador = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderizador.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  contenedor.replaceChildren(renderizador.domElement);

  escena.add(new THREE.AmbientLight(0xffffff, 1.8));
  const luz = new THREE.DirectionalLight(0xffffff, 1.4);
  luz.position.set(5, 8, 7);
  escena.add(luz);
  escena.add(new THREE.GridHelper(12, 24, 0x164e63, 0x1e293b));

  ajustarTamano();
  animacionActiva = true;
  dibujarProcesos(listasActuales);
  animar();
  window.addEventListener("resize", ajustarTamano);
  if ("ResizeObserver" in window) {
    observadorTamano = new ResizeObserver(ajustarTamano);
    observadorTamano.observe(contenedor);
  }
}

function dibujarProcesos(listas = {}) {
  listasActuales = listas;
  if (!escena || !window.THREE) return;
  objetosProcesos.forEach(objeto => {
    escena.remove(objeto);
    objeto.geometry.dispose();
    objeto.material.dispose();
  });
  objetosProcesos = [];

  columnasEstado.forEach((columna, columnaIndex) => {
    const procesos = (listas[columna.nombre] || []).slice(0, 8);
    procesos.forEach((proceso, indice) => {
      const esError = columna.nombre === "terminados" &&
        proceso.estado === "error";
      const geometria = new THREE.BoxGeometry(0.78, 0.78, 0.78);
      const material = new THREE.MeshStandardMaterial({
        color: esError ? 0xef4444 : columna.color,
        roughness: 0.38,
        metalness: 0.12
      });
      const cubo = new THREE.Mesh(geometria, material);
      const baseY = 0.48 + Math.floor(indice / 4) * 1.05;
      cubo.position.set(columna.x, baseY, (indice % 4 - 1.5) * 1.2);
      cubo.userData.baseY = baseY;
      cubo.userData.indice = indice + columnaIndex;
      escena.add(cubo);
      objetosProcesos.push(cubo);
    });
  });
}

function animar() {
  if (!animacionActiva || !renderizador) return;
  requestAnimationFrame(animar);
  objetosProcesos.forEach((cubo, indice) => {
    cubo.rotation.y += 0.006;
    cubo.position.y = cubo.userData.baseY + Math.sin(Date.now() * 0.0015 + indice) * 0.08;
  });
  renderizador.render(escena, camara);
}

function ajustarTamano() {
  const contenedor = document.querySelector("#escena");
  if (!contenedor || !renderizador || !camara) return;
  const ancho = Math.max(contenedor.clientWidth, 1);
  const alto = Math.max(contenedor.clientHeight, 240);
  camara.aspect = ancho / alto;
  camara.updateProjectionMatrix();
  renderizador.setSize(ancho, alto, false);
}

window.dibujarProcesos = dibujarProcesos;
window.addEventListener("DOMContentLoaded", iniciarVisualizacion, { once: true });
