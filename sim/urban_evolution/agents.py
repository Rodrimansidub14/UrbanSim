import numpy as np
from .config import (
    INCOME_LEVELS,
    RENT_BURDEN_THRESH,
    LAMBDA_RENT_BURDEN,
    MU_TRAVEL,
    GAMMA_AMENITIES,
    DELTA_PEERS,
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
        # Evalúa barrios con alta ocupación y precio > costo
        scores = []
        for n in city.neighborhoods:
            price = n.rent
            occ = n.occupancy
            cap_mult = n.zoning_cap_mult
            can_expand = (
                n.total_units < n.base_capacity * cap_mult
            ) and n.growth_allowed
            if can_expand:
                profit = max(0.0, price - self.unit_cost)
                # Impuesto a la vacancia: desincentiva construir donde hay alta vacancia
                vac_penalty = city.vacancy_penalty * max(0.0, 1.0 - occ)
                score = (profit - vac_penalty) * (occ - 0.85)
                scores.append((score, n))
        if not scores:
            return

        scores.sort(key=lambda x: x[0], reverse=True)
        best = scores[0][1]
        # Construye unidades respetando zonificación inclusiva
        aff_share = city.current_affordable_share
        n_aff = int(self.build_rate * aff_share)
        n_mkt = self.build_rate - n_aff
        best.add_units(n_aff, n_mkt)
