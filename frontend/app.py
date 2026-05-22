"""
Prototipo web demostrador con Streamlit.
Muestra las dos direcciones del sistema de recomendación:
  1. Candidato busca pisos compatibles
  2. Hogar busca candidatos compatibles
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from models.models import (
    Candidate, Listing, Household,
    Ocupacion, EstiloConvivencia, ToleranciaRuido, Duracion, Horario,
    BARRIOS_BARCELONA
)
from database.db import (
    init_db,
    get_all_candidates, get_candidate,
    get_all_listings, get_listing,
    get_all_households, get_household, get_household_by_listing,
    insert_candidate
)
from engine.recommender import recommend_listings_for_candidate, recommend_candidates_for_household

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="CoLiving Recommender",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    .score-high   { background:#d4edda; border-left:4px solid #28a745; padding:8px 12px; border-radius:4px; margin:4px 0; }
    .score-mid    { background:#fff3cd; border-left:4px solid #ffc107; padding:8px 12px; border-radius:4px; margin:4px 0; }
    .score-low    { background:#f8d7da; border-left:4px solid #dc3545; padding:8px 12px; border-radius:4px; margin:4px 0; }
    .reason-tag   { background:#e8f5e9; color:#2e7d32; padding:3px 8px; border-radius:12px; font-size:0.85em; margin:2px; display:inline-block; }
    .warn-tag     { background:#fff8e1; color:#f57f17; padding:3px 8px; border-radius:12px; font-size:0.85em; margin:2px; display:inline-block; }
    .metric-box   { background:#f0f2f6; padding:12px; border-radius:8px; text-align:center; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

st.sidebar.title("🏠 CoLiving Recommender")
st.sidebar.markdown("**Sistema de recomendación multi-criterio**  \n*TFG – Ricard Bosch*")
st.sidebar.divider()

modo = st.sidebar.radio(
    "Selecciona modo",
    ["🔍 Candidato busca piso", "🏡 Hogar busca candidato", "📊 Explorar datos", "➕ Nuevo candidato"]
)

# ─────────────────────────────────────────────
# HELPER: render result card
# ─────────────────────────────────────────────

def render_result_card(r, rank: int, extra_info: str = ""):
    color_class = "score-high" if r.score_pct >= 70 else ("score-mid" if r.score_pct >= 45 else "score-low")
    emoji = "🟢" if r.score_pct >= 70 else ("🟡" if r.score_pct >= 45 else "🔴")

    with st.expander(f"{emoji} #{rank}  {r.target_nombre}  —  **{r.score_pct}% compatibilidad**", expanded=(rank <= 3)):
        col1, col2 = st.columns([2, 1])

        with col1:
            if extra_info:
                st.caption(extra_info)

            st.markdown("**✅ Puntos a favor:**")
            for rz in r.razones:
                st.markdown(f'<span class="reason-tag">✓ {rz}</span>', unsafe_allow_html=True)

            if r.advertencias:
                st.markdown("**⚠️ Puntos de atención:**")
                for av in r.advertencias:
                    st.markdown(f'<span class="warn-tag">⚠ {av}</span>', unsafe_allow_html=True)

        with col2:
            st.markdown("**Detalle por criterio:**")
            if r.score_detalle:
                labels = {
                    "estilo_convivencia": "Estilo conv.",
                    "tolerancia_ruido": "Ruido",
                    "horario": "Horario",
                    "duracion": "Duración",
                    "edad": "Edad",
                    "ocupacion": "Ocupación",
                }
                for k, v in r.score_detalle.items():
                    pct = int(v * 100)
                    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
                    st.caption(f"{labels.get(k, k)}: {bar} {pct}%")


# ─────────────────────────────────────────────
# MODO 1: CANDIDATO BUSCA PISO
# ─────────────────────────────────────────────

if modo == "🔍 Candidato busca piso":
    st.title("🔍 Pisos recomendados para un candidato")
    st.markdown("Selecciona un candidato del dataset para ver qué pisos le son más compatibles.")

    candidates = get_all_candidates()
    if not candidates:
        st.warning("No hay candidatos en la base de datos. Ejecuta el seed primero.")
        st.stop()

    cand_options = {f"[{c.id}] {c.nombre} ({c.edad}a, {c.ocupacion.value})": c.id for c in candidates}
    selected_label = st.selectbox("Candidato", list(cand_options.keys()))
    candidate = get_candidate(cand_options[selected_label])

    top_n = st.slider("Número de recomendaciones", 3, 15, 8)

    if candidate:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Presupuesto máx.", f"{candidate.presupuesto_max}€/mes")
        col2.metric("Duración deseada", candidate.duracion_deseada.value)
        col3.metric("Estilo convivencia", candidate.estilo_convivencia.value)
        col4.metric("Barrios preferidos", len(candidate.barrios_preferidos))

        st.caption(f"Barrios: {', '.join(candidate.barrios_preferidos)}")
        st.divider()

        if st.button("🚀 Obtener recomendaciones", type="primary"):
            listings = get_all_listings()
            households = get_all_households()

            with st.spinner("Calculando compatibilidad..."):
                results = recommend_listings_for_candidate(candidate, listings, households, top_n)

            if not results:
                st.warning("No se encontraron pisos que cumplan los filtros obligatorios.")
            else:
                st.success(f"Se encontraron **{len(results)} pisos compatibles** (de {len(listings)} disponibles)")

                for i, r in enumerate(results, 1):
                    listing = get_listing(r.target_id)
                    extra = f"📍 {listing.barrio} · {listing.precio_mes}€/mes · {listing.plazas_disponibles} plaza(s) libre(s)" if listing else ""
                    render_result_card(r, i, extra)


# ─────────────────────────────────────────────
# MODO 2: HOGAR BUSCA CANDIDATO
# ─────────────────────────────────────────────

elif modo == "🏡 Hogar busca candidato":
    st.title("🏡 Candidatos recomendados para un hogar")
    st.markdown("Selecciona un piso/hogar para ver qué candidatos encajan mejor.")

    listings = get_all_listings()
    households = get_all_households()

    listings_with_hh = [l for l in listings if get_household_by_listing(l.id) is not None]

    if not listings_with_hh:
        st.warning("No hay hogares definidos. Ejecuta el seed primero.")
        st.stop()

    listing_options = {f"[{l.id}] {l.titulo} – {l.barrio} ({l.precio_mes}€)": l.id for l in listings_with_hh}
    selected_label = st.selectbox("Piso / Hogar", list(listing_options.keys()))
    listing = get_listing(listing_options[selected_label])
    household = get_household_by_listing(listing.id) if listing else None

    top_n = st.slider("Número de recomendaciones", 3, 15, 8)

    if listing and household:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Precio", f"{listing.precio_mes}€/mes")
        col2.metric("Estilo hogar", household.estilo_convivencia.value)
        col3.metric("Convivientes actuales", household.num_convivientes_actuales)
        col4.metric("Rango edad buscado", f"{household.perfil_buscado_edad_min}–{household.perfil_buscado_edad_max}a")

        if household.perfil_buscado_ocupacion:
            st.caption(f"Ocupación preferida: {household.perfil_buscado_ocupacion.value}")
        st.divider()

        if st.button("🚀 Buscar candidatos compatibles", type="primary"):
            candidates = get_all_candidates()

            with st.spinner("Calculando compatibilidad..."):
                results = recommend_candidates_for_household(household, listing, candidates, top_n)

            if not results:
                st.warning("No hay candidatos que cumplan los requisitos del hogar.")
            else:
                st.success(f"Se encontraron **{len(results)} candidatos compatibles** (de {len(candidates)} en el sistema)")

                for i, r in enumerate(results, 1):
                    candidate = get_candidate(r.target_id)
                    extra = f"👤 {candidate.edad}a · {candidate.ocupacion.value} · {candidate.presupuesto_max}€ presup." if candidate else ""
                    render_result_card(r, i, extra)


# ─────────────────────────────────────────────
# MODO 3: EXPLORAR DATOS
# ─────────────────────────────────────────────

elif modo == "📊 Explorar datos":
    st.title("📊 Explorador del dataset")

    tab1, tab2, tab3 = st.tabs(["Candidatos", "Pisos", "Hogares"])

    with tab1:
        candidates = get_all_candidates()
        if candidates:
            df = pd.DataFrame([c.to_dict() for c in candidates])
            df["barrios_preferidos"] = df["barrios_preferidos"].str.replace(",", ", ")
            st.dataframe(df[["id","nombre","edad","ocupacion","presupuesto_max","duracion_deseada","estilo_convivencia"]], use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                ocupacion_counts = df["ocupacion"].value_counts()
                st.bar_chart(ocupacion_counts)
                st.caption("Distribución por ocupación")
            with col2:
                estilo_counts = df["estilo_convivencia"].value_counts()
                st.bar_chart(estilo_counts)
                st.caption("Distribución por estilo de convivencia")

    with tab2:
        listings = get_all_listings()
        if listings:
            df = pd.DataFrame([l.to_dict() for l in listings])
            st.dataframe(df[["id","titulo","barrio","precio_mes","plazas_disponibles","duracion_minima"]], use_container_width=True)

            st.bar_chart(df.set_index("barrio")["precio_mes"])
            st.caption("Precio medio por barrio")

    with tab3:
        households = get_all_households()
        if households:
            df = pd.DataFrame([h.to_dict() for h in households])
            st.dataframe(df[["id","listing_id","estilo_convivencia","tolerancia_ruido","duracion_preferida","num_convivientes_actuales"]], use_container_width=True)


# ─────────────────────────────────────────────
# MODO 4: NUEVO CANDIDATO
# ─────────────────────────────────────────────

elif modo == "➕ Nuevo candidato":
    st.title("➕ Crear nuevo candidato")
    st.markdown("Introduce un perfil nuevo y obtén recomendaciones en tiempo real.")

    with st.form("nuevo_candidato"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre", placeholder="Tu nombre")
            edad = st.number_input("Edad", 18, 80, 25)
            ocupacion = st.selectbox("Ocupación", [o.value for o in Ocupacion])
            presupuesto = st.number_input("Presupuesto máximo (€/mes)", 300, 2000, 600, step=50)
        with col2:
            barrios = st.multiselect("Barrios preferidos", BARRIOS_BARCELONA, default=["Gràcia", "Eixample"])
            duracion = st.selectbox("Duración deseada", [d.value for d in Duracion])
            estilo = st.selectbox("Estilo de convivencia", [e.value for e in EstiloConvivencia])
            ruido = st.selectbox("Tolerancia al ruido", [r.value for r in ToleranciaRuido])

        col3, col4 = st.columns(2)
        with col3:
            horario = st.selectbox("Horario", [h.value for h in Horario])
        with col4:
            mascotas = st.checkbox("Acepta mascotas")
            fumador = st.checkbox("Fumador/a")

        submitted = st.form_submit_button("🔍 Buscar recomendaciones", type="primary")

    if submitted and nombre and barrios:
        candidate = Candidate(
            id=0, nombre=nombre, edad=edad,
            ocupacion=Ocupacion(ocupacion),
            presupuesto_max=presupuesto,
            barrios_preferidos=barrios,
            duracion_deseada=Duracion(duracion),
            estilo_convivencia=EstiloConvivencia(estilo),
            tolerancia_ruido=ToleranciaRuido(ruido),
            horario=Horario(horario),
            acepta_mascotas=mascotas,
            fumador=fumador,
        )

        listings = get_all_listings()
        households = get_all_households()

        with st.spinner("Calculando compatibilidad..."):
            results = recommend_listings_for_candidate(candidate, listings, households, top_n=8)

        st.divider()
        if not results:
            st.warning("No se encontraron pisos que cumplan tus criterios. Prueba ampliando barrios o presupuesto.")
        else:
            st.success(f"**{len(results)} pisos compatibles** encontrados para ti")
            for i, r in enumerate(results, 1):
                listing = get_listing(r.target_id)
                extra = f"📍 {listing.barrio} · {listing.precio_mes}€/mes" if listing else ""
                render_result_card(r, i, extra)
    elif submitted:
        st.error("Por favor, introduce nombre y selecciona al menos un barrio.")
