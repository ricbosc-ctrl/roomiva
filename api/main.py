"""API REST v4 — compatibilidad grupal."""

import sys, os, secrets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Depends, Header
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
    insert_household, get_all_households, get_household_by_listing,
    get_all_roommates, get_roommates_by_listing,
    save_feedback, get_feedback_count, get_ml_weights
)
from engine.recommender import recommend_listings_for_candidate, DEFAULT_ALPHA

app = FastAPI(title="Roomiva API v4 — Group Compatibility", version="4.0.0")
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

# ── PROFILE ──
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

# ── RECOMMENDATIONS ──
class RoommateScoreOut(BaseModel):
    roommate_id: int; roommate_nombre: str; score: float; score_pct: int
    razones: List[str]; advertencias: List[str]

class RecommendationOut(BaseModel):
    target_id: int; target_nombre: str; score_total: float; score_pct: int
    score_detalle: dict; razones: List[str]; advertencias: List[str]
    roommate_scores: List[RoommateScoreOut]
    listing_info: Optional[dict] = None

@app.get("/recommend/listings", tags=["Recommendations"], response_model=List[RecommendationOut])
def recommend_for_me(top_n: int = 15, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or user.rol != "candidato" or not user.candidate_id:
        raise HTTPException(403, "Completa tu perfil primero")
    candidate = get_candidate(user.candidate_id)
    results = recommend_listings_for_candidate(
        candidate, get_all_listings(), get_all_households(), get_all_roommates(), top_n)
    return [RecommendationOut(
        target_id=r.target_id, target_nombre=r.target_nombre,
        score_total=r.score_total, score_pct=r.score_pct,
        score_detalle=r.score_detalle, razones=r.razones, advertencias=r.advertencias,
        roommate_scores=[RoommateScoreOut(
            roommate_id=rs.roommate_id, roommate_nombre=rs.roommate_nombre,
            score=rs.score, score_pct=rs.score_pct,
            razones=rs.razones, advertencias=rs.advertencias)
            for rs in r.roommate_scores],
        listing_info=r.listing_info) for r in results]

# ── FEEDBACK ──
class FeedbackIn(BaseModel):
    listing_id: int; scores: dict; valor: int

@app.post("/feedback", tags=["Feedback"])
def submit_feedback(data: FeedbackIn, uid: int = Depends(get_uid)):
    user = get_user(uid)
    if not user or not user.candidate_id:
        raise HTTPException(403, "Solo candidatos")
    if data.valor not in (0, 1):
        raise HTTPException(400, "valor debe ser 0 o 1")
    save_feedback(uid, user.candidate_id, data.listing_id, data.scores, data.valor)
    return {"ok": True, "total_feedback": get_feedback_count()}

@app.get("/feedback/stats", tags=["Feedback"])
def feedback_stats():
    count = get_feedback_count()
    weights = get_ml_weights()
    return {
        "total_feedbacks": count,
        "modelo_activo": count >= 10,
        "alpha_actual": {k: weights[k] for k in ["alpha_mean","alpha_min","alpha_weighted"]},
        "alpha_base": DEFAULT_ALPHA,
        "precision_modelo": weights.get("accuracy", 0),
        "muestras_entrenamiento": weights.get("sample_count", 0),
    }

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

@app.get("/listings/{lid}/roommates", tags=["Utils"])
def get_listing_roommates(lid: int):
    return [rm.to_dict() for rm in get_roommates_by_listing(lid)]

@app.get("/barrios", tags=["Utils"])
def get_barrios():
    return {"barrios": BARRIOS_BARCELONA}

@app.get("/health", tags=["Utils"])
def health():
    return {"status": "ok", "version": "4.0.0", "feedback_count": get_feedback_count()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
