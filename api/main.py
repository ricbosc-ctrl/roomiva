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
    save_feedback, get_feedback_count, get_ml_weights, get_all_feedback
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
    roommate_info: Optional[dict] = None
    roommate_info: Optional[dict] = None

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
            razones=rs.razones, advertencias=rs.advertencias,
            roommate_info=rs.roommate_info)
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


# ── ADMIN ──
@app.get("/admin/stats", tags=["Admin"], response_class=HTMLResponse)
def admin_stats():
    candidates = get_all_candidates()
    feedbacks = get_all_feedback()
    listings = get_all_listings()
    roommates = get_all_roommates()
    ml = get_ml_weights()

    total_likes    = sum(1 for f in feedbacks if f['valor'] == 1)
    total_dislikes = sum(1 for f in feedbacks if f['valor'] == 0)

    def cand_row(c):
        return (f"<tr><td>{c.id}</td><td>{c.nombre}</td><td>{c.edad}</td>"
                f"<td>{c.ocupacion.value}</td><td>{c.presupuesto_max}€</td>"
                f"<td>{', '.join(c.barrios_preferidos)}</td>"
                f"<td>{c.meses_estancia}m · {c.duracion_deseada.value}</td>"
                f"<td>{c.estilo_convivencia.value}</td><td>{c.tolerancia_ruido.value}</td>"
                f"<td>{c.horario.value}</td><td>{c.genero.value}</td></tr>")

    def fb_row(f):
        color = "#16A34A" if f['valor'] == 1 else "#DC2626"
        label = "Me interesa" if f['valor'] == 1 else "No encaja"
        sm = f"{round(f['score_mean']*100)}%" if f['score_mean'] is not None else "-"
        si = f"{round(f['score_min']*100)}%" if f['score_min'] is not None else "-"
        return (f"<tr><td>{f['id']}</td><td>{f['user_id']}</td>"
                f"<td>{f['candidate_id']}</td><td>{f['listing_id']}</td>"
                f"<td style='color:{color};font-weight:600'>{label}</td>"
                f"<td>{sm}</td><td>{si}</td>"
                f"<td>{str(f['created_at'])[:16]}</td></tr>")

    cand_rows = "".join(cand_row(c) for c in candidates)
    fb_rows   = "".join(fb_row(f) for f in feedbacks)
    ml_status = f"Activo ({ml['sample_count']} muestras)" if ml['sample_count'] >= 10 else "Inactivo — necesita 10+ feedbacks"
    ml_color  = "#16A34A" if ml['sample_count'] >= 10 else "#D97706"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Roomiva Admin</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Arial,sans-serif;background:#F7F5F0;color:#111;padding:40px}}
