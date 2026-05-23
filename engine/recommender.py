"""Motor de recomendación v4 — compatibilidad grupal con ML en función de agregación."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Tuple, Optional
from models.models import (
    Candidate, Listing, Household, Roommate,
    RecommendationResult, RoommateScore,
    EstiloConvivencia, ToleranciaRuido, Duracion, Horario,
    Ocupacion, PreferenciaGenero, Genero
)

# ── PESOS DE CRITERIOS (fijos, sobre el score individual) ──
CRITERIA_WEIGHTS = {
    "estilo_convivencia": 0.30,
    "tolerancia_ruido":   0.20,
    "horario":            0.18,
    "edad":               0.12,
    "ocupacion":          0.10,
    "genero":             0.10,
}

# ── PESOS DE AGREGACIÓN GRUPAL (aprendidos por ML) ──
DEFAULT_ALPHA = {"alpha_mean": 0.40, "alpha_min": 0.30, "alpha_weighted": 0.30}

SCORE_THRESHOLD = 0.50
_DURACION_ORDER = {Duracion.CORTA: 0, Duracion.MEDIA: 1, Duracion.LARGA: 2}
_RUIDO_ORDER    = {ToleranciaRuido.BAJA: 0, ToleranciaRuido.MEDIA: 1, ToleranciaRuido.ALTA: 2}


def get_alpha_weights() -> dict:
    """Carga los pesos de agregación del modelo ML si existen."""
    try:
        from database.db import get_ml_weights
        w = get_ml_weights()
        if w["sample_count"] >= 10:
            return {"alpha_mean": w["alpha_mean"], "alpha_min": w["alpha_min"],
                    "alpha_weighted": w["alpha_weighted"]}
    except Exception:
        pass
    return DEFAULT_ALPHA


# ── SCORES INDIVIDUALES CANDIDATO VS CONVIVIENTE ──

def _score_estilo(c, r) -> Tuple[float, str]:
    if c == r: return 1.0, f"El conviviente también es {r.value} — estilos idénticos"
    if EstiloConvivencia.MIXTO in (c, r): return 0.65, f"El conviviente es {r.value}, compatible"
    return 0.15, f"El conviviente es {r.value} y tú prefieres {c.value} — estilos opuestos"

def _score_ruido(c, r) -> Tuple[float, str]:
    diff = abs(_RUIDO_ORDER[c] - _RUIDO_ORDER[r])
    if diff == 0: return 1.0, f"Misma tolerancia al ruido ({r.value})"
    if diff == 1: return 0.55, f"Tolerancia al ruido del conviviente: {r.value}, similar a la tuya"
    return 0.10, f"Tolerancia al ruido del conviviente: {r.value} — muy diferente a la tuya"

def _score_horario(c, r) -> Tuple[float, str]:
    if c == r: return 1.0, f"El conviviente tiene horario {r.value}, igual que tú"
    if Horario.FLEXIBLE in (c, r): return 0.72, f"Horario {r.value}, fácil de compatibilizar"
    return 0.15, f"El conviviente tiene horario {r.value} y el tuyo es {c.value} — pueden chocar"

def _score_edad(c_age, r_age) -> Tuple[float, str]:
    diff = abs(c_age - r_age)
    if diff <= 3: return 1.0, f"El conviviente tiene {r_age} años, muy similar a ti"
    if diff <= 8: return 0.75, f"El conviviente tiene {r_age} años, rango similar"
    if diff <= 15: return 0.45, f"El conviviente tiene {r_age} años, diferencia notable"
    return 0.15, f"El conviviente tiene {r_age} años, diferencia de edad grande"

def _score_ocupacion(c, r) -> Tuple[float, str]:
    if c == r: return 1.0, f"El conviviente también es {r.value}"
    if r == Ocupacion.OTRO or c == Ocupacion.OTRO: return 0.60, "Perfiles ocupacionales distintos pero sin conflicto"
    return 0.35, f"El conviviente es {r.value} y tú eres {c.value}"

def _score_genero(c_gen, c_pref, r_gen, r_pref) -> Tuple[float, str]:
    if c_pref == PreferenciaGenero.SIN_PREFERENCIA and r_pref == PreferenciaGenero.SIN_PREFERENCIA:
        return 1.0, "Sin preferencias de género"
    if r_pref == PreferenciaGenero.MIXTO or c_pref == PreferenciaGenero.MIXTO:
        return 1.0, "El conviviente prefiere entorno mixto"
    if r_pref == PreferenciaGenero.SIN_PREFERENCIA and c_pref == PreferenciaGenero.SIN_PREFERENCIA:
        return 1.0, "Sin restricciones de género"
    return 0.75, "Preferencias de género compatibles"


def compute_candidate_roommate_score(candidate: Candidate, roommate: Roommate) -> Tuple[float, dict, List[str], List[str]]:
    """Score de compatibilidad entre un candidato y un conviviente individual."""
    scores = {}
    razones = []
    advertencias = []

    criterios = [
        ("estilo_convivencia", _score_estilo(candidate.estilo_convivencia, roommate.estilo_convivencia)),
        ("tolerancia_ruido",   _score_ruido(candidate.tolerancia_ruido, roommate.tolerancia_ruido)),
        ("horario",            _score_horario(candidate.horario, roommate.horario)),
        ("edad",               _score_edad(candidate.edad, roommate.edad)),
        ("ocupacion",          _score_ocupacion(candidate.ocupacion, roommate.ocupacion)),
        ("genero",             _score_genero(candidate.genero, candidate.preferencia_genero,
                                             roommate.genero, roommate.preferencia_genero)),
    ]

    for key, (score, msg) in criterios:
        scores[key] = score
        (razones if score >= 0.65 else advertencias).append(msg)

    total = sum(CRITERIA_WEIGHTS.get(k, 0) * scores[k] for k in scores)
    return round(total, 4), scores, razones, advertencias


def aggregate_group_score(
    roommate_scores: List[float],
    roommate_weights: List[float],
    alpha: dict
) -> Tuple[float, str]:
    """
    Combina los scores individuales en un score grupal usando tres métodos:
    - mean: media aritmética (todos pesan igual)
    - min: mínimo (el más difícil de convencer marca el score)
    - weighted: media ponderada (propietario pesa más)

    El score final es una combinación lineal de los tres, con pesos aprendidos por ML.
    """
    if not roommate_scores:
        return 0.5, "mean"

    score_mean = sum(roommate_scores) / len(roommate_scores)

    score_min = min(roommate_scores)

    total_w = sum(roommate_weights)
    score_weighted = sum(s * w for s, w in zip(roommate_scores, roommate_weights)) / total_w if total_w > 0 else score_mean

    alpha_mean = alpha.get("alpha_mean", 0.40)
    alpha_min  = alpha.get("alpha_min",  0.30)
    alpha_w    = alpha.get("alpha_weighted", 0.30)

    final = alpha_mean * score_mean + alpha_min * score_min + alpha_w * score_weighted
    return round(final, 4), "hybrid"


# ── HARD CONSTRAINTS ──
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


# ── RECOMENDACIÓN PRINCIPAL ──
def recommend_listings_for_candidate(
    candidate: Candidate,
    listings: List[Listing],
    households: List[Household],
    all_roommates: List[Roommate],
    top_n: int = 15,
    threshold: float = SCORE_THRESHOLD
) -> List[RecommendationResult]:

    hh_map = {h.listing_id: h for h in households}
    rm_map: dict = {}
    for rm in all_roommates:
        rm_map.setdefault(rm.listing_id, []).append(rm)

    alpha = get_alpha_weights()
    results = []

    for listing in listings:
        passes, _ = check_hard_constraints(candidate, listing)
        if not passes:
            continue

        roommates = rm_map.get(listing.id, [])
        household = hh_map.get(listing.id)

        if not roommates:
            # Sin convivientes definidos: score base
            results.append(RecommendationResult(
                target_id=listing.id, target_nombre=listing.titulo,
                score_total=0.55, score_detalle={},
                razones=["Hogar sin convivientes registrados"], advertencias=[],
                hard_constraints_ok=True,
                listing_info=_listing_info(listing, household)
            ))
            continue

        # Score individual contra cada conviviente
        rm_scores_list = []
        rm_score_objs = []
        rm_weights = []

        for rm in roommates:
            sc, det, raz, adv = compute_candidate_roommate_score(candidate, rm)
            rm_scores_list.append(sc)
            rm_weights.append(1.0)
            rm_score_objs.append(RoommateScore(
                roommate_id=rm.id, roommate_nombre=rm.nombre,
                score=sc, detalle=det, razones=raz, advertencias=adv
            ))

        # Agregación grupal con pesos ML
        score_total, method = aggregate_group_score(rm_scores_list, rm_weights, alpha)

        # Score de duración vs hogar
        dur_score = 1.0
        if household:
            dc = _DURACION_ORDER[candidate.duracion_deseada]
            dh = _DURACION_ORDER[household.duracion_preferida]
            if dc < dh:
                dur_score = 0.50 if dc == dh - 1 else 0.10
            # Ajuste leve del score grupal con duración
            score_total = round(score_total * 0.90 + dur_score * 0.10, 4)

        if score_total < threshold:
            continue

        # Razones y advertencias del mejor conviviente
        best = max(rm_score_objs, key=lambda x: x.score)
        razones = best.razones[:3]
        advertencias = best.advertencias[:2]

        # Score detalle = media de scores parciales de todos los convivientes
        all_keys = list(CRITERIA_WEIGHTS.keys())
        mean_detalle = {}
        for k in all_keys:
            vals = [rm.detalle.get(k, 0) for rm in rm_score_objs if k in rm.detalle]
            mean_detalle[k] = round(sum(vals) / len(vals), 3) if vals else 0.0

        results.append(RecommendationResult(
            target_id=listing.id, target_nombre=listing.titulo,
            score_total=score_total, score_detalle=mean_detalle,
            razones=razones, advertencias=advertencias,
            hard_constraints_ok=True,
            roommate_scores=rm_score_objs,
            listing_info=_listing_info(listing, household),
            aggregation_method=method
        ))

    results.sort(key=lambda r: r.score_total, reverse=True)
    return results[:top_n]


def _listing_info(listing: Listing, household: Optional[Household]) -> dict:
    info = {
        "barrio": listing.barrio, "precio_mes": listing.precio_mes,
        "plazas_disponibles": listing.plazas_disponibles,
        "plazas_totales": listing.plazas_totales,
        "permite_mascotas": listing.permite_mascotas,
        "permite_fumar": listing.permite_fumar,
        "meses_minimos": listing.meses_minimos,
        "descripcion": listing.descripcion or "",
    }
    if household:
        info["duracion_preferida"] = household.duracion_preferida.value
        info["edad_min"] = household.perfil_buscado_edad_min
        info["edad_max"] = household.perfil_buscado_edad_max
    return info
