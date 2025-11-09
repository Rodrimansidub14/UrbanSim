import numpy as np
import pandas as pd
from dataclasses import dataclass
from .config import *
from .agents import Household, Developer
from . import policies as policies_mod
from .utils import manhattan_dist


@dataclass
class Neighborhood:
    # Barrio con oferta de vivienda, renta, amenidades y transporte
    idx: int
    pos: tuple
    amen: float
    zoning: int
    base_capacity: int
    t0: float
    road_capacity: float
    rent: float
    rent_init: float  # guarda la renta inicial para definir pisos por barrio
    # Estado dinámico
    units_aff: int
    units_mkt: int
    pop_low: int = 0
    pop_mid: int = 0
    pop_high: int = 0
    growth_allowed: bool = True  # controlado por políticas

    def add_units(self, n_aff, n_mkt):
        self.units_aff += n_aff
        self.units_mkt += n_mkt

    @property
    def total_units(self):
        return self.units_aff + self.units_mkt

    @property
    def occupancy(self):
        pop = self.pop_low + self.pop_mid + self.pop_high
        return min(1.0, pop / max(self.total_units, 1e-6))

    @property
    def gentr_index(self):
        pop = self.pop_low + self.pop_mid + self.pop_high
        if pop <= 0:
            return 0.0
        return self.pop_high / pop

    @property
    def zoning_cap_mult(self):
        return ZONING_DENSITY_MULT[self.zoning]