h1{{font-size:1.8rem;color:#1A3A2A;margin-bottom:4px}}
h2{{font-size:1rem;font-weight:600;color:#2D6147;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid #E8E6E0}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0}}
.card{{background:white;border:1px solid #E8E6E0;border-radius:10px;padding:20px;text-align:center}}
.n{{font-size:2rem;font-weight:700;color:#1A3A2A}}
.l{{font-size:0.8rem;color:#6B6A65;margin-top:4px}}
table{{width:100%;border-collapse:collapse;background:white;border-radius:10px;overflow:hidden;border:1px solid #E8E6E0;font-size:0.8rem;margin-bottom:8px}}
th{{background:#1A3A2A;color:white;padding:9px 12px;text-align:left;font-weight:500}}
td{{padding:8px 12px;border-bottom:1px solid #F0EDE8}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#F7F5F0}}
.btn{{display:inline-block;padding:7px 16px;background:#1A3A2A;color:white;border-radius:6px;text-decoration:none;font-size:0.8rem;margin-right:8px}}
.ml{{background:white;border:1px solid #E8E6E0;border-radius:10px;padding:20px;margin:8px 0 16px}}
.ml-r{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #F0EDE8;font-size:0.85rem}}
.ml-r:last-child{{border-bottom:none}}
</style>
</head>
<body>
<h1>Roomiva — Panel de Administración</h1>
<p style="color:#6B6A65;margin-top:4px">{len(candidates)} candidatos · {len(feedbacks)} feedbacks · {len(listings)} pisos · {len(roommates)} convivientes</p>

<div class="grid">
  <div class="card"><div class="n">{len(candidates)}</div><div class="l">Candidatos</div></div>
  <div class="card"><div class="n">{len(feedbacks)}</div><div class="l">Feedbacks</div></div>
  <div class="card"><div class="n" style="color:#16A34A">{total_likes}</div><div class="l">Me interesa</div></div>
  <div class="card"><div class="n" style="color:#DC2626">{total_dislikes}</div><div class="l">No encaja</div></div>
</div>

<h2>Modelo ML</h2>
<div class="ml">
  <div class="ml-r"><span>Estado</span><span style="color:{ml_color};font-weight:600">{ml_status}</span></div>
  <div class="ml-r"><span>Alpha media (todos pesan igual)</span><span style="font-weight:600">{round(ml['alpha_mean']*100)}%</span></div>
  <div class="ml-r"><span>Alpha mínimo (el más difícil marca el score)</span><span style="font-weight:600">{round(ml['alpha_min']*100)}%</span></div>
  <div class="ml-r"><span>Alpha ponderado</span><span style="font-weight:600">{round(ml['alpha_weighted']*100)}%</span></div>
  <div class="ml-r"><span>Precisión del modelo</span><span style="font-weight:600">{round(ml['accuracy']*100)}%</span></div>
</div>
<a class="btn" href="/admin/candidates.csv">Descargar candidatos CSV</a>
<a class="btn" href="/admin/feedback.csv">Descargar feedback CSV</a>

<h2>Candidatos registrados ({len(candidates)})</h2>
<table>
<thead><tr><th>ID</th><th>Nombre</th><th>Edad</th><th>Ocupación</th><th>Presupuesto</th><th>Barrios</th><th>Estancia</th><th>Estilo</th><th>Ruido</th><th>Horario</th><th>Género</th></tr></thead>
<tbody>{cand_rows if cand_rows else '<tr><td colspan="11" style="text-align:center;color:#6B6A65;padding:20px">Sin candidatos todavía</td></tr>'}</tbody>
</table>

<h2>Feedbacks ({len(feedbacks)})</h2>
<table>
<thead><tr><th>ID</th><th>Usuario</th><th>Candidato</th><th>Piso</th><th>Valoración</th><th>Score medio</th><th>Score mínimo</th><th>Fecha</th></tr></thead>
<tbody>{fb_rows if fb_rows else '<tr><td colspan="8" style="text-align:center;color:#6B6A65;padding:20px">Sin feedbacks todavía</td></tr>'}</tbody>
</table>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/admin/candidates.csv", tags=["Admin"])
def export_candidates_csv():
    from fastapi.responses import Response
    candidates = get_all_candidates()
    lines = ["id,nombre,edad,ocupacion,presupuesto_max,barrios,meses_estancia,estilo,ruido,horario,genero,fumador,mascotas"]
    for c in candidates:
        barrios = "|".join(c.barrios_preferidos)
        lines.append(f'{c.id},{c.nombre},{c.edad},{c.ocupacion.value},{c.presupuesto_max},{barrios},{c.meses_estancia},{c.estilo_convivencia.value},{c.tolerancia_ruido.value},{c.horario.value},{c.genero.value},{int(c.fumador)},{int(c.acepta_mascotas)}')
    return Response(content="\n".join(lines), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=candidatos.csv"})


@app.get("/admin/feedback.csv", tags=["Admin"])
def export_feedback_csv():
    from fastapi.responses import Response
    feedbacks = get_all_feedback()
    lines = ["id,user_id,candidate_id,listing_id,valor,score_mean,score_min,score_weighted,created_at"]
    for f in feedbacks:
        lines.append(f'{f["id"]},{f["user_id"]},{f["candidate_id"]},{f["listing_id"]},{f["valor"]},{f["score_mean"]},{f["score_min"]},{f["score_weighted"]},{f["created_at"]}')
    return Response(content="\n".join(lines), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=feedback.csv"})
