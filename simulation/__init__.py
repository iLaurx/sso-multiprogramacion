"""Motor de multiprogramación por lotes, independiente del servidor."""

# * Expone las clases públicas para importarlas directamente desde simulation.
from .engine import SimulationEngine, SimulationStateError
from .models import Process

# ? __all__ indica los nombres exportados al usar from simulation import *.
__all__ = ["Process", "SimulationEngine", "SimulationStateError"]
