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

# Parámetros de congestión local
BPR_A = 0.15
BPR_B = 4.0

# Capacidad vial base por barrio
BASE_ROAD_CAP = 300

# Renta inicial promedio y dispersión
INIT_RENT_MEAN = 500.0
INIT_RENT_SD = 80.0

# Ajuste de precio por desbalance oferta-demanda (antes de acotar cambios)
PRICE_ADJ_ALPHA = 0.25
TARGET_OCCUPANCY = 0.92  # objetivo de ocupación

# Límites de ajuste de renta para evitar colapso o saltos irreales
MAX_RENT_CHANGE = 0.03  # cambio máximo mensual (3% arriba/abajo)
RENT_FLOOR_FRAC = 0.60  # piso de renta por barrio: 60% de su renta inicial

# Costos de construcción y obsolescencia
DEV_UNIT_COST = 350.0
DEV_BUILD_RATE = 30  # unidades por decisión de cada desarrollador
UNIT_DECAY_RATE = 0.002  # fracción mensual

# Criterios para habilitar nueva construcción (evitar sobreoferta persistente)
BUILD_OCC_THRESHOLD = 0.90  # solo se construye con ocupación alta
BUILD_MIN_PROFIT = 40.0  # margen mínimo (renta - costo) para construir

# Zonificación: 0=estricta, 1=mixta, 2=liberal (afecta densidad tope)
ZONING_PROBS = [0.3, 0.5, 0.2]
ZONING_DENSITY_MULT = {0: 1.0, 1: 1.5, 2: 2.2}

# Preferencias hogares (utilidad)
LAMBDA_RENT_BURDEN = 2.0
MU_TRAVEL = 0.05
GAMMA_AMENITIES = 1.2
DELTA_PEERS = 0.5

# Probabilidad mensual de considerar mudanza si no hay estrés
SPONT_MOVE_PROB = 0.01

# Umbrales de carga de renta (renta/ingreso) que disparan mudanza
RENT_BURDEN_THRESH = {"low": 0.35, "mid": 0.30, "high": 0.25}

# Oferta inicial de unidades por barrio (asequibles/mercado)
# Nota: bajamos el stock inicial para evitar arrancar con sobreoferta extrema.
INIT_UNITS_PER_NEIGH = (30, 10)

# Proporción inicial de asequibles/mercado en nuevas construcciones
INCL_ZONING_SHARE_AFFORD = 0.3  # modificable por política

# CBD en el centro de la grilla
CBD_POS = (GRID_N // 2, GRID_N // 2)

# Movilidad entre clases de ingreso (pequeña, para evitar series planas)
MOBILITY_LOW_TO_MID = 0.002
MOBILITY_MID_TO_HIGH = 0.0015
MOBILITY_MID_TO_LOW = 0.0010
MOBILITY_HIGH_TO_MID = 0.0015

# Carpeta de salidas y snapshots espaciales
OUTPUTS_DIR = "outputs"
HOLD_PLOTS_OPEN = True  # mantener ventanas abiertas al final

# Políticas/choques programados: (step, tipo, payload)
POLICY_EVENTS = [
    (
        12,
        "upzoning_cluster",
        {"center": (GRID_N // 2, GRID_N // 2), "radius": 2, "new_zoning": 2},
    ),
    (24, "transport_invest", {"ring": 3, "t0_factor": 0.85, "capacity_factor": 1.2}),
    (30, "voucher_program", {"discount_low": 0.20}),  # vales para low-income
    (36, "inclusionary_zoning", {"aff_share": 0.5}),
    (48, "growth_boundary", {"ring_min": 5}),  # restringe expansión
    (54, "amenity_investment", {"positions": [(4, 6), (5, 6), (6, 6)], "delta": 0.2}),
    (60, "rent_cap", {"monthly_cap": 0.01}),
    (72, "tod", {"ring": 2, "amen_boost": 0.15, "t0_factor": 0.9, "upzone_to": 2}),
    (84, "vacancy_tax", {"penalty": 120.0}),  # penaliza construir con vacancia
]
