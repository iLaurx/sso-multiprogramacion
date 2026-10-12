async function comprobarApi() {
  const salida = document.querySelector("#estado");
  try {
    const respuesta = await fetch("/api/health");
    if (!respuesta.ok) throw new Error("API no disponible");
    const datos = await respuesta.json();
    salida.textContent = `API: ${datos.status}`;
  } catch (error) {
    salida.textContent = error.message;
  }
}

comprobarApi();