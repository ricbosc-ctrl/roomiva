"""Dataset sintético v4 — hogares con convivientes individuales."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.models import (Candidate, Listing, Household, Roommate,
    Ocupacion, EstiloConvivencia, ToleranciaRuido, Duracion, Horario,
    Genero, PreferenciaGenero, meses_a_duracion)
from database.db import (init_db, insert_candidate, insert_listing,
    insert_household, insert_roommate, get_connection)

LISTINGS_RAW = [
    ("Habitación asequible en Nou Barris",       "Nou Barris",               300, 4, 2, 3,  False, False, "Piso amplio y funcional. Buenas conexiones de metro. Ambiente estudiantil."),
    ("Hab. tranquila en Horta-Guinardó",         "Horta-Guinardó",           310, 5, 3, 3,  False, True,  "Zona residencial tranquila. Cocina equipada, wifi incluido."),
    ("Hab. en piso familiar Sant Andreu",        "Sant Andreu",              320, 4, 2, 6,  True,  False, "Piso amplio con terraza. Mascotas bienvenidas. Barrio tranquilo."),
    ("Hab. económica en Sants",                  "Sants-Montjuïc",           330, 4, 2, 4,  False, False, "Muy bien comunicado con Sants Estació. Piso luminoso."),
    ("Hab. piso estudiantes Clot",               "Clot",                     340, 5, 3, 4,  False, False, "Piso joven y social. Cerca de universidad y transporte."),
    ("Hab. en Nou Barris reformada",             "Nou Barris",               360, 3, 1, 6,  False, False, "Piso reformado. Ascensor. Compañeros trabajadores tranquilos."),
    ("Hab. con jardín en Horta",                 "Horta-Guinardó",           370, 4, 2, 6,  True,  False, "Jardín compartido. Barrio silencioso. Mascotas permitidas."),
    ("Hab. en Sant Andreu norte",                "Sant Andreu",              380, 4, 1, 6,  False, False, "Zona tranquila con parques. Compañeros respetuosos."),
    ("Hab. social en Vila de Gràcia",            "Vila de Gràcia",           410, 4, 2, 6,  False, False, "Piso muy social en Gràcia. Ambiente festivo y abierto."),
    ("Hab. luminosa en Camp de l'Arpa",          "Camp de l'Arpa",           420, 3, 1, 6,  False, False, "Piso moderno. Buena comunidad de jóvenes profesionales."),
    ("Hab. tranquila Sagrada Família",           "Sagrada Família",          430, 3, 1, 9,  False, False, "Piso silencioso, compañeros respetuosos. Cerca universidades."),
    ("Hab. en Sant Pere céntrico",               "Sant Pere",                440, 4, 2, 6,  False, True,  "Zona histórica. Ambiente mixto joven. Fumadores en terraza."),
    ("Hab. profesional en Sants",                "Sants-Montjuïc",           450, 3, 1, 12, False, False, "Compañeros trabajadores. Piso muy organizado."),
    ("Hab. con encanto en El Born",              "El Born",                  460, 3, 1, 6,  False, False, "Techos altos. Compañeros creativos y abiertos."),
    ("Hab. en Poblenou tecnológico",             "Poblenou",                 470, 4, 2, 9,  False, False, "Zona 22@. Ideal para sector tech. Ambiente dinámico."),
    ("Hab. con terraza en Clot",                 "Clot",                     490, 3, 1, 9,  False, False, "Acceso a terraza privada. Compañeros jóvenes trabajadores."),
    ("Hab. en Esquerra de l'Eixample",           "Esquerra de l'Eixample",   500, 4, 2, 9,  False, False, "Eixample izquierdo animado. Cerca bares y transporte."),
    ("Hab. tranquila en Sant Martí",             "Sant Martí",               510, 3, 1, 12, False, False, "Barrio tranquilo. Compañeros profesionales organizados."),
    ("Hab. cerca del mar Barceloneta",           "Barceloneta",              520, 3, 1, 3,  False, True,  "Cerca del mar. Ambiente veraniego. Estancias cortas."),
    ("Hab. en Gràcia con carácter",              "Gràcia",                   530, 3, 1, 6,  False, False, "Piso acogedor. Comunidad mixta y abierta."),
    ("Hab. moderna en Vila de Gràcia",           "Vila de Gràcia",           540, 3, 1, 9,  False, False, "Zona muy buscada. Piso tranquilo con buena convivencia."),
    ("Hab. premium El Born",                     "El Born",                  560, 3, 1, 9,  False, False, "Techos originales, suelos de madera. Ambiente cultural."),
    ("Hab. en Eixample derecho",                 "Dreta de l'Eixample",      580, 4, 2, 12, False, False, "Piso señorial reformado. Compañeros profesionales."),
    ("Hab. con balcón en Poblenou",              "Poblenou",                 600, 3, 1, 9,  False, False, "Balcón propio. Zona tech. Compañeros del sector digital."),
    ("Hab. reformada en Sant Martí",             "Sant Martí",               610, 3, 1, 12, False, False, "Reformado 2023. Compañeros profesionales estables."),
    ("Hab. exclusiva Barceloneta",               "Barceloneta",              620, 2, 1, 6,  False, False, "A 2 minutos de la playa. Piso para 2 personas, muy cuidado."),
    ("Hab. en Esquerra Eixample premium",        "Esquerra de l'Eixample",   640, 3, 1, 12, False, False, "Gayxample. Comunidad tolerante. Muy bien equipado."),
    ("Hab. con mascotas en Gràcia",              "Gràcia",                   650, 3, 1, 9,  True,  False, "Mascotas bienvenidas. Piso cálido y acogedor."),
    ("Hab. en Sagrada Família premium",          "Sagrada Família",          660, 3, 1, 12, False, False, "Piso luminoso junto a la Sagrada Família. Muy tranquilo."),
    ("Hab. en Poblenou junto al mar",            "Poblenou",                 680, 3, 1, 12, False, False, "A 5 minutos de la playa. Terraza compartida. Luminoso."),
    ("Hab. premium en Eixample",                 "Eixample",                 700, 3, 1, 12, False, False, "Piso señorial. Techos altos, suelos hidráulicos."),
    ("Hab. en Les Corts zona universitaria",     "Les Corts",                720, 3, 1, 12, False, False, "Cerca UB y hospitales. Ideal médicos o investigadores."),
    ("Hab. luminosa en Sarrià",                  "Sarrià-Sant Gervasi",      750, 3, 1, 18, False, False, "Barrio residencial tranquilo. Jardín privado."),
    ("Hab. premium Les Corts",                   "Les Corts",                780, 2, 1, 18, False, False, "Máxima privacidad. Zona premium tranquila."),
    ("Piso exclusivo en Sarrià",                 "Sarrià-Sant Gervasi",      820, 2, 1, 24, True,  False, "Jardín privado. Máxima tranquilidad. Solo adultos."),
    ("Hab. en Dreta Eixample exclusiva",         "Dreta de l'Eixample",      840, 3, 1, 18, False, False, "Piso modernista reformado. Perfil profesional alto."),
    ("Hab. en Les Corts con piscina",            "Les Corts",                860, 4, 2, 12, False, False, "Edificio con piscina comunitaria. Cerca del Camp Nou."),
    ("Piso de lujo en Sarrià-Sant Gervasi",      "Sarrià-Sant Gervasi",      900, 2, 1, 24, True,  False, "Zona alta de Barcelona. Jardín, garaje. Perfil ejecutivo."),
    ("Hab. premium Eixample con terraza",        "Eixample",                 920, 3, 1, 18, False, False, "Terraza privada en el Eixample. Alto standing."),
    ("Hab. en Sarrià top",                       "Sarrià-Sant Gervasi",      950, 2, 1, 24, True,  False, "Jardín, terraza, zona exclusiva. Todo incluido."),
]

# Convivientes por listing (1-3 por piso)
# (nombre, edad, ocupacion, estilo, ruido, horario, genero, pref_genero, es_propietario, desc)
ROOMMATES_BY_LISTING = {
    0:  [("Arnau", 22, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Estudiante de ingeniería, me gusta el ambiente social pero respeto las normas."),
         ("Irina", 21, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Erasmus rusa, busco gente con quien salir y conocer la ciudad.")],
    1:  [("Carles", 34, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Técnico de laboratorio, horarios fijos. Busco ambiente tranquilo.")],
    2:  [("Mònica", 38, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Enfermera. Tengo dos gatos. Busco persona tranquila y amante de los animales."),
         ("Bernat", 40, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Arquitecto freelance. Trabajo desde casa algunos días.")],
    3:  [("Júlia", 26, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Trabajo en marketing digital. Horarios variables. Soy ordenada y limpia."),
         ("Tomàs", 27, Ocupacion.FREELANCE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Diseñador gráfico. Trabajo desde casa. Tranquilo pero me gusta socializar.")],
    4:  [("Laia", 20, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.MUJER, PreferenciaGenero.MISMO_GENERO, True, "Estudiante de Bellas Artes. Me encanta el ambiente estudiantil y hacer planes."),
         ("Sara", 21, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.MUJER, PreferenciaGenero.MISMO_GENERO, False, "Estudiante de psicología. Sociable y positiva."),
         ("Ona", 22, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Estudiante de máster. Un poco más tranquila que mis compañeras pero me adapto.")],
    5:  [("Gerard", 31, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Ingeniero civil. Trabajo exigente, en casa necesito tranquilidad.")],
    6:  [("Núria", 29, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Veterinaria. Tengo un perro. Busco persona que ame los animales."),
         ("David", 32, Ocupacion.FREELANCE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Fotógrafo freelance. Viajo mucho, cuando estoy en casa me gusta la tranquilidad.")],
    7:  [("Ferran", 35, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Profesor universitario. Busco ambiente serio y respetuoso.")],
    8:  [("Marta", 23, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.MUJER, PreferenciaGenero.MIXTO, True, "Estudiante Erasmus italiana. Busco gente para conocer Barcelona."),
         ("Pau", 24, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.MIXTO, False, "Estudiante de ADE. Me gusta el balance entre vida social y estudios.")],
    9:  [("Elena", 27, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Trabaja en recursos humanos. Organizada y comunicativa."),
         ("Marc", 28, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Contable. Rutinas muy fijas. Muy ordenado y tranquilo.")],
    10: [("Irene", 30, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Abogada. Trabajo duro entre semana, necesito silencio en casa.")],
    11: [("Guillem", 25, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Estudiante de música. Me gusta el ambiente bohemio del Born."),
         ("Claudia", 24, Ocupacion.FREELANCE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Escritora freelance. Trabajo en cafeterías, en casa soy tranquila.")],
    12: [("Roger", 33, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Técnico informático. Piso muy organizado, buscamos profesional serio.")],
    13: [("Anna", 28, Ocupacion.FREELANCE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Ilustradora. El Born es mi barrio ideal, llevo 3 años aquí."),
         ("Jordi", 30, Ocupacion.TRABAJADOR, EstiloConvivencia.SOCIAL, ToleranciaRuido.MEDIA, Horario.NOCTURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Trabaja en hostelería, llega tarde. Le gusta el ambiente animado.")],
    14: [("Xavier", 29, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Desarrollador de software. Trabajo en una startup del 22@."),
         ("Celia", 27, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Data scientist. También del sector tech. Horarios algo variables.")],
    15: [("Ricard", 32, Ocupacion.FREELANCE, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Diseñador UX freelance. Trabajo desde casa, necesito tranquilidad.")],
    16: [("Meritxell", 26, Ocupacion.TRABAJADOR, EstiloConvivencia.SOCIAL, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.MIXTO, True, "Trabaja en agencia de publicidad. Sociable, le gusta quedar con los compañeros."),
         ("Abel", 25, Ocupacion.ESTUDIANTE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.NOCTURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Estudiante de posgrado. Entre estudios y salidas de vez en cuando.")],
    17: [("Patricia", 36, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Directora de proyectos. Busco compañero serio para larga estancia.")],
    18: [("Bruno", 22, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Estudiante de Turismo. Me encanta la Barceloneta y el ambiente playero."),
         ("Valentina", 23, Ocupacion.ESTUDIANTE, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Estudiante italiana. Aquí de intercambio, busco vivir la experiencia al máximo.")],
    19: [("Àlex", 27, Ocupacion.FREELANCE, EstiloConvivencia.SOCIAL, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.MIXTO, True, "Músico y productor. Gràcia es mi barrio, llevo años aquí."),
         ("Neus", 26, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Trabaja en una galería de arte. Tranquila pero disfruta del ambiente de Gràcia.")],
    20: [("Vicenç", 31, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Trabaja en banca. Ordenado y comunicativo.")],
    21: [("Júlia", 29, Ocupacion.FREELANCE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Traductora literaria. El Born es mi inspiración diaria."),
         ("Oriol", 31, Ocupacion.TRABAJADOR, EstiloConvivencia.SOCIAL, ToleranciaRuido.ALTA, Horario.NOCTURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Trabaja en un restaurante hasta tarde. Le encanta el ambiente del Born.")],
    22: [("Cristina", 37, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Médica especialista. Vivo en el Eixample desde hace 5 años."),
         ("Enric", 39, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Farmacéutico. Horarios regulares, vida tranquila.")],
    23: [("Nil", 28, Ocupacion.FREELANCE, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Full-stack developer. Trabajo desde casa, busco ambiente tech."),
         ("Clàudia", 26, Ocupacion.TRABAJADOR, EstiloConvivencia.MIXTO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Product manager en startup. También del mundo digital.")],
    24: [("Miquel", 34, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Ingeniero industrial. Ordenado, tranquilo, busco lo mismo.")],
    25: [("Rosa", 41, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Profesora de secundaria. Piso solo para 2, busco persona madura.")],
    26: [("Héctor", 33, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Consultor de empresa. Viajo mucho, cuando estoy busco tranquilidad."),
         ("Montse", 31, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Trabaja en RRHH. Muy organizada, le gusta el orden en casa.")],
    27: [("Sílvia", 30, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Veterinaria. Tengo un gato. Solo personas que amen los animales.")],
    28: [("Ignasi", 42, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Arquitecto senior. Busco ambiente serio y tranquilo para larga estancia."),
         ("Carme", 38, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Trabaja en administración pública. Rutinas fijas, muy ordenada.")],
    29: [("Llorenç", 35, Ocupacion.FREELANCE, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.FLEXIBLE, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Consultor autónomo. Vivo cerca del mar hace 3 años, no lo cambiaría.")],
    30: [("Elisenda", 44, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Directora de departamento. Busco perfil profesional para el piso del Eixample."),
         ("Andreu", 41, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Notario. Vida muy ordenada y tranquila.")],
    31: [("Assumpta", 46, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Médica adjunta en el Hospital Clínic. Busco compañero del sector salud o similar.")],
    32: [("Francesc", 50, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Empresario. Jardín privado. Solo adultos maduros y tranquilos.")],
    33: [("Mercè", 48, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Gerente de empresa. Solo para 2 personas. Perfil muy seleccionado.")],
    34: [("Josep", 55, Ocupacion.OTRO, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Jubilado. Zona alta exclusiva. Busco persona muy tranquila y respetuosa.")],
    35: [("Victòria", 45, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Ejecutiva de banca. Eixample modernista. Perfil muy profesional."),
         ("Lluís", 47, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Abogado. Rutinas muy fijas. Silencio absoluto en casa.")],
    36: [("Gemma", 38, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Fisioterapeuta. Piscina en el edificio. Zona muy familiar."),
         ("Albert", 40, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, False, "Ingeniero agrónomo. Muy tranquilo y ordenado.")],
    37: [("Pilar", 52, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, True, "Directora general. El piso más premium. Solo perfil muy senior.")],
    38: [("Sergi", 40, Ocupacion.TRABAJADOR, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Director creativo. Terraza privada en el Eixample. Solo larga estancia."),
         ("Noemí", 37, Ocupacion.FREELANCE, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.FLEXIBLE, Genero.MUJER, PreferenciaGenero.SIN_PREFERENCIA, False, "Arquitecta freelance. Trabaja desde casa algunos días, silencio necesario.")],
    39: [("Joaquim", 58, Ocupacion.OTRO, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA, Horario.DIURNO, Genero.HOMBRE, PreferenciaGenero.SIN_PREFERENCIA, True, "Inversor. El mejor piso del dataset. Solo adultos de perfil muy alto.")],
}

HOUSEHOLDS_RAW = [
    (0,  Duracion.CORTA,  18, 28, Ocupacion.ESTUDIANTE, "Piso universitario. Buscamos estudiante o joven trabajador."),
    (1,  Duracion.CORTA,  22, 40, None,                 "Piso tranquilo. Persona ordenada y respetuosa."),
    (2,  Duracion.MEDIA,  25, 50, Ocupacion.TRABAJADOR, "Hogar familiar. Persona estable y tranquila con mascotas."),
    (3,  Duracion.CORTA,  20, 35, None,                 "Ambiente mixto. Persona limpia y comunicativa."),
    (4,  Duracion.CORTA,  18, 26, Ocupacion.ESTUDIANTE, "Piso de chicas universitarias. Solo mujeres estudiantes."),
    (5,  Duracion.MEDIA,  25, 42, Ocupacion.TRABAJADOR, "Piso profesional serio. Solo larga o media estancia."),
    (6,  Duracion.MEDIA,  22, 45, None,                 "Hogar tranquilo con mascotas. Persona amante de los animales."),
    (7,  Duracion.MEDIA,  28, 50, Ocupacion.TRABAJADOR, "Ambiente académico. Buscamos perfil profesional o investigador."),
    (8,  Duracion.MEDIA,  18, 30, None,                 "Ambiente internacional y social. Cualquier perfil bienvenido."),
    (9,  Duracion.MEDIA,  22, 38, None,                 "Piso joven profesional. Persona organizada y comunicativa."),
    (10, Duracion.LARGA,  24, 40, Ocupacion.TRABAJADOR, "Solo larga estancia. Profesional que valore el silencio."),
    (11, Duracion.MEDIA,  20, 35, None,                 "Ambiente creativo. Artistas y freelances bienvenidos."),
    (12, Duracion.LARGA,  26, 45, Ocupacion.TRABAJADOR, "Piso muy organizado. Solo profesionales serios."),
    (13, Duracion.MEDIA,  22, 38, None,                 "Born histórico. Ambiente cultural y artístico."),
    (14, Duracion.MEDIA,  24, 40, Ocupacion.TRABAJADOR, "Zona 22@. Perfil tech o digital."),
    (15, Duracion.MEDIA,  25, 42, None,                 "Piso tranquilo. Persona que valore el silencio."),
    (16, Duracion.MEDIA,  20, 35, None,                 "Eixample animado. Perfil social o mixto."),
    (17, Duracion.LARGA,  28, 50, Ocupacion.TRABAJADOR, "Solo larga estancia. Profesional estable."),
    (18, Duracion.CORTA,  18, 30, None,                 "Cerca del mar. Ambiente festivo y relajado."),
    (19, Duracion.MEDIA,  22, 35, None,                 "Gràcia bohemia. Ambiente cultural y musical."),
    (20, Duracion.MEDIA,  22, 38, None,                 "Vila de Gràcia. Persona comunicativa y organizada."),
    (21, Duracion.MEDIA,  22, 38, None,                 "Born artístico. Ambiente cultural y nocturno."),
    (22, Duracion.LARGA,  28, 50, Ocupacion.TRABAJADOR, "Eixample clásico. Profesional para larga estancia."),
    (23, Duracion.MEDIA,  24, 40, Ocupacion.FREELANCE,  "Poblenou digital. Perfil tech o creativo."),
    (24, Duracion.LARGA,  28, 48, Ocupacion.TRABAJADOR, "Solo larga estancia. Ambiente muy tranquilo."),
    (25, Duracion.MEDIA,  30, 55, None,                 "Solo 2 personas. Perfil maduro cerca del mar."),
    (26, Duracion.LARGA,  28, 45, Ocupacion.TRABAJADOR, "Eixample premium. Profesional estable."),
    (27, Duracion.MEDIA,  24, 45, None,                 "Gràcia con mascotas. Amante de los animales."),
    (28, Duracion.LARGA,  30, 55, Ocupacion.TRABAJADOR, "Sagrada Família. Perfil serio para larga estancia."),
    (29, Duracion.LARGA,  28, 48, None,                 "Poblenou mar. Solo larga estancia."),
    (30, Duracion.LARGA,  32, 55, Ocupacion.TRABAJADOR, "Eixample señorial. Perfil muy profesional."),
    (31, Duracion.LARGA,  28, 55, None,                 "Les Corts universitaria. Sector salud preferido."),
    (32, Duracion.LARGA,  32, 65, None,                 "Sarrià exclusivo. Solo adultos muy tranquilos."),
    (33, Duracion.LARGA,  35, 60, Ocupacion.TRABAJADOR, "Les Corts premium. Perfil muy seleccionado."),
    (34, Duracion.LARGA,  35, 70, None,                 "Sarrià top. Persona muy mayor y tranquila."),
    (35, Duracion.LARGA,  35, 55, Ocupacion.TRABAJADOR, "Eixample modernista. Perfil ejecutivo."),
    (36, Duracion.LARGA,  28, 55, None,                 "Les Corts con piscina. Ambiente familiar."),
    (37, Duracion.LARGA,  38, 70, None,                 "Sarrià lujo. Solo perfil senior muy seleccionado."),
    (38, Duracion.LARGA,  30, 52, Ocupacion.TRABAJADOR, "Eixample terraza. Solo larga estancia."),
    (39, Duracion.LARGA,  35, 70, None,                 "Sarrià top exclusivo. Perfil muy alto."),
]

CANDIDATES_RAW = [
    ("Laura Gómez",    23, Ocupacion.ESTUDIANTE, 420,  ["Gràcia","Vila de Gràcia"],          9,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, Genero.MUJER,          PreferenciaGenero.MIXTO),
    ("Marc Puig",      28, Ocupacion.TRABAJADOR, 750,  ["Eixample","Dreta de l'Eixample"],   18, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Sofía Martín",   21, Ocupacion.ESTUDIANTE, 380,  ["Nou Barris","Horta-Guinardó"],       4,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, True,  Genero.MUJER,          PreferenciaGenero.MISMO_GENERO),
    ("Pau Ferrer",     32, Ocupacion.FREELANCE,  900,  ["Sarrià-Sant Gervasi","Les Corts"],  24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.FLEXIBLE,  True,  False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Elena Torres",   26, Ocupacion.TRABAJADOR, 650,  ["Poblenou","Sant Martí"],            10, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("Jordi Casas",    24, Ocupacion.ESTUDIANTE, 450,  ["Gràcia","Camp de l'Arpa","Clot"],    8, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.FLEXIBLE,  False, False, Genero.HOMBRE,         PreferenciaGenero.MIXTO),
    ("Ana Ruiz",       35, Ocupacion.TRABAJADOR, 820,  ["Les Corts","Sarrià-Sant Gervasi"],  24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("David López",    29, Ocupacion.FREELANCE,  700,  ["Eixample","Poblenou"],              18, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  True,  False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Marta Vidal",    22, Ocupacion.ESTUDIANTE, 350,  ["Horta-Guinardó","Nou Barris"],       9, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, Genero.MUJER,          PreferenciaGenero.MISMO_GENERO),
    ("Carlos Sánchez", 31, Ocupacion.TRABAJADOR, 680,  ["Sant Martí","Poblenou"],            24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Núria Mas",      20, Ocupacion.ESTUDIANTE, 330,  ["Nou Barris","Horta-Guinardó"],       4, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, Genero.MUJER,          PreferenciaGenero.MISMO_GENERO),
    ("Tomàs Roca",     27, Ocupacion.FREELANCE,  580,  ["El Born","Barceloneta","Sant Pere"],10, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Irene Blanco",   33, Ocupacion.TRABAJADOR, 780,  ["Eixample","Esquerra de l'Eixample"],24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("Guillem Font",   25, Ocupacion.ESTUDIANTE, 480,  ["Sant Pere","El Born"],               6, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, True,  Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Rosa Jiménez",   40, Ocupacion.TRABAJADOR, 950,  ["Sarrià-Sant Gervasi","Les Corts"],  36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    True,  False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("Andreu Sala",    23, Ocupacion.ESTUDIANTE, 400,  ["Horta-Guinardó","Nou Barris","Clot"],8, EstiloConvivencia.SOCIAL,    ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Xavier Pons",    26, Ocupacion.FREELANCE,  620,  ["Poblenou","Clot","Sant Martí"],     12, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Claudia Rey",    21, Ocupacion.ESTUDIANTE, 360,  ["Nou Barris","Horta-Guinardó"],       5, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, Genero.MUJER,          PreferenciaGenero.MISMO_GENERO),
    ("Sara Pedraza",   27, Ocupacion.TRABAJADOR, 600,  ["Poblenou","Sant Martí"],            12, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("Arnau Esteve",   31, Ocupacion.FREELANCE,  750,  ["Gràcia","Eixample","Poblenou"],     18, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Montse Herrero", 44, Ocupacion.TRABAJADOR, 950,  ["Sarrià-Sant Gervasi","Les Corts"],  36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    True,  False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("Pol Oliveras",   20, Ocupacion.ESTUDIANTE, 310,  ["Nou Barris","Horta-Guinardó"],       4, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Júlia Campà",    25, Ocupacion.ESTUDIANTE, 500,  ["Barceloneta","El Born","Gràcia"],    9, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, Genero.MUJER,          PreferenciaGenero.MISMO_GENERO),
    ("Ferran Coll",    34, Ocupacion.TRABAJADOR, 800,  ["Sant Andreu","Clot","Sant Martí"],  24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Miquel Serra",   30, Ocupacion.TRABAJADOR, 700,  ["Sant Andreu","Clot","Sant Martí"],  18, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Laia Montserrat",24, Ocupacion.ESTUDIANTE, 460,  ["El Born","Barceloneta","Sant Pere"], 9, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, True,  Genero.MUJER,          PreferenciaGenero.MISMO_GENERO),
    ("Carme Solà",     36, Ocupacion.TRABAJADOR, 850,  ["Sarrià-Sant Gervasi","Gràcia"],     36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    True,  False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
    ("Biel Nadal",     22, Ocupacion.ESTUDIANTE, 390,  ["Camp de l'Arpa","Clot","Nou Barris"],5, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Roger Expósito", 29, Ocupacion.FREELANCE,  800,  ["Eixample","Poblenou"],              18, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  True,  False, Genero.HOMBRE,         PreferenciaGenero.SIN_PREFERENCIA),
    ("Pilar Moreno",   38, Ocupacion.TRABAJADOR, 870,  ["Les Corts","Eixample"],             24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, Genero.MUJER,          PreferenciaGenero.SIN_PREFERENCIA),
]


def populate_database():
    init_db()
    conn = get_connection()
    for tbl in ["roommates","households","listings","candidates"]:
        conn.execute(f"DELETE FROM {tbl}")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('roommates','households','listings','candidates')")
    except: pass
    conn.commit(); conn.close()

    listing_ids = []
    for titulo, barrio, precio, pt, pd, meses, mascotas, fumar, desc in LISTINGS_RAW:
        dur = meses_a_duracion(meses)
        l = Listing(id=0, titulo=titulo, barrio=barrio, precio_mes=precio,
            plazas_totales=pt, plazas_disponibles=pd, duracion_minima=dur,
            meses_minimos=meses, permite_mascotas=mascotas, permite_fumar=fumar,
            descripcion=desc)
        listing_ids.append(insert_listing(l))

    for idx, dur_pref, emin, emax, ocu, desc in HOUSEHOLDS_RAW:
        hh = Household(id=0, listing_id=listing_ids[idx], duracion_preferida=dur_pref,
            perfil_buscado_edad_min=emin, perfil_buscado_edad_max=emax,
            perfil_buscado_ocupacion=ocu, descripcion=desc)
        insert_household(hh)

    for idx, roommates_data in ROOMMATES_BY_LISTING.items():
        lid = listing_ids[idx]
        for nombre, edad, ocu, estilo, ruido, horario, genero, pgen, es_prop, desc in roommates_data:
            rm = Roommate(id=0, listing_id=lid, nombre=nombre, edad=edad,
                ocupacion=ocu, estilo_convivencia=estilo, tolerancia_ruido=ruido,
                horario=horario, genero=genero, preferencia_genero=pgen,
                es_propietario=es_prop, descripcion=desc)
            insert_roommate(rm)

    for nombre, edad, ocu, presup, barrios, meses, estilo, ruido, horario, mascotas, fumador, genero, pgen in CANDIDATES_RAW:
        dur = meses_a_duracion(meses)
        c = Candidate(id=0, nombre=nombre, edad=edad, ocupacion=ocu,
            presupuesto_max=presup, barrios_preferidos=barrios,
            meses_estancia=meses, duracion_deseada=dur, estilo_convivencia=estilo,
            tolerancia_ruido=ruido, horario=horario, acepta_mascotas=mascotas,
            fumador=fumador, genero=genero, preferencia_genero=pgen, descripcion="")
        insert_candidate(c)

    rm_total = sum(len(v) for v in ROOMMATES_BY_LISTING.values())
    print(f"Dataset v4: {len(LISTINGS_RAW)} pisos, {len(HOUSEHOLDS_RAW)} hogares, {rm_total} convivientes, {len(CANDIDATES_RAW)} candidatos.")

if __name__ == "__main__":
    populate_database()
