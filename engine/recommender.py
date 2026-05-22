"""Motor de recomendación v3 — género, umbral 50%, pesos ML."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Tuple, Optional
from models.models import (
    Candidate, Listing, Household, RecommendationResult,
    EstiloConvivencia, ToleranciaRuido, Duracion, Horario, Ocupacion,
    PreferenciaGenero, Genero
)

DEFAULT_WEIGHTS = {
    "estilo_convivencia": 0.28,
    "tolerancia_ruido":   0.18,
    "horario":            0.14,
    "duracion":           0.14,
    "edad":               0.10,
    "ocupacion":          0.08,
    "genero":             0.08,
}

SCORE_THRESHOLD = 0.50

_DURACION_ORDER = {Duracion.CORTA: 0, Duracion.MEDIA: 1, Duracion.LARGA: 2}
_RUIDO_ORDER    = {ToleranciaRuido.BAJA: 0, ToleranciaRuido.MEDIA: 1, ToleranciaRuido.ALTA: 2}


def get_active_weights() -> dict:
    path = os.path.join(os.path.dirname(__file__), "ml_weights.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return DEFAULT_WEIGHTS


def _score_estilo(c, h) -> Tuple[float, str]:
    if c == h: return 1.0, f"El hogar también es {h.value} — estilos idénticos"
    if EstiloConvivencia.MIXTO in (c, h): return 0.65, f"El hogar es {h.value}, compatible con tu estilo"
    return 0.15, f"El hogar es {h.value} y tú prefieres {c.value} — estilos opuestos"

def _score_ruido(c, h) -> Tuple[float, str]:
    diff = abs(_RUIDO_ORDER[c] - _RUIDO_ORDER[h])
    if diff == 0: return 1.0, f"El hogar tiene tolerancia al ruido {h.value}, igual que tú"
    if diff == 1: return 0.55, f"El hogar tiene tolerancia al ruido {h.value}, similar a la tuya"
    return 0.10, f"El hogar tiene tolerancia al ruido {h.value} y la tuya es {c.value} — muy diferente"

def _score_horario(c, h) -> Tuple[float, str]:
    if c == h: return 1.0, f"El hogar tiene horario {h.value}, igual que tú"
    if Horario.FLEXIBLE in (c, h): return 0.72, f"El hogar tiene horario {h.value}, fácil de compatibilizar"
    return 0.15, f"El hogar tiene horario {h.value} y el tuyo es {c.value} — pueden chocar"

def _score_duracion(c, h) -> Tuple[float, str]:
    dc, dh = _DURACION_ORDER[c], _DURACION_ORDER[h]
    if dc >= dh: return 1.0, f"El hogar acepta estancia {h.value}, compatible con tu plan"
    if dc == dh - 1: return 0.50, f"El hogar prefiere estancia {h.value} y tú buscas {c.value}"
    return 0.10, f"El hogar exige estancia {h.value} pero tú buscas {c.value} — incompatible"

def _score_edad(age, age_min, age_max) -> Tuple[float, str]:
    if age_min <= age <= age_max: return 1.0, f"El hogar busca personas de {age_min}–{age_max} años — encajas"
    diff = max(age_min - age, age - age_max)
    if diff <= 5: return 0.55, f"El hogar busca {age_min}–{age_max} años, estás cerca del rango"
    return 0.15, f"El hogar busca {age_min}–{age_max} años — fuera de su rango preferido"

def _score_ocupacion(c, pref) -> Tuple[float, str]:
    if pref is None: return 1.0, "El hogar no tiene preferencia de ocupación"
    if c == pref: return 1.0, f"El hogar busca {pref.value} — coincide con tu perfil"
    return 0.40, f"El hogar prefiere {pref.value}, tú eres {c.value}"

def _score_genero(c_genero, c_pref, h_pref) -> Tuple[float, str]:
    if h_pref == PreferenciaGenero.SIN_PREFERENCIA and c_pref == PreferenciaGenero.SIN_PREFERENCIA:
        return 1.0, "El hogar no tiene preferencia de género"
    if c_genero is None or c_genero == Genero.NO_ESPECIFICAR:
        if h_pref == PreferenciaGenero.SIN_PREFERENCIA: return 1.0, "El hogar no tiene preferencia de género"
        return 0.70, "El hogar tiene preferencia de género pero tú no lo has especificado"
    if h_pref == PreferenciaGenero.MIXTO:
        return 1.0, "El hogar busca entorno mixto — bienvenido/a"
    if h_pref == PreferenciaGenero.SIN_PREFERENCIA:
        return 1.0, "El hogar acepta cualquier género"
    return 0.80, "La preferencia de género es compatible con el hogar"


def check_hard_constraints(candidate: Candidate, listing: Listing) -> Tuple[bool, List[str]]:
    rejections = []
    if candidate.presupuesto_max < listing.precio_mes:
        rejections.append(f"Presupuesto insuficiente ({candidate.presupuesto_max}€ < {listing.precio_mes}€/mes)")
    if listing.barrio not in candidate.barrios_preferidos:
        rejections.append(f"Barrio no preferido ({listing.barrio})")
    if _DURACION_ORDER[candidate.duracion_deseada] < _DURACION_ORDER[listing.duracion_minima]:
        rejections.append(f"Duración incompatible")
    if candidate.fumador and not listing.permite_fumar:
        rejections.append("El piso no permite fumar")
    if listing.plazas_disponibles < 1:
        rejections.append("Sin plazas disponibles")
    return len(rejections) == 0, rejections


def compute_soft_score(candidate: Candidate, household: Household) -> Tuple[float, dict, List[str], List[str]]:
    weights = get_active_weights()
    scores = {}
    razones = []
    advertencias = []

    criterios = [
        ("estilo_convivencia", _score_estilo(candidate.estilo_convivencia, household.estilo_convivencia)),
        ("tolerancia_ruido",   _score_ruido(candidate.tolerancia_ruido, household.tolerancia_ruido)),
        ("horario",            _score_horario(candidate.horario, household.horario_predominante)),
        ("duracion",           _score_duracion(candidate.duracion_deseada, household.duracion_preferida)),
        ("edad",               _score_edad(candidate.edad, household.perfil_buscado_edad_min, household.perfil_buscado_edad_max)),
        ("ocupacion",          _score_ocupacion(candidate.ocupacion, household.perfil_buscado_ocupacion)),
        ("genero",             _score_genero(candidate.genero, candidate.preferencia_genero, household.preferencia_genero)),
    ]

    for key, (score, msg) in criterios:
        scores[key] = score
        (razones if score >= 0.65 else advertencias).append(msg)

    total = sum(weights.get(k, 0) * scores[k] for k in scores)
    return round(total, 4), scores, razones, advertencias


def recommend_listings_for_candidate(
    candidate: Candidate, listings: List[Listing], households: List[Household],
    top_n: int = 15, threshold: float = SCORE_THRESHOLD
) -> List[RecommendationResult]:

    hh_map = {h.listing_id: h for h in households}
    results = []

    for listing in listings:
        passes, _ = check_hard_constraints(candidate, listing)
        if not passes:
            continue
        household = hh_map.get(listing.id)
        if household is None:
            score_total, detalle, razones, advertencias = 0.55, {}, ["Piso sin hogar definido"], []
        else:
            score_total, detalle, razones, advertencias = compute_soft_score(candidate, household)

        if score_total < threshold:
            continue

        results.append(RecommendationResult(
            target_id=listing.id, target_nombre=listing.titulo,
            score_total=score_total, score_detalle=detalle,
            razones=razones, advertencias=advertencias,
            hard_constraints_ok=True,
            listing_info={
                "barrio": listing.barrio, "precio_mes": listing.precio_mes,
                "plazas_disponibles": listing.plazas_disponibles,
                "plazas_totales": listing.plazas_totales,
                "permite_mascotas": listing.permite_mascotas,
                "permite_fumar": listing.permite_fumar,
                "meses_minimos": listing.meses_minimos,
                "descripcion": listing.descripcion or "",
            }
        ))

    results.sort(key=lambda r: r.score_total, reverse=True)
    return results[:top_n]


def recommend_candidates_for_household(
    household: Household, listing: Listing, candidates: List[Candidate],
    top_n: int = 15, threshold: float = SCORE_THRESHOLD
) -> List[RecommendationResult]:

    results = []
    for candidate in candidates:
        passes, _ = check_hard_constraints(candidate, listing)
        if not passes:
            continue
        score_total, detalle, razones, advertencias = compute_soft_score(candidate, household)
        if score_total < threshold:
            continue
        results.append(RecommendationResult(
            target_id=candidate.id, target_nombre=candidate.nombre,
            score_total=score_total, score_detalle=detalle,
            razones=razones, advertencias=advertencias,
            hard_constraints_ok=True,
            listing_info={
                "edad": candidate.edad, "ocupacion": candidate.ocupacion.value,
                "presupuesto_max": candidate.presupuesto_max,
                "meses_estancia": candidate.meses_estancia,
                "barrios": ", ".join(candidate.barrios_preferidos),
            }
        ))

    results.sort(key=lambda r: r.score_total, reverse=True)
    return results[:top_n]
