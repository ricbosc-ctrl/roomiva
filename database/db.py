"""Capa de persistencia SQLite v4 — compatibilidad grupal."""

import sqlite3, os, hashlib
from typing import List, Optional
from models.models import (
    Candidate, Listing, Household, Roommate, User,
    Ocupacion, EstiloConvivencia, ToleranciaRuido, Duracion, Horario,
    PreferenciaGenero, Genero, meses_a_duracion
)

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "coliving.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, edad INTEGER NOT NULL,
            ocupacion TEXT NOT NULL, presupuesto_max REAL NOT NULL,
            barrios_preferidos TEXT NOT NULL,
            meses_estancia INTEGER NOT NULL DEFAULT 6,
            duracion_deseada TEXT NOT NULL,
            estilo_convivencia TEXT NOT NULL, tolerancia_ruido TEXT NOT NULL,
            horario TEXT NOT NULL, acepta_mascotas INTEGER DEFAULT 0,
            fumador INTEGER DEFAULT 0,
            genero TEXT DEFAULT 'no_especificar',
            preferencia_genero TEXT DEFAULT 'sin_preferencia',
            descripcion TEXT
        );
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL, barrio TEXT NOT NULL,
            precio_mes REAL NOT NULL, plazas_totales INTEGER NOT NULL,
            plazas_disponibles INTEGER NOT NULL,
            duracion_minima TEXT NOT NULL, meses_minimos INTEGER NOT NULL DEFAULT 3,
            permite_mascotas INTEGER DEFAULT 0, permite_fumar INTEGER DEFAULT 0,
            descripcion TEXT
        );
        CREATE TABLE IF NOT EXISTS households (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL UNIQUE,
            duracion_preferida TEXT NOT NULL,
            perfil_buscado_edad_min INTEGER DEFAULT 18,
            perfil_buscado_edad_max INTEGER DEFAULT 99,
            perfil_buscado_ocupacion TEXT DEFAULT '',
            descripcion TEXT,
            FOREIGN KEY (listing_id) REFERENCES listings(id)
        );
        CREATE TABLE IF NOT EXISTS roommates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            edad INTEGER NOT NULL,
            ocupacion TEXT NOT NULL,
            estilo_convivencia TEXT NOT NULL,
            tolerancia_ruido TEXT NOT NULL,
            horario TEXT NOT NULL,
            genero TEXT DEFAULT 'no_especificar',
            preferencia_genero TEXT DEFAULT 'sin_preferencia',
            es_propietario INTEGER DEFAULT 0,
            descripcion TEXT,
            FOREIGN KEY (listing_id) REFERENCES listings(id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            rol TEXT NOT NULL, nombre TEXT NOT NULL,
            candidate_id INTEGER, listing_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, candidate_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            score_mean REAL, score_min REAL, score_weighted REAL,
            score_estilo REAL, score_ruido REAL, score_horario REAL,
            score_duracion REAL, score_edad REAL, score_ocupacion REAL,
            score_genero REAL, valor INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, listing_id)
        );
        CREATE TABLE IF NOT EXISTS ml_weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alpha_mean REAL DEFAULT 0.33,
            alpha_min REAL DEFAULT 0.33,
            alpha_weighted REAL DEFAULT 0.34,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sample_count INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0.0
        );
    """)
    conn.commit(); conn.close()

# ── AUTH ──
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def verify_password(p, h): return hash_password(p) == h

def create_user(email, password, rol, nombre):
    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO users (email,password_hash,rol,nombre) VALUES (?,?,?,?)",
                           (email, hash_password(password), rol, nombre))
        conn.commit(); return cur.lastrowid
    except sqlite3.IntegrityError: return None
    finally: conn.close()

def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close(); return _row_to_user(row) if row else None

def get_user(uid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close(); return _row_to_user(row) if row else None

def update_user_candidate(uid, cid):
    conn = get_connection()
    conn.execute("UPDATE users SET candidate_id=? WHERE id=?", (cid, uid))
    conn.commit(); conn.close()

def update_user_listing(uid, lid):
    conn = get_connection()
    conn.execute("UPDATE users SET listing_id=? WHERE id=?", (lid, uid))
    conn.commit(); conn.close()

def _row_to_user(r):
    return User(id=r["id"], email=r["email"], password_hash=r["password_hash"],
                rol=r["rol"], nombre=r["nombre"],
                candidate_id=r["candidate_id"], listing_id=r["listing_id"])

# ── FEEDBACK ──
def save_feedback(user_id, candidate_id, listing_id, scores, valor):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO feedback
            (user_id,candidate_id,listing_id,score_mean,score_min,score_weighted,
             score_estilo,score_ruido,score_horario,score_duracion,score_edad,
             score_ocupacion,score_genero,valor)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (user_id, candidate_id, listing_id,
              scores.get("mean",0), scores.get("min",0), scores.get("weighted",0),
              scores.get("estilo_convivencia",0), scores.get("tolerancia_ruido",0),
              scores.get("horario",0), scores.get("duracion",0),
              scores.get("edad",0), scores.get("ocupacion",0),
              scores.get("genero",0), valor))
        conn.commit()
    finally: conn.close()

def get_all_feedback():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM feedback").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_feedback_count():
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    conn.close(); return n

def get_ml_weights():
    conn = get_connection()
    row = conn.execute("SELECT * FROM ml_weights ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return {"alpha_mean": row["alpha_mean"], "alpha_min": row["alpha_min"],
                "alpha_weighted": row["alpha_weighted"],
                "sample_count": row["sample_count"], "accuracy": row["accuracy"]}
    return {"alpha_mean": 0.33, "alpha_min": 0.33, "alpha_weighted": 0.34,
            "sample_count": 0, "accuracy": 0.0}

def save_ml_weights(alpha_mean, alpha_min, alpha_weighted, sample_count, accuracy):
    conn = get_connection()
    conn.execute("""INSERT INTO ml_weights (alpha_mean,alpha_min,alpha_weighted,sample_count,accuracy)
                    VALUES (?,?,?,?,?)""",
                 (alpha_mean, alpha_min, alpha_weighted, sample_count, accuracy))
    conn.commit(); conn.close()

# ── CANDIDATES ──
def insert_candidate(c):
    conn = get_connection()
    d = c.to_dict()
    cur = conn.execute("""
        INSERT INTO candidates
        (nombre,edad,ocupacion,presupuesto_max,barrios_preferidos,meses_estancia,
         duracion_deseada,estilo_convivencia,tolerancia_ruido,horario,
         acepta_mascotas,fumador,genero,preferencia_genero,descripcion)
        VALUES (:nombre,:edad,:ocupacion,:presupuesto_max,:barrios_preferidos,:meses_estancia,
                :duracion_deseada,:estilo_convivencia,:tolerancia_ruido,:horario,
                :acepta_mascotas,:fumador,:genero,:preferencia_genero,:descripcion)
    """, d)
    conn.commit(); new_id = cur.lastrowid; conn.close(); return new_id

def get_all_candidates():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close(); return [_row_to_candidate(r) for r in rows]

def get_candidate(cid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    conn.close(); return _row_to_candidate(row) if row else None

def _row_to_candidate(r):
    return Candidate(
        id=r["id"], nombre=r["nombre"], edad=r["edad"],
        ocupacion=Ocupacion(r["ocupacion"]), presupuesto_max=r["presupuesto_max"],
        barrios_preferidos=r["barrios_preferidos"].split(","),
        meses_estancia=r["meses_estancia"], duracion_deseada=Duracion(r["duracion_deseada"]),
        estilo_convivencia=EstiloConvivencia(r["estilo_convivencia"]),
        tolerancia_ruido=ToleranciaRuido(r["tolerancia_ruido"]),
        horario=Horario(r["horario"]),
        acepta_mascotas=bool(r["acepta_mascotas"]), fumador=bool(r["fumador"]),
        genero=Genero(r["genero"] or "no_especificar"),
        preferencia_genero=PreferenciaGenero(r["preferencia_genero"] or "sin_preferencia"),
        descripcion=r["descripcion"],
    )

# ── LISTINGS ──
def insert_listing(l):
    conn = get_connection()
    d = l.to_dict()
    cur = conn.execute("""
        INSERT INTO listings
        (titulo,barrio,precio_mes,plazas_totales,plazas_disponibles,
         duracion_minima,meses_minimos,permite_mascotas,permite_fumar,descripcion)
        VALUES (:titulo,:barrio,:precio_mes,:plazas_totales,:plazas_disponibles,
                :duracion_minima,:meses_minimos,:permite_mascotas,:permite_fumar,:descripcion)
    """, d)
    conn.commit(); new_id = cur.lastrowid; conn.close(); return new_id

def get_all_listings():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM listings").fetchall()
    conn.close(); return [_row_to_listing(r) for r in rows]

def get_listing(lid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM listings WHERE id=?", (lid,)).fetchone()
    conn.close(); return _row_to_listing(row) if row else None

def _row_to_listing(r):
    return Listing(
        id=r["id"], titulo=r["titulo"], barrio=r["barrio"],
        precio_mes=r["precio_mes"], plazas_totales=r["plazas_totales"],
        plazas_disponibles=r["plazas_disponibles"],
        duracion_minima=Duracion(r["duracion_minima"]), meses_minimos=r["meses_minimos"],
        permite_mascotas=bool(r["permite_mascotas"]), permite_fumar=bool(r["permite_fumar"]),
        descripcion=r["descripcion"],
    )

# ── HOUSEHOLDS ──
def insert_household(h):
    conn = get_connection()
    d = h.to_dict()
    cur = conn.execute("""
        INSERT INTO households
        (listing_id,duracion_preferida,perfil_buscado_edad_min,
         perfil_buscado_edad_max,perfil_buscado_ocupacion,descripcion)
        VALUES (:listing_id,:duracion_preferida,:perfil_buscado_edad_min,
                :perfil_buscado_edad_max,:perfil_buscado_ocupacion,:descripcion)
    """, d)
    conn.commit(); new_id = cur.lastrowid; conn.close(); return new_id

def get_all_households():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM households").fetchall()
    conn.close(); return [_row_to_household(r) for r in rows]

def get_household_by_listing(lid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM households WHERE listing_id=?", (lid,)).fetchone()
    conn.close(); return _row_to_household(row) if row else None

def _row_to_household(r):
    ocu = r["perfil_buscado_ocupacion"]
    return Household(
        id=r["id"], listing_id=r["listing_id"],
        duracion_preferida=Duracion(r["duracion_preferida"]),
        perfil_buscado_edad_min=r["perfil_buscado_edad_min"],
        perfil_buscado_edad_max=r["perfil_buscado_edad_max"],
        perfil_buscado_ocupacion=Ocupacion(ocu) if ocu else None,
        descripcion=r["descripcion"],
    )

# ── ROOMMATES ──
def insert_roommate(rm):
    conn = get_connection()
    d = rm.to_dict()
    cur = conn.execute("""
        INSERT INTO roommates
        (listing_id,nombre,edad,ocupacion,estilo_convivencia,tolerancia_ruido,
         horario,genero,preferencia_genero,es_propietario,descripcion)
        VALUES (:listing_id,:nombre,:edad,:ocupacion,:estilo_convivencia,:tolerancia_ruido,
                :horario,:genero,:preferencia_genero,:es_propietario,:descripcion)
    """, d)
    conn.commit(); new_id = cur.lastrowid; conn.close(); return new_id

def get_roommates_by_listing(lid):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM roommates WHERE listing_id=?", (lid,)).fetchall()
    conn.close(); return [_row_to_roommate(r) for r in rows]

def get_all_roommates():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM roommates").fetchall()
    conn.close(); return [_row_to_roommate(r) for r in rows]

def _row_to_roommate(r):
    return Roommate(
        id=r["id"], listing_id=r["listing_id"],
        nombre=r["nombre"], edad=r["edad"],
        ocupacion=Ocupacion(r["ocupacion"]),
        estilo_convivencia=EstiloConvivencia(r["estilo_convivencia"]),
        tolerancia_ruido=ToleranciaRuido(r["tolerancia_ruido"]),
        horario=Horario(r["horario"]),
        genero=Genero(r["genero"] or "no_especificar"),
        preferencia_genero=PreferenciaGenero(r["preferencia_genero"] or "sin_preferencia"),
        es_propietario=bool(r["es_propietario"]),
        descripcion=r["descripcion"],
    )
