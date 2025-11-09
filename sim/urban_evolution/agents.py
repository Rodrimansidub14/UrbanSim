import numpy as np
from .config import (
    INCOME_LEVELS,
    RENT_BURDEN_THRESH,
    LAMBDA_RENT_BURDEN,
    MU_TRAVEL,
    GAMMA_AMENITIES,
    DELTA_PEERS,
    BUILD_MIN_PROFIT,
    BUILD_OCC_THRESHOLD,
)


class Household:
    # Representa un hogar con ingreso, ubicación y comportamiento de relocalización
    def __init__(self, hid, income_class, node):
        self.id = hid
        self.income_class = income_class
        self.income = INCOME_LEVELS[income_class]
        self.node = node
        self.displaced = False

    def wants_to_move(self, current_rent, travel_time, rng):
        # Carga de renta actual
        burden = current_rent / max(self.income, 1e-6)
        if burden > RENT_BURDEN_THRESH[self.income_class]:
            return True
        # Probabilidad espontánea pequeña
        return rng.random() < 0.01

    def utility(self, n_features):
        # n_features: dict con rent, travel, amenities, gentr, voucher_discount
        rent = n_features["rent"]
        # Aplica descuento de renta si el programa de vales está activo para ingresos bajos
        voucher_disc = n_features.get("voucher_discount", 0.0)
        if self.income_class == "low":
            rent = rent * (1.0 - voucher_disc)

        travel = n_features["travel"]
        amen = n_features["amen"]
        g = n_features["gentr"]

        # Preferencia por pares: alta renta atrae a high; low prefiere g bajo
        peer_term = g if self.income_class == "high" else (1.0 - g)
        u = (
            -LAMBDA_RENT_BURDEN * (rent / max(self.income, 1e-6))
            - MU_TRAVEL * travel
            + GAMMA_AMENITIES * amen
            + DELTA_PEERS * peer_term
        )
        return u


class Developer:
    # Desarrollador invierte según rentabilidad esperada y ocupación
    def __init__(self, did, unit_cost, build_rate):
        self.id = did
        self.unit_cost = unit_cost
        self.build_rate = build_rate

    def choose_and_build(self, city, rng):
        # Construye solo si hay alta ocupación y margen suficiente
        candidates = []
        for n in city.neighborhoods:
            if not n.growth_allowed:
                continue
            cap_mult = n.zoning_cap_mult
            if n.total_units >= n.base_capacity * cap_mult:
                continue

            price = n.rent
            occ = n.occupancy
            margin = price - self.unit_cost

            # Filtros de racionalidad para evitar sobreoferta crónica
            if margin < BUILD_MIN_PROFIT:
                continue
            if occ < BUILD_OCC_THRESHOLD:
                continue

            # Impuesto a la vacancia: desincentiva construir donde hay alta vacancia
            vac_penalty = city.vacancy_penalty * max(0.0, 1.0 - occ)
            score = (margin - vac_penalty) * occ
            candidates.append((score, n))

        if not candidates:
            return

        # Selecciona el mejor candidato
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]
        if candidates[0][0] <= 0:
            return  # evita construir si el puntaje no es positivo

        # Construye unidades respetando zonificación inclusiva
        aff_share = city.current_affordable_share
        n_aff = int(round(self.build_rate * aff_share))
        n_mkt = int(self.build_rate - n_aff)
        best.add_units(n_aff, n_mkt)
