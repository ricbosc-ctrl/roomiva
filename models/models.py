"""Modelos de datos v3 — sin tipo habitación, con preferencia género."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class Ocupacion(str, Enum):
    ESTUDIANTE = "estudiante"
    TRABAJADOR = "trabajador"
    FREELANCE = "freelance"
    OTRO = "otro"

class EstiloConvivencia(str, Enum):
    TRANQUILO = "tranquilo"
    SOCIAL = "social"
    MIXTO = "mixto"

class ToleranciaRuido(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"

class Duracion(str, Enum):
    CORTA = "corta"   # 3–6 meses
    MEDIA = "media"   # 7–12 meses
    LARGA = "larga"   # 13+ meses

class Horario(str, Enum):
    DIURNO = "diurno"
    NOCTURNO = "nocturno"
    FLEXIBLE = "flexible"

class Genero(str, Enum):
    HOMBRE = "hombre"
    MUJER = "mujer"
    NO_ESPECIFICAR = "no_especificar"

class PreferenciaGenero(str, Enum):
    MIXTO = "mixto"
    MISMO_GENERO = "mismo_genero"
    SIN_PREFERENCIA = "sin_preferencia"

def meses_a_duracion(meses: int) -> "Duracion":
    if meses < 3:
        raise ValueError("La duración mínima es 3 meses")
    elif meses <= 6:
        return Duracion.CORTA
    elif meses <= 12:
        return Duracion.MEDIA
    else:
        return Duracion.LARGA

BARRIOS_BARCELONA = [
    "Eixample", "Gràcia", "Sant Martí", "Sants-Montjuïc", "Sarrià-Sant Gervasi",
    "Horta-Guinardó", "Nou Barris", "Sant Andreu", "Ciutat Vella", "Les Corts",
    "Poblenou", "Barceloneta", "El Born", "Sagrada Família", "Esquerra de l'Eixample",
    "Dreta de l'Eixample", "Vila de Gràcia", "Camp de l'Arpa", "Clot", "Sant Pere"
]


@dataclass
class Candidate:
    id: int
    nombre: str
    edad: int
    ocupacion: Ocupacion
    presupuesto_max: float
    barrios_preferidos: List[str]
    meses_estancia: int
    duracion_deseada: Duracion
    estilo_convivencia: EstiloConvivencia
    tolerancia_ruido: ToleranciaRuido
    horario: Horario
    acepta_mascotas: bool
    fumador: bool
    genero: "Genero" = None
    preferencia_genero: PreferenciaGenero = PreferenciaGenero.SIN_PREFERENCIA
    descripcion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "nombre": self.nombre, "edad": self.edad,
            "ocupacion": self.ocupacion.value, "presupuesto_max": self.presupuesto_max,
            "barrios_preferidos": ",".join(self.barrios_preferidos),
            "meses_estancia": self.meses_estancia, "duracion_deseada": self.duracion_deseada.value,
            "estilo_convivencia": self.estilo_convivencia.value,
            "tolerancia_ruido": self.tolerancia_ruido.value, "horario": self.horario.value,
            "acepta_mascotas": int(self.acepta_mascotas), "fumador": int(self.fumador),
            "genero": self.genero.value if self.genero else "no_especificar",
            "preferencia_genero": self.preferencia_genero.value,
            "descripcion": self.descripcion or "",
        }


@dataclass
class Listing:
    id: int
    titulo: str
    barrio: str
    precio_mes: float
    plazas_totales: int
    plazas_disponibles: int
    duracion_minima: Duracion
    meses_minimos: int
    permite_mascotas: bool
    permite_fumar: bool
    descripcion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "titulo": self.titulo, "barrio": self.barrio,
            "precio_mes": self.precio_mes, "plazas_totales": self.plazas_totales,
            "plazas_disponibles": self.plazas_disponibles,
            "duracion_minima": self.duracion_minima.value, "meses_minimos": self.meses_minimos,
            "permite_mascotas": int(self.permite_mascotas), "permite_fumar": int(self.permite_fumar),
            "descripcion": self.descripcion or "",
        }


@dataclass
class Household:
    id: int
    listing_id: int
    estilo_convivencia: EstiloConvivencia
    tolerancia_ruido: ToleranciaRuido
    horario_predominante: Horario
    perfil_buscado_ocupacion: Optional[Ocupacion]
    perfil_buscado_edad_min: Optional[int]
    perfil_buscado_edad_max: Optional[int]
    duracion_preferida: Duracion
    num_convivientes_actuales: int
    preferencia_genero: PreferenciaGenero = PreferenciaGenero.SIN_PREFERENCIA
    descripcion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "listing_id": self.listing_id,
            "estilo_convivencia": self.estilo_convivencia.value,
            "tolerancia_ruido": self.tolerancia_ruido.value,
            "horario_predominante": self.horario_predominante.value,
            "perfil_buscado_ocupacion": self.perfil_buscado_ocupacion.value if self.perfil_buscado_ocupacion else "",
            "perfil_buscado_edad_min": self.perfil_buscado_edad_min or 0,
            "perfil_buscado_edad_max": self.perfil_buscado_edad_max or 99,
            "duracion_preferida": self.duracion_preferida.value,
            "num_convivientes_actuales": self.num_convivientes_actuales,
            "preferencia_genero": self.preferencia_genero.value,
            "descripcion": self.descripcion or "",
        }


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    rol: str
    nombre: str
    candidate_id: Optional[int] = None
    listing_id: Optional[int] = None


@dataclass
class RecommendationResult:
    target_id: int
    target_nombre: str
    score_total: float
    score_detalle: dict
    razones: List[str]
    advertencias: List[str]
    hard_constraints_ok: bool
    listing_info: Optional[dict] = None

    @property
    def score_pct(self) -> int:
        return round(self.score_total * 100)