class CityModel:
    # Modelo híbrido con programación por ticks
    def __init__(self, rng=None):
        self.rng = np.random.default_rng(RNG_SEED if rng is None else rng.integers(1e9))
        self.N = GRID_N
        self.step = 0
        self.neighborhoods = []
        self.index_to_node = {}
        self.households = []
        self.developers = [
            Developer(did=i, unit_cost=DEV_UNIT_COST, build_rate=DEV_BUILD_RATE)
            for i in range(8)
        ]
        self.current_affordable_share = INCL_ZONING_SHARE_AFFORD
        self.rent_cap_monthly = None
        self.voucher_discount = 0.0
        self.vacancy_penalty = 0.0

        self._init_city()
        self._init_households()

        # registros
        self.records = []

    def _init_city(self):
        idx = 0
        for i in range(self.N):
            for j in range(self.N):
                pos = (i, j)
                ring = manhattan_dist(pos, CBD_POS)
                amen = max(
                    0.0,
                    np.random.normal(AMENITY_BASE + 0.05 * (self.N / 2 - ring), 0.1),
                )
                zoning = self.rng.choice([0, 1, 2], p=ZONING_PROBS)
                base_cap = int(np.random.normal(BASE_ROAD_CAP, 30))
                t0 = BASE_T_TIME + 1.2 * ring
                road_cap = BASE_ROAD_CAP * (1.0 + 0.1 * (self.N / 2 - ring))
                rent0 = max(
                    100.0,
                    np.random.normal(
                        INIT_RENT_MEAN + 15 * (self.N / 2 - ring), INIT_RENT_SD
                    ),
                )
                units_aff, units_mkt = INIT_UNITS_PER_NEIGH

                nbh = Neighborhood(
                    idx=idx,
                    pos=pos,
                    amen=amen,
                    zoning=zoning,
                    base_capacity=base_cap,
                    t0=t0,
                    road_capacity=road_cap,
                    rent=rent0,
                    rent_init=rent0,
                    units_aff=units_aff,
                    units_mkt=units_mkt,
                )
                self.neighborhoods.append(nbh)
                self.index_to_node[idx] = nbh
                idx += 1

    def _random_node(self):
        return self.index_to_node[self.rng.integers(0, self.N * self.N)]

    def _init_households(self):
        # Distribuye hogares por ingresos y barrios
        id_counter = 0
        for cls, share in INCOME_SHARES.items():
            n_cls = int(N_HOUSEHOLDS * share)
            for _ in range(n_cls):
                node = self._random_node()
                hh = Household(id_counter, cls, node.idx)
                self.households.append(hh)
                self._add_pop(node.idx, cls, +1)
                id_counter += 1

    def _add_pop(self, node_idx, cls, delta):
        n = self.index_to_node[node_idx]
        if cls == "low":
            n.pop_low += delta
        elif cls == "mid":
            n.pop_mid += delta
        else:
            n.pop_high += delta

    def _compute_travel_time(self, nbh):
        # Tiempo de viaje local con congestión
        pop = nbh.pop_low + nbh.pop_mid + nbh.pop_high
        v_c = pop / max(nbh.road_capacity, 1e-6)
        return nbh.t0 * (1.0 + BPR_A * (v_c**BPR_B))

    def _price_adjustment(self, nbh):
        # Ajuste de precios por ocupación vs objetivo con límites de cambio y piso por barrio
        occ_gap = nbh.occupancy - TARGET_OCCUPANCY
        desired = nbh.rent * (1.0 + PRICE_ADJ_ALPHA * occ_gap)

        # Límite de cambio mensual
        up_cap = 1.0 + (
            self.rent_cap_monthly
            if self.rent_cap_monthly is not None
            else MAX_RENT_CHANGE
        )
        dn_cap = 1.0 - MAX_RENT_CHANGE
        bounded = min(max(desired, nbh.rent * dn_cap), nbh.rent * up_cap)

        # Piso por barrio proporcional a la renta inicial
        floor_price = max(50.0, RENT_FLOOR_FRAC * nbh.rent_init)

        nbh.rent = max(floor_price, bounded)

    def _decay_units(self, nbh):
        # Obsolescencia leve mensual
        lost_aff = int(nbh.units_aff * UNIT_DECAY_RATE)
        lost_mkt = int(nbh.units_mkt * UNIT_DECAY_RATE)
        nbh.units_aff = max(0, nbh.units_aff - lost_aff)
        nbh.units_mkt = max(0, nbh.units_mkt - lost_mkt)

    def _neigh_features(self, nbh):
        return {
            "rent": nbh.rent,
            "travel": self._compute_travel_time(nbh),
            "amen": nbh.amen,
            "gentr": nbh.gentr_index,
            "voucher_discount": self.voucher_discount,
        }

    def _pick_destination(self, hh):
        # Selección logit sobre un subconjunto de barrios candidatos
        cand = self.rng.choice(
            self.neighborhoods, size=min(15, len(self.neighborhoods)), replace=False
        )
        utils = np.array([hh.utility(self._neigh_features(n)) for n in cand])
        utils = utils - utils.max()
        probs = np.exp(utils)
        s = probs.sum()
        if s <= 0:
            return hh.node
        probs /= s
        choice = self.rng.choice(len(cand), p=probs)
        return cand[choice].idx

    def _maybe_change_income_class(self, hh):
        # Movilidad simple y pequeña, controlada por parámetros
        r = self.rng.random()
        if hh.income_class == "low":
            if r < MOBILITY_LOW_TO_MID:
                hh.income_class = "mid"
                hh.income = INCOME_LEVELS["mid"]
        elif hh.income_class == "mid":
            if r < MOBILITY_MID_TO_HIGH:
                hh.income_class = "high"
                hh.income = INCOME_LEVELS["high"]
            elif r < MOBILITY_MID_TO_HIGH + MOBILITY_MID_TO_LOW:
                hh.income_class = "low"
                hh.income = INCOME_LEVELS["low"]
        else:  # high
            if r < MOBILITY_HIGH_TO_MID:
                hh.income_class = "mid"
                hh.income = INCOME_LEVELS["mid"]

    def _households_step(self):
        # Limpia recuentos y re-ubica con decisión
        for n in self.neighborhoods:
            n.pop_low = n.pop_mid = n.pop_high = 0
        for hh in self.households:
            # Posible movilidad de ingreso antes de registrar población
            self._maybe_change_income_class(hh)

            current = self.index_to_node[hh.node]
            if hh.wants_to_move(
                current.rent, self._compute_travel_time(current), self.rng
            ):
                dest_idx = self._pick_destination(hh)
                hh.displaced = dest_idx != hh.node
                hh.node = dest_idx
            self._add_pop(hh.node, hh.income_class, +1)

    def _developers_step(self):
        for dev in self.developers:
            dev.choose_and_build(self, self.rng)

    def _apply_policies(self):
        # Aplica eventos en el tick actual delegando en policies.py
        events_now = [e for e in POLICY_EVENTS if e[0] == self.step]
        for _, etype, payload in events_now:
            policies_mod.apply_policy(self, etype, payload)

    def _record(self):
        # Métricas de ciudad para análisis/streaming
        rents = np.array([n.rent for n in self.neighborhoods])
        travels = np.array([self._compute_travel_time(n) for n in self.neighborhoods])
        pops = np.array(
            [n.pop_low + n.pop_mid + n.pop_high for n in self.neighborhoods]
        )
        gentr = np.array([n.gentr_index for n in self.neighborhoods])
        units_aff = np.array([n.units_aff for n in self.neighborhoods])
        units_mkt = np.array([n.units_mkt for n in self.neighborhoods])
        units_total = units_aff + units_mkt

        total_pop = pops.sum() + 1e-6
        w_avg = lambda x: (x * pops).sum() / total_pop

        def gini_weighted(values, weights):
            # Calcula coeficiente Gini ponderado por población
            order = np.argsort(values)
            v = values[order]
            w = weights[order]
            cw = np.cumsum(w)
            vw = v * w
            cvw = np.cumsum(vw)
            if cw[-1] == 0 or cvw[-1] == 0:
                return 0.0
            g = 1.0 - 2.0 * np.sum((cvw / cvw[-1]) * (w / cw[-1]))
            return float(max(0.0, g))

        avg_rent = w_avg(rents)
        avg_travel = w_avg(travels)
        share_low = sum(n.pop_low for n in self.neighborhoods) / total_pop
        dispers = gini_weighted(gentr, pops)
        disp_count = sum(1 for hh in self.households if hh.displaced)
        for hh in self.households:
            hh.displaced = False

        occupancy_weighted = (pops.sum()) / max(units_total.sum(), 1e-6)
        vacancy_rate = max(0.0, 1.0 - occupancy_weighted)

        self.records.append(
            {
                "step": self.step,
                "avg_rent": avg_rent,
                "avg_travel": avg_travel,
                "share_low_income": share_low,
                "gentr_dispersion": dispers,
                "displacements": disp_count,
                "vacancy_rate": vacancy_rate,
                "aff_units": int(units_aff.sum()),
                "mkt_units": int(units_mkt.sum()),
                "total_units": int(units_total.sum()),
            }
        )

    def step_once(self):
        # 1) SD: ajustar precios + obsolescencia
        for n in self.neighborhoods:
            self._price_adjustment(n)
            self._decay_units(n)
        # 2) ABM: hogares
        self._households_step()
        # 3) Desarrolladores
        self._developers_step()
        # 4) Políticas/eventos
        self._apply_policies()
        # 5) Registro
        self._record()
        self.step += 1

    def run(self, steps=STEPS, progress_cb=None):
        for _ in range(steps):
            self.step_once()
            if progress_cb:
                progress_cb(self)

    def results_df(self):
        return pd.DataFrame(self.records)

    def spatial_grids(self):
        # Devuelve matrices N x N con variables espaciales para mapas
        rents = np.zeros((self.N, self.N))
        gentr = np.zeros((self.N, self.N))
        pop = np.zeros((self.N, self.N))
        occ = np.zeros((self.N, self.N))
        for n in self.neighborhoods:
            i, j = n.pos
            rents[i, j] = n.rent
            gentr[i, j] = n.gentr_index
            pop[i, j] = n.pop_low + n.pop_mid + n.pop_high
            occ[i, j] = n.occupancy
        return {"rent": rents, "gentr": gentr, "pop": pop, "occ": occ}
