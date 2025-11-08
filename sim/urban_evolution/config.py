import numpy as np

# Semilla para reproducibilidad
RNG_SEED = 42

# Dimensiones de la ciudad (grilla N x N)
GRID_N = 10

# Pasos de simulación (meses)
STEPS = 120

# Población total de hogares
N_HOUSEHOLDS = 4000

# Distribución de ingresos de hogares (proporciones)
INCOME_SHARES = {"low": 0.45, "mid": 0.40, "high": 0.15}

# Ingresos mensuales característicos por clase
INCOME_LEVELS = {"low": 800, "mid": 1600, "high": 4000}

# Amenidades base por barrio (se derivan con ruido)
AMENITY_BASE = 0.5

# Velocidad base de viaje (minutos por unidad de distancia implícita)
BASE_T_TIME = 10.0

# Parámetros de congestión tipo BPR local
BPR_A = 0.15
BPR_B = 4.0

# Capacidad vial base por barrio
BASE_ROAD_CAP = 300

# Renta inicial promedio y dispersión
INIT_RENT_MEAN = 500.0
INIT_RENT_SD = 80.0

# Ajuste de precio por desbalance oferta-demanda (SD)
PRICE_ADJ_ALPHA = 0.25
TARGET_OCCUPANCY = 0.92  # objetivo de ocupación

# Costos de construcción y obsolescencia
DEV_UNIT_COST = 350.0
DEV_BUILD_RATE = 30  # unidades por decisión
UNIT_DECAY_RATE = 0.002  # fracción mensual

# Zonificación: 0=estricta, 1=mixta, 2=liberal (afecta densidad tope)
ZONING_PROBS = [0.3, 0.5, 0.2]
ZONING_DENSITY_MULT = {0: 1.0, 1: 1.5, 2: 2.2}

# Preferencias hogares (utilidad)
LAMBDA_RENT_BURDEN = 2.0
MU_TRAVEL = 0.05
GAMMA_AMENITIES = 1.2
DELTA_PEERS = 0.5  # atracción/repulsión por pares

# Probabilidad mensual de considerar mudanza si no hay estrés
SPONT_MOVE_PROB = 0.01

# Umbrales de carga de renta (renta/ingreso) que disparan mudanza
RENT_BURDEN_THRESH = {"low": 0.35, "mid": 0.30, "high": 0.25}

# Oferta inicial de unidades por barrio (asequibles/mercado)
INIT_UNITS_PER_NEIGH = (120, 80)

# Proporción inicial de asequibles/mercado para nuevas construcciones
INCL_ZONING_SHARE_AFFORD = 0.3  # se puede modificar por política

# CBD en el centro de la grilla
CBD_POS = (GRID_N // 2, GRID_N // 2)

# Políticas/choques programados: (step, tipo, payload)
POLICY_EVENTS = [
    # Nueva infraestructura: mejora T0 en anillo intermedio
    (24, "transport_invest", {"ring": 3, "t0_factor": 0.85, "capacity_factor": 1.2}),
    # Zonificación inclusiva: reservar % de nuevas unidades como asequibles
    (36, "inclusionary_zoning", {"aff_share": 0.5}),
    # Tope a crecimiento de renta anual (mensual aprox.)
    (60, "rent_cap", {"monthly_cap": 0.01}),
]
