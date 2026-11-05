"""Recorrido con Chromium/Chrome y servidor real, sin ticks artificiales.

Uso: python tests/browser_fcfs.py http://127.0.0.1:8766
Requiere playwright y Chrome local (o Chromium instalado por Playwright).
No forma parte de pytest: verifica el reloj real y tarda aproximadamente un minuto.
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


def verificar_peticiones(browser, url):
    """Latencia y fallos de transporte sobre la API real; sin sustituir el motor."""
    context = browser.new_context()
    page = context.new_page()
    peticiones = []
    activas = set()
    simultaneas = []

    def registrar(request):
        if "/api/" in request.url:
            peticiones.append((request.method, request.url))
            activas.add(request)
            simultaneas.append(len(activas))

    page.on("request", registrar)
    page.on("requestfinished", lambda request: activas.discard(request))
    page.on("requestfailed", lambda request: activas.discard(request))

    def demorar(route):
        response = route.fetch()
        time.sleep(0.35)
        route.fulfill(response=response)

    page.route("**/api/**", demorar)
    page.goto(url)
    expect(page.locator("#btnIniciar")).to_be_enabled()
    # Dos llamadas en el mismo turno antes de que llegue la primera respuesta.
    page.evaluate("Promise.all([iniciarSimulacion(), iniciarSimulacion()])")
    assert sum(method == "POST" and path.endswith("/simulations") for method, path in peticiones) == 1
    page.evaluate("Promise.all([ejecutarAccion('pause'), ejecutarAccion('pause')])")
    expect(page.locator("#estadoSimulacion")).to_have_text("paused")
    assert sum(method == "POST" and path.endswith("/actions") for method, path in peticiones) == 1
    # Enter no crea otra simulación; los atajos no actúan durante edición.
    page.locator("#numeroTrabajos").focus()
    page.keyboard.press("Enter")
    page.keyboard.press("c")
    page.locator("#numeroTrabajos").blur()
    page.evaluate("""() => {
        const editor = document.createElement('div');
        editor.contentEditable = 'true'; editor.id = 'editorPrueba';
        document.body.append(editor); editor.focus();
    }""")
    page.keyboard.press("c")
    page.locator("#editorPrueba").blur()
    assert sum(method == "POST" for method, _ in peticiones) == 2
    # Un fallo HTTP de acción no detiene las consultas ni reintenta el POST.
    page.route("**/actions", lambda route: route.fulfill(
        status=422, json={"detail": [{"msg": "Acción inválida de prueba"}]}))
    page.locator("#btnContinue").click()
    expect(page.locator("#mensaje")).to_contain_text("Acción inválida de prueba")
    antes = sum(method == "GET" and "/simulations/" in path for method, path in peticiones)
    page.wait_for_timeout(2700)
    despues = sum(method == "GET" and "/simulations/" in path for method, path in peticiones)
    assert 1 <= despues - antes <= 2, (antes, despues)
    assert sum(method == "POST" for method, _ in peticiones) == 3
    page.unroute("**/actions")
    # La recuperación lenta reserva la pantalla y nunca se cruza con crear.
    page.reload(wait_until="domcontentloaded")
    page.evaluate("iniciarSimulacion()")
    expect(page.locator("#estadoSimulacion")).to_have_text("paused")
    assert sum(method == "POST" and path.endswith("/simulations") for method, path in peticiones) == 1
    assert max(simultaneas) == 1, simultaneas
    context.close()


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8766"
    output = Path("tmp/fcfs-browser")
    output.mkdir(parents=True, exist_ok=True)
    chrome = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=str(chrome) if chrome.exists() else None,
            headless=True,
        )
        verificar_peticiones(browser, url)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        expect(page.locator("#estadoApi")).to_have_text("API: ok")
        page.locator("#numeroTrabajos").fill("4")
        page.locator("#btnIniciar").click()
        expect(page.locator("#cantidadNuevos")).to_have_text("1")
        expect(page.locator("#memoriaOcupada")).to_have_text("3")
        expect(page.locator("#estadoListos article")).to_have_count(2)
        # null de un nuevo y cero de llegada/primera atención se distinguen.
        cells = page.locator("#tbodyResumen tr").all_text_contents()
        assert "—" in cells[0] and "0s" in cells[3]
        page.locator("#numeroTrabajos").blur()
        for count in range(1, 4):
            page.keyboard.press("i")
            expect(page.locator("#estadoBloqueados article")).to_have_count(count)
        expect(page.locator("#btnInterrupt")).to_be_disabled()
        expect(page.locator("#btnError")).to_be_disabled()
        expect(page.locator("#btnPause")).to_be_enabled()
        expect(page.locator("#estadoCpu")).to_contain_text("CPU libre")
        page.keyboard.press("p")
        expect(page.locator("#estadoSimulacion")).to_have_text("paused")
        paused = page.locator("#reloj").inner_text()
        blocked = page.locator("#estadoBloqueados").inner_text()
        page.wait_for_timeout(2200)
        assert page.locator("#reloj").inner_text() == paused
        assert page.locator("#estadoBloqueados").inner_text() == blocked
        page.screenshot(path=str(output / "pausa-cpu-libre.png"), full_page=True)
        sim_id = page.evaluate("sessionStorage.getItem('simulacion_id')")
        page.reload()
        expect(page.locator("#estadoSimulacion")).to_have_text("paused")
        assert page.evaluate("sessionStorage.getItem('simulacion_id')") == sim_id
        page.keyboard.press("c")
        expect(page.locator("#estadoSimulacion")).to_have_text("running")
        # El polling continúa con CPU libre; a los 10 ticks vuelve a CPU.
        expect(page.locator("#estadoCpu article")).to_have_count(1, timeout=15000)
        snapshot = page.request.get(f"{url}/api/simulations/{sim_id}").json()
        assert snapshot["reloj"] >= 10
        assert snapshot["en_ejecucion"]["bloqueado"] == 10
        # Un segundo bloqueo deja terminar P2 antes que P1: detectar un sort por ID.
        page.keyboard.press("i")
        expect(page.locator("#estadoCpu article")).to_contain_text("P2")
        page.wait_for_function("snapshotActual.en_ejecucion.ejecutado > 0")
        # Terminar por error conserva el servicio real y admite al nuevo.
        page.keyboard.press("e")
        expect(page.locator("#estadoTerminados")).to_contain_text("ERROR")
        expect(page.locator("#cantidadNuevos")).to_have_text("0")
        # Provocar un 409 real: otro cliente pausa antes de I en la pantalla.
        response = page.request.post(f"{url}/api/simulations/{sim_id}/actions", data={"accion": "pause"})
        assert response.ok
        page.evaluate("ejecutarAccion('interrupt').catch(e => mostrarMensaje(mostrarError(e)))")
        expect(page.locator("#estadoSimulacion")).to_have_text("paused")
        page.keyboard.press("c")
        expect(page.locator("#estadoSimulacion")).to_have_text("running")
        # P1 vuelve al final de listos mientras otro proceso conserva la CPU.
        expect(page.locator("#estadoListos")).to_contain_text("P1", timeout=15000)
        # Dejar terminar normalmente: el reloj y todos los tiempos son reales.
        expect(page.locator("#estadoSimulacion")).to_have_text("completed", timeout=65000)
        expect(page.locator("#btnIniciar")).to_be_enabled()
        snapshot = page.request.get(f"{url}/api/simulations/{sim_id}").json()
        failed = next(process for process in snapshot["terminados"] if process["estado"] == "error")
        assert 0 < failed["ejecutado"] < failed["tme"]
        expected_rows = []
        fields = ["llegada", "primera_atencion", "finalizacion", "retorno", "respuesta", "espera", "ejecutado", "bloqueo_transcurrido", "bloqueado"]
        for process in snapshot["terminados"]:
            number = process["resultado"]
            result = "ERROR" if process["estado"] == "error" else str(int(number) if number == int(number) else number)
            expected_rows.append([
                f"P{process['id']}", "Terminado · ERROR" if process["estado"] == "error" else "Terminado",
                f"{process['operando_a']} {process['operacion']} {process['operando_b']}", f"{process['tme']}s", result,
                *["—" if process.get(field) is None else f"{process[field]}s" for field in fields],
            ])
        actual_rows = page.locator("#tbodyResumen tr").evaluate_all("rows => rows.map(row => [...row.cells].map(cell => cell.textContent))")
        assert actual_rows == expected_rows, (actual_rows, expected_rows)
        expect(page.locator("#memoriaOcupada")).to_have_text("0")
        for button in ["Interrupt", "Error", "Pause", "Continue"]:
            expect(page.locator(f"#btn{button}")).to_be_disabled()
        page.reload()
        expect(page.locator("#estadoSimulacion")).to_have_text("completed")
        expect(page.locator("#btnIniciar")).to_be_enabled()
        assert page.locator("#tbodyResumen tr").count() == 4
        page.screenshot(path=str(output / "final.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(200)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(output / "movil.png"), full_page=True)
        # Recuperación ante pérdida de red: conservar el ID y reintentar.
        page.route("**/api/simulations/*", lambda route: route.abort())
        page.reload()
        expect(page.locator("#mensaje")).to_contain_text("No se pudo recuperar")
        assert page.evaluate("sessionStorage.getItem('simulacion_id')") == sim_id
        page.unroute("**/api/simulations/*")
        expect(page.locator("#estadoSimulacion")).to_have_text("completed", timeout=5000)
        # Un ID perdido por reinicio del servidor vuelve a permitir creación.
        page.evaluate("sessionStorage.setItem('simulacion_id', 'no-existe')")
        page.reload()
        expect(page.locator("#mensaje")).to_contain_text("ya no existe")
        expect(page.locator("#btnIniciar")).to_be_enabled()
        assert page.evaluate("sessionStorage.getItem('simulacion_id')") is None
        assert not errors, errors
        (output / "resultado.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        print("OK: creación, nuevos, memoria, I/E/P/C, CPU libre, bloqueo 10s, pausa, 409/422, final normal/error, tiempos/orden/null, recarga, red y 404; sin errores JS. Sin POST duplicados ni consultas simultáneas; atajos ignorados al editar.")
        browser.close()


if __name__ == "__main__":
    main()
