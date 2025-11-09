# Implementación de políticas urbanas aplicables al CityModel
from .config import CBD_POS
from .utils import manhattan_dist

# Cada función modifica el estado del modelo o de sus barrios


def apply_transport_invest(city, payload):
    ring = payload.get("ring")
    for n in city.neighborhoods:
        if ring is None or manhattan_dist(n.pos, CBD_POS) == ring:
            n.t0 *= payload.get("t0_factor", 1.0)
            n.road_capacity *= payload.get("capacity_factor", 1.0)


def apply_inclusionary_zoning(city, payload):
    city.current_affordable_share = payload.get(
        "aff_share", city.current_affordable_share
    )


def apply_rent_cap(city, payload):
    city.rent_cap_monthly = payload.get("monthly_cap", 0.01)


def apply_voucher_program(city, payload):
    # Descuento efectivo de renta para hogares de bajos ingresos
    city.voucher_discount = payload.get("discount_low", city.voucher_discount)


def apply_growth_boundary(city, payload):
    # Prohíbe expandir unidades en anillos exteriores
    ring_min = payload.get("ring_min", None)
    if ring_min is None:
        return
    for n in city.neighborhoods:
        if manhattan_dist(n.pos, CBD_POS) >= ring_min:
            n.growth_allowed = False


def apply_tod(city, payload):
    # Desarrollo orientado al transporte en un anillo: mejora amenidades, reduce tiempos y upzone
    ring = payload.get("ring", None)
    amen_boost = payload.get("amen_boost", 0.0)
    t0_factor = payload.get("t0_factor", 1.0)
    upzone_to = payload.get("upzone_to", None)
    for n in city.neighborhoods:
        if ring is None or manhattan_dist(n.pos, CBD_POS) == ring:
            n.amen += amen_boost
            n.t0 *= t0_factor
            if upzone_to is not None:
                n.zoning = upzone_to


def apply_amenity_investment(city, payload):
    # Mejora amenidades en posiciones puntuales
    for pos in payload.get("positions", []):
        for n in city.neighborhoods:
            if tuple(n.pos) == tuple(pos):
                n.amen += payload.get("delta", 0.0)


def apply_upzoning_cluster(city, payload):
    # Cambia zonificación en un cluster circular Manhattan
    center = payload.get("center")
    radius = payload.get("radius", 1)
    new_zoning = payload.get("new_zoning", 2)
    if center is None:
        return
    for n in city.neighborhoods:
        if manhattan_dist(n.pos, center) <= radius:
            n.zoning = new_zoning


def apply_vacancy_tax(city, payload):
    # Ajusta penalización por vacancia (afecta decisión de desarrolladores)
    city.vacancy_penalty = float(payload.get("penalty", city.vacancy_penalty))


# Mapeo de políticas
_POLICY_MAP = {
    "transport_invest": apply_transport_invest,
    "inclusionary_zoning": apply_inclusionary_zoning,
    "rent_cap": apply_rent_cap,
    "voucher_program": apply_voucher_program,
    "growth_boundary": apply_growth_boundary,
    "tod": apply_tod,
    "amenity_investment": apply_amenity_investment,
    "upzoning_cluster": apply_upzoning_cluster,
    "vacancy_tax": apply_vacancy_tax,
}


def apply_policy(city, etype, payload):
    # Aplica la política correspondiente si existe
    fn = _POLICY_MAP.get(etype)
    if fn is not None:
        fn(city, payload)
