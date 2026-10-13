from fastapi import APIRouter, HTTPException, Request, status
from simulation import SimulationStateError
from backend.schemas import CrearSimulacion, AccionSimulacion

router = APIRouter(prefix="/api/simulations", tags=["Simulaciones"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_simulacion(datos: CrearSimulacion, request: Request):
    service = request.app.state.service
    return await service.create(numero_trabajos=datos.numero_trabajos, seed=datos.seed)

@router.get("/{simulacion_id}")
async def obtener_simulacion(simulacion_id: str, request: Request):
    service = request.app.state.service
    snapshot = await service.get_snapshot(simulacion_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return snapshot

@router.post("/{simulacion_id}/actions")
async def ejecutar_accion(simulacion_id: str, datos: AccionSimulacion, request: Request):
    service = request.app.state.service
    try:
        return await service.apply_action(simulacion_id, datos.accion)
    except KeyError:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    except SimulationStateError as e:
        raise HTTPException(status_code=409, detail=str(e))