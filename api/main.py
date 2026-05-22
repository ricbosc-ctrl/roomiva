"""API REST v3 — sirve frontend + endpoints."""

import sys, os, secrets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

from models.models import (
    Candidate, Listing, Household,
    Ocupacion, EstiloConvivencia, ToleranciaRuido, Duracion, Horario,
    PreferenciaGenero, Genero, BARRIOS_BARCELONA, meses_a_duracion
)
from database.db import (
    init_db, get_user_by_email, get_user, create_user,
    update_user_candidate, update_user_listing, verify_password,
    insert_candidate, get_all_candidates, get_candidate,
    insert_listing, get_all_listings, get_listing,
    insert_household, get_all_households, get_household, get_household_by_listing,
    save_feedback, get_feedback_count
)
from engine.recommender import (
    recommend_listings_for_candidate, recommend_candidates_for_household,
    DEFAULT_WEIGHTS, get_active_weights
)

app = FastAPI(title="Roomiva API v3", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_sessions: dict = {}
_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend_v2", "index.html")

def get_uid(x_token: Optional[str] = Header(default=None)) -> int:
    if not x_token or x_token not in _sessions:
        raise HTTPException(401, "No autenticado")
    return _sessions[x_token]

@app.on_event("startup")
def startup():
    init_db()

# ── SERVE FRONTEND ──
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_index():
    with open(_FRONTEND, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ── AUTH ──
class RegisterIn(BaseModel):
    email: str; password: str; nombre: str; rol: str

class LoginIn(BaseModel):
    email: str; password: str

@app.post("/auth/register", tags=["Auth"])
def register(data: RegisterIn):
    if data.rol not in ("candidato", "propietario"):
        raise HTTPException(400, "Rol inválido")
    uid = create_user(data.email, data.password, data.rol, data.nombre)
    if uid is None:
        raise HTTPException(409, "Email ya registrado")
    token = secrets.token_hex(32)
    _sessions[token] = uid
    return {"token": token, "rol": data.rol, "nombre": data.nombre, "user_id": uid}

@app.post("/auth/login", tags=["Auth"])
def login(data: LoginIn):
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Credenciales incorrectas")
    token = secrets.token_hex(32)
    _sessions[token] = user.id
    return {"token": token, "rol": user.rol, "nombre": user.nombre,
            "user_id": user.id, "candidate_id": user.candidate_id, "listing_id": user.listing_id}

@app.get("/auth/me", tags=["Auth"])
def me(uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user: raise HTTPException(404)
    return {"user_id": user.id, "email": user.email, "rol": user.rol,
            "nombre": user.nombre, "candidate_id": user.candidate_id, "listing_id": user.listing_id}

# ── PROFILES ──
class CandidateProfileIn(BaseModel):
    edad: int; ocupacion: Ocupacion; presupuesto_max: float
    barrios_preferidos: List[str]; meses_estancia: int
    estilo_convivencia: EstiloConvivencia; tolerancia_ruido: ToleranciaRuido
    horario: Horario; acepta_mascotas: bool = False; fumador: bool = False
    genero: Genero = Genero.NO_ESPECIFICAR
    preferencia_genero: PreferenciaGenero = PreferenciaGenero.SIN_PREFERENCIA
    descripcion: Optional[str] = None

@app.post("/profile/candidate", tags=["Profile"])
def create_candidate_profile(data: CandidateProfileIn, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or user.rol != "candidato":
        raise HTTPException(403, "Solo candidatos")
    if data.meses_estancia < 3:
        raise HTTPException(400, "Mínimo 3 meses")
    for b in data.barrios_preferidos:
        if b not in BARRIOS_BARCELONA:
            raise HTTPException(400, f"Barrio desconocido: {b}")
    duracion = meses_a_duracion(data.meses_estancia)
    c = Candidate(id=0, nombre=user.nombre, edad=data.edad, ocupacion=data.ocupacion,
        presupuesto_max=data.presupuesto_max, barrios_preferidos=data.barrios_preferidos,
        meses_estancia=data.meses_estancia, duracion_deseada=duracion,
        estilo_convivencia=data.estilo_convivencia, tolerancia_ruido=data.tolerancia_ruido,
        horario=data.horario, acepta_mascotas=data.acepta_mascotas, fumador=data.fumador,
        genero=data.genero, preferencia_genero=data.preferencia_genero, descripcion=data.descripcion)
    cid = insert_candidate(c)
    update_user_candidate(uid, cid)
    return {"candidate_id": cid, "duracion_categoria": duracion.value}

class ListingProfileIn(BaseModel):
    titulo: str; barrio: str; precio_mes: float
    plazas_totales: int; plazas_disponibles: int; meses_minimos: int
    permite_mascotas: bool = False; permite_fumar: bool = False
    descripcion: Optional[str] = None
    estilo_convivencia: EstiloConvivencia; tolerancia_ruido: ToleranciaRuido
    horario_predominante: Horario; perfil_buscado_ocupacion: Optional[Ocupacion] = None
    perfil_buscado_edad_min: int = 18; perfil_buscado_edad_max: int = 99
    num_convivientes_actuales: int = 1
    preferencia_genero: PreferenciaGenero = PreferenciaGenero.SIN_PREFERENCIA
    descripcion_hogar: Optional[str] = None

@app.post("/profile/listing", tags=["Profile"])
def create_listing_profile(data: ListingProfileIn, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or user.rol != "propietario":
        raise HTTPException(403, "Solo propietarios")
    if data.barrio not in BARRIOS_BARCELONA:
        raise HTTPException(400, f"Barrio desconocido: {data.barrio}")
    if data.meses_minimos < 3:
        raise HTTPException(400, "Mínimo 3 meses")
    duracion = meses_a_duracion(data.meses_minimos)
    listing = Listing(id=0, titulo=data.titulo, barrio=data.barrio, precio_mes=data.precio_mes,
        plazas_totales=data.plazas_totales, plazas_disponibles=data.plazas_disponibles,
        duracion_minima=duracion, meses_minimos=data.meses_minimos,
        permite_mascotas=data.permite_mascotas, permite_fumar=data.permite_fumar,
        descripcion=data.descripcion)
    lid = insert_listing(listing)
    hh = Household(id=0, listing_id=lid, estilo_convivencia=data.estilo_convivencia,
        tolerancia_ruido=data.tolerancia_ruido, horario_predominante=data.horario_predominante,
        perfil_buscado_ocupacion=data.perfil_buscado_ocupacion,
        perfil_buscado_edad_min=data.perfil_buscado_edad_min,
        perfil_buscado_edad_max=data.perfil_buscado_edad_max,
        duracion_preferida=duracion, num_convivientes_actuales=data.num_convivientes_actuales,
        preferencia_genero=data.preferencia_genero, descripcion=data.descripcion_hogar)
    insert_household(hh)
    update_user_listing(uid, lid)
    return {"listing_id": lid, "duracion_categoria": duracion.value}

# ── RECOMMENDATIONS ──
class RecommendationOut(BaseModel):
    target_id: int; target_nombre: str; score_total: float; score_pct: int
    score_detalle: dict; razones: List[str]; advertencias: List[str]
    listing_info: Optional[dict] = None

@app.get("/recommend/listings", tags=["Recommendations"], response_model=List[RecommendationOut])
def recommend_for_me(top_n: int = 15, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or user.rol != "candidato" or not user.candidate_id:
        raise HTTPException(403, "Completa tu perfil primero")
    candidate = get_candidate(user.candidate_id)
    results = recommend_listings_for_candidate(candidate, get_all_listings(), get_all_households(), top_n)
    return [RecommendationOut(target_id=r.target_id, target_nombre=r.target_nombre,
            score_total=r.score_total, score_pct=r.score_pct, score_detalle=r.score_detalle,
            razones=r.razones, advertencias=r.advertencias, listing_info=r.listing_info)
            for r in results]

@app.get("/recommend/candidates", tags=["Recommendations"], response_model=List[RecommendationOut])
def recommend_candidates_for_me(top_n: int = 15, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or user.rol != "propietario" or not user.listing_id:
        raise HTTPException(403, "Completa tu perfil primero")
    listing = get_listing(user.listing_id)
    household = get_household_by_listing(user.listing_id)
    if not household: raise HTTPException(404, "Hogar no encontrado")
    results = recommend_candidates_for_household(household, listing, get_all_candidates(), top_n)
    return [RecommendationOut(target_id=r.target_id, target_nombre=r.target_nombre,
            score_total=r.score_total, score_pct=r.score_pct, score_detalle=r.score_detalle,
            razones=r.razones, advertencias=r.advertencias, listing_info=r.listing_info)
            for r in results]

# ── FEEDBACK ──
class FeedbackIn(BaseModel):
    listing_id: int; score_detalle: dict; valor: int

@app.post("/feedback", tags=["Feedback"])
def submit_feedback(data: FeedbackIn, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or not user.candidate_id:
        raise HTTPException(403, "Solo candidatos")
    if data.valor not in (0, 1):
        raise HTTPException(400, "valor debe ser 0 o 1")
    save_feedback(uid, user.candidate_id, data.listing_id, data.score_detalle, data.valor)
    return {"ok": True, "total_feedback": get_feedback_count()}

@app.get("/feedback/stats", tags=["Feedback"])
def feedback_stats():
    count = get_feedback_count()
    return {"total_feedbacks": count, "modelo_activo": count >= 10,
            "pesos_activos": get_active_weights(), "pesos_base": DEFAULT_WEIGHTS}

# ── UTILS ──
@app.get("/candidates/{cid}", tags=["Utils"])
def get_candidate_ep(cid: int):
    c = get_candidate(cid)
    if not c: raise HTTPException(404)
    return c.to_dict()

@app.get("/listings/{lid}", tags=["Utils"])
def get_listing_ep(lid: int):
    l = get_listing(lid)
    if not l: raise HTTPException(404)
    return l.to_dict()

@app.get("/barrios", tags=["Utils"])
def get_barrios():
    return {"barrios": BARRIOS_BARCELONA}

@app.get("/health", tags=["Utils"])
def health():
    return {"status": "ok", "version": "3.0.0", "feedback_count": get_feedback_count()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
