"""Dataset sintético v3 — 40 pisos variados, precios desde 300€, coherencia precio-barrio."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.models import (Candidate, Listing, Household, Ocupacion, EstiloConvivencia,
    ToleranciaRuido, Duracion, Horario, PreferenciaGenero, meses_a_duracion)
from database.db import init_db, insert_candidate, insert_listing, insert_household, get_connection

# (titulo, barrio, precio, plazas_tot, plazas_disp, meses_min, mascotas, fumar, descripcion)
LISTINGS_RAW = [
    # ECONÓMICOS 300–400€ (barrios periféricos)
    ("Habitación asequible en Nou Barris",       "Nou Barris",               300, 4, 2, 3,  False, False, "Piso amplio y funcional. Buenas conexiones de metro. Compañeros estudiantes."),
    ("Hab. tranquila en Horta-Guinardó",         "Horta-Guinardó",           310, 5, 3, 3,  False, True,  "Ambiente tranquilo, cocina equipada, wifi incluido. Zona residencial bien comunicada."),
    ("Hab. en piso familiar Sant Andreu",        "Sant Andreu",              320, 4, 2, 6,  True,  False, "Piso amplio con terraza. Mascotas pequeñas bienvenidas. Barrio tranquilo."),
    ("Hab. económica en Sants",                  "Sants-Montjuïc",           330, 4, 2, 4,  False, False, "Muy bien comunicado con Sants Estació. Piso luminoso con buenas zonas comunes."),
    ("Hab. piso estudiantes Clot",               "Clot",                     340, 5, 3, 4,  False, False, "Piso joven y social. Cerca transporte y universidad. Comunidad activa."),
    ("Hab. en Nou Barris reformada",             "Nou Barris",               360, 3, 1, 6,  False, False, "Piso reformado en 2022. Ascensor. Compañeros trabajadores tranquilos."),
    ("Hab. con jardín en Horta",                 "Horta-Guinardó",           370, 4, 2, 6,  True,  False, "Jardín compartido. Barrio residencial silencioso. Mascotas permitidas."),
    ("Hab. asequible en Sant Andreu norte",      "Sant Andreu",              380, 4, 1, 6,  False, False, "Zona tranquila con parques. Piso bien mantenido, compañeros respetuosos."),

    # RANGO MEDIO-BAJO 400–520€
    ("Hab. social en Vila de Gràcia",            "Vila de Gràcia",           410, 4, 2, 6,  False, False, "Piso muy social en el corazón de Gràcia. Ambiente festivo y abierto."),
    ("Hab. luminosa en Camp de l'Arpa",          "Camp de l'Arpa",           420, 3, 1, 6,  False, False, "Piso moderno y luminoso. Buena comunidad de jóvenes profesionales."),
    ("Hab. tranquila Sagrada Família",           "Sagrada Família",          430, 3, 1, 9,  False, False, "Piso silencioso, compañeros respetuosos. Cerca de universidades y transporte."),
    ("Hab. en Sant Pere céntrico",               "Sant Pere",                440, 4, 2, 6,  False, True,  "Zona histórica céntrica. Ambiente mixto joven. Fumadores bienvenidos en terraza."),
    ("Hab. profesional en Sants",                "Sants-Montjuïc",           450, 3, 1, 12, False, False, "Compañeros trabajadores, ambiente muy organizado. Piso bien equipado."),
    ("Hab. con encanto en El Born",              "El Born",                  460, 3, 1, 6,  False, False, "Piso con carácter, techos altos. Compañeros creativos y abiertos."),
    ("Hab. en Poblenou tecnológico",             "Poblenou",                 470, 4, 2, 9,  False, False, "Zona 22@ en auge. Ideal para trabajadores del sector tech. Ambiente dinámico."),
    ("Hab. con terraza en Clot",                 "Clot",                     490, 3, 1, 9,  False, False, "Acceso a terraza privada. Compañeros jóvenes trabajadores. Muy soleado."),
    ("Hab. en Esquerra de l'Eixample",           "Esquerra de l'Eixample",   500, 4, 2, 9,  False, False, "Eixample izquierdo animado. Cerca de bares, restaurantes y transporte."),
    ("Hab. tranquila en Sant Martí",             "Sant Martí",               510, 3, 1, 12, False, False, "Barrio tranquilo en expansión. Compañeros profesionales. Piso bien organizado."),
    ("Hab. cerca del mar Barceloneta",           "Barceloneta",              520, 3, 1, 3,  False, True,  "Cerca del mar. Ambiente veraniego y social. Ideal para estancias cortas."),
    ("Hab. en Gràcia con carácter",              "Gràcia",                   530, 3, 1, 6,  False, False, "Piso acogedor en Gràcia. Comunidad mixta y abierta. Mucha luz natural."),

    # RANGO MEDIO 540–700€
    ("Hab. moderna en Vila de Gràcia",           "Vila de Gràcia",           540, 3, 1, 9,  False, False, "Zona muy buscada. Piso tranquilo con buena convivencia. Terrazas comunitarias."),
    ("Hab. premium El Born",                     "El Born",                  560, 3, 1, 9,  False, False, "Piso con encanto en el Born. Techos originales, suelos de madera. Ambiente cultural."),
    ("Hab. en Eixample derecho",                 "Dreta de l'Eixample",      580, 4, 2, 12, False, False, "Eixample clásico, piso señorial reformado. Compañeros profesionales establecidos."),
    ("Hab. con balcón en Poblenou",              "Poblenou",                 600, 3, 1, 9,  False, False, "Balcón propio. Zona tech en auge. Compañeros del sector digital y creativo."),
    ("Hab. reformada en Sant Martí",             "Sant Martí",               610, 3, 1, 12, False, False, "Piso reformado completamente en 2023. Compañeros profesionales estables."),
    ("Hab. exclusiva Barceloneta",               "Barceloneta",              620, 2, 1, 6,  False, False, "A 2 minutos de la playa. Piso para 2 personas. Silencioso y muy cuidado."),
    ("Hab. en Esquerra Eixample premium",        "Esquerra de l'Eixample",   640, 3, 1, 12, False, False, "Gayxample. Comunidad tolerante y diversa. Muy bien equipado y luminoso."),
    ("Hab. con mascotas en Gràcia",              "Gràcia",                   650, 3, 1, 9,  True,  False, "Mascotas bienvenidas. Piso muy cálido y acogedor. Compañeros amantes de los animales."),
    ("Hab. en Sagrada Família premium",          "Sagrada Família",          660, 3, 1, 12, False, False, "Piso luminoso junto a la Sagrada Família. Muy turístico pero tranquilo por dentro."),
    ("Hab. en Poblenou junto al mar",            "Poblenou",                 680, 3, 1, 12, False, False, "A 5 minutos a pie de la playa. Piso moderno con terraza compartida. Muy luminoso."),

    # PREMIUM 700–950€ (Eixample, Sarrià, Les Corts)
    ("Hab. premium en Eixample",                 "Eixample",                 700, 3, 1, 12, False, False, "Piso señorial en el Eixample. Techos altos, suelos hidráulicos. Compañeros profesionales."),
    ("Hab. en Les Corts zona universitaria",     "Les Corts",                720, 3, 1, 12, False, False, "Cerca de la UB y hospitales. Ideal para médicos residentes o profesores. Muy tranquilo."),
    ("Hab. luminosa en Sarrià",                  "Sarrià-Sant Gervasi",      750, 3, 1, 18, False, False, "Barrio residencial tranquilo. Piso cuidado con jardín privado. Compañeros profesionales."),
    ("Hab. premium Les Corts",                   "Les Corts",                780, 2, 1, 18, False, False, "Piso para 2 personas, máxima privacidad. Zona premium tranquila y bien comunicada."),
    ("Piso exclusivo en Sarrià",                 "Sarrià-Sant Gervasi",      820, 2, 1, 24, True,  False, "Jardín privado, zona de máxima tranquilidad. Mascotas bienvenidas. Solo adultos."),
    ("Hab. en Dreta Eixample exclusiva",         "Dreta de l'Eixample",      840, 3, 1, 18, False, False, "Piso modernista reformado. Zona premium. Compañeros de perfil profesional alto."),
    ("Hab. en Les Corts con piscina",            "Les Corts",                860, 4, 2, 12, False, False, "Edificio con piscina comunitaria. Zona tranquila cerca del Camp Nou."),
    ("Piso de lujo en Sarrià-Sant Gervasi",      "Sarrià-Sant Gervasi",      900, 2, 1, 24, True,  False, "Zona alta de Barcelona. Jardín, garaje. Perfil ejecutivo o profesional senior."),
    ("Hab. premium Eixample con terraza",        "Eixample",                 920, 3, 1, 18, False, False, "Terraza privada en el Eixample. Piso de alto standing. Solo larga estancia."),
    ("Hab. en Sarrià top",                       "Sarrià-Sant Gervasi",      950, 2, 1, 24, True,  False, "El mejor piso del dataset. Jardín, terraza, zona residencial exclusiva. Todo incluido."),
]

# (listing_idx, estilo, ruido, horario, ocu_pref, edad_min, edad_max, dur_pref, num_conv, pref_genero, descripcion)
HOUSEHOLDS_RAW = [
    (0,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  Ocupacion.ESTUDIANTE, 18,27, Duracion.CORTA,  3, PreferenciaGenero.SIN_PREFERENCIA, "Piso de estudiantes con buen ambiente. Buscamos alguien sociable y respetuoso."),
    (1,  EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO,    None,                 20,35, Duracion.CORTA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso tranquilo. Buscamos persona ordenada y respetuosa con los espacios comunes."),
    (2,  EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 25,45, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Hogar familiar y acogedor. Buscamos persona estable y tranquila."),
    (3,  EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,35, Duracion.CORTA,  3, PreferenciaGenero.SIN_PREFERENCIA, "Ambiente mixto y flexible. Buscamos persona limpia y comunicativa."),
    (4,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  Ocupacion.ESTUDIANTE, 18,26, Duracion.CORTA,  4, PreferenciaGenero.MIXTO,           "Piso universitario muy social. Fiestas ocasionales entre semana."),
    (5,  EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 25,40, Duracion.MEDIA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Piso solo para 2. Buscamos profesional tranquilo y ordenado."),
    (6,  EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 28,50, Duracion.MEDIA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Persona mayor de 28 bienvenida. Piso tranquilo y ordenado."),
    (7,  EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 22,40, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso con jardín, muy tranquilo. Aceptamos mascotas."),
    (8,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  None,                 18,30, Duracion.MEDIA,  2, PreferenciaGenero.MIXTO,           "Ambiente muy social y abierto. Buscamos persona extrovertida y sociable."),
    (9,  EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,35, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso joven y profesional. Buscamos alguien limpio y comunicativo."),
    (10, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 22,35, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Ambiente silencioso. Ideal para quien necesita concentración."),
    (11, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  None,                 18,30, Duracion.CORTA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Zona céntrica y animada. Piso social cerca de bares y restaurantes."),
    (12, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 25,45, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Buscamos profesional estable para larga estancia. Piso muy organizado."),
    (13, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,35, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Ambiente creativo y abierto. Artistas y freelances bienvenidos."),
    (14, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  Ocupacion.TRABAJADOR, 22,38, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso tech en Poblenou. Buscamos perfil profesional del sector digital."),
    (15, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 23,40, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso con terraza. Ambiente tranquilo y organizado."),
    (16, EstiloConvivencia.SOCIAL,    ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,35, Duracion.MEDIA,  2, PreferenciaGenero.MIXTO,           "Zona animada del Eixample. Piso mixto y abierto."),
    (17, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 25,45, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso profesional. Solo larga estancia. Compañeros estables y tranquilos."),
    (18, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  None,                 18,30, Duracion.CORTA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Cerca del mar. Ambiente festivo y relajado."),
    (19, EstiloConvivencia.SOCIAL,    ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,32, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso de Gràcia con mucho carácter. Ambiente cultural y bohemio."),
    (20, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,35, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso moderno en Vila de Gràcia. Buscamos persona comunicativa."),
    (21, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  None,                 20,35, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Born histórico. Ambiente cultural y artístico. Techos altos."),
    (22, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 25,42, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Eixample clásico. Buscamos profesional para larga estancia."),
    (23, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  Ocupacion.FREELANCE,  24,38, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Zona digital de Poblenou. Ideal para freelances y perfiles tech."),
    (24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 26,45, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Piso reformado. Solo larga estancia. Ambiente muy tranquilo."),
    (25, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 28,50, Duracion.MEDIA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Solo 2 personas. Máxima privacidad cerca del mar."),
    (26, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 25,40, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Eixample izquierdo premium. Comunidad profesional estable."),
    (27, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 25,45, Duracion.MEDIA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Mascotas bienvenidas. Piso cálido y familiar en Gràcia."),
    (28, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 28,50, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Zona Sagrada Família. Piso luminoso y tranquilo."),
    (29, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 26,45, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Cerca de la playa. Piso moderno con terraza. Solo larga estancia."),
    (30, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 28,50, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Eixample señorial. Compañeros profesionales de perfil alto."),
    (31, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 25,45, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Zona universitaria y hospitalaria. Ideal para médicos o investigadores."),
    (32, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 28,55, Duracion.LARGA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Sarrià tranquilo con jardín. Solo adultos. Larga estancia."),
    (33, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 30,55, Duracion.LARGA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Solo 2 personas. Piso premium y tranquilo. Perfil profesional."),
    (34, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 30,65, Duracion.LARGA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Zona alta exclusiva. Solo adultos mayores de 30. Máxima tranquilidad."),
    (35, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 28,50, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Eixample modernista. Piso de alto standing. Perfil ejecutivo."),
    (36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 25,50, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Les Corts con piscina comunitaria. Zona muy tranquila y familiar."),
    (37, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 32,65, Duracion.LARGA,  1, PreferenciaGenero.SIN_PREFERENCIA, "El mejor piso. Jardín, terraza. Perfil ejecutivo o profesional senior."),
    (38, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    Ocupacion.TRABAJADOR, 28,50, Duracion.LARGA,  2, PreferenciaGenero.SIN_PREFERENCIA, "Terraza privada en Eixample. Solo larga estancia. Alto standing."),
    (39, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    None,                 30,65, Duracion.LARGA,  1, PreferenciaGenero.SIN_PREFERENCIA, "Sarrià exclusivo. Jardín, garaje. El piso más premium del sistema."),
]

# Candidatos sintéticos
CANDIDATES_RAW = [
    ("Laura Gómez",    23, Ocupacion.ESTUDIANTE, 420,  ["Gràcia","Vila de Gràcia"],          9,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, PreferenciaGenero.MIXTO),
    ("Marc Puig",      28, Ocupacion.TRABAJADOR, 750,  ["Eixample","Dreta de l'Eixample"],   18, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Sofía Martín",   21, Ocupacion.ESTUDIANTE, 380,  ["Nou Barris","Horta-Guinardó"],       4,  EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, True,  PreferenciaGenero.MISMO_GENERO),
    ("Pau Ferrer",     32, Ocupacion.FREELANCE,  900,  ["Sarrià-Sant Gervasi","Les Corts"],  24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.FLEXIBLE,  True,  False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Elena Torres",   26, Ocupacion.TRABAJADOR, 650,  ["Poblenou","Sant Martí"],            10, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Jordi Casas",    24, Ocupacion.ESTUDIANTE, 450,  ["Gràcia","Camp de l'Arpa","Clot"],    8, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.FLEXIBLE,  False, False, PreferenciaGenero.MIXTO),
    ("Ana Ruiz",       35, Ocupacion.TRABAJADOR, 820,  ["Les Corts","Sarrià-Sant Gervasi"],  24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("David López",    29, Ocupacion.FREELANCE,  700,  ["Eixample","Poblenou"],              18, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  True,  False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Marta Vidal",    22, Ocupacion.ESTUDIANTE, 350,  ["Horta-Guinardó","Nou Barris"],       9, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, PreferenciaGenero.MISMO_GENERO),
    ("Carlos Sánchez", 31, Ocupacion.TRABAJADOR, 680,  ["Sant Martí","Poblenou"],            24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Núria Mas",      20, Ocupacion.ESTUDIANTE, 330,  ["Nou Barris","Horta-Guinardó"],       4, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, PreferenciaGenero.MISMO_GENERO),
    ("Tomàs Roca",     27, Ocupacion.FREELANCE,  580,  ["El Born","Barceloneta","Sant Pere"],10, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Irene Blanco",   33, Ocupacion.TRABAJADOR, 780,  ["Eixample","Esquerra de l'Eixample"],24,EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Guillem Font",   25, Ocupacion.ESTUDIANTE, 480,  ["Sant Pere","El Born"],               6, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, True,  PreferenciaGenero.SIN_PREFERENCIA),
    ("Rosa Jiménez",   40, Ocupacion.TRABAJADOR, 950,  ["Sarrià-Sant Gervasi","Les Corts"],  36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    True,  False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Andreu Sala",    23, Ocupacion.ESTUDIANTE, 400,  ["Horta-Guinardó","Nou Barris","Clot"],8, EstiloConvivencia.SOCIAL,    ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Pilar Moreno",   38, Ocupacion.TRABAJADOR, 870,  ["Les Corts","Eixample"],             24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Xavier Pons",    26, Ocupacion.FREELANCE,  620,  ["Poblenou","Clot","Sant Martí"],     12, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Claudia Rey",    21, Ocupacion.ESTUDIANTE, 360,  ["Nou Barris","Horta-Guinardó"],       5, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, PreferenciaGenero.MISMO_GENERO),
    ("Miquel Serra",   30, Ocupacion.TRABAJADOR, 700,  ["Sant Andreu","Clot","Sant Martí"],  18, EstiloConvivencia.TRANQUILO, ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Laia Montserrat",24, Ocupacion.ESTUDIANTE, 460,  ["El Born","Barceloneta","Sant Pere"], 9, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, True,  PreferenciaGenero.MISMO_GENERO),
    ("Roger Expósito", 29, Ocupacion.FREELANCE,  720,  ["Eixample","Poblenou"],              18, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  True,  False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Carme Solà",     36, Ocupacion.TRABAJADOR, 850,  ["Sarrià-Sant Gervasi","Gràcia"],     36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    True,  False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Biel Nadal",     22, Ocupacion.ESTUDIANTE, 390,  ["Camp de l'Arpa","Clot","Nou Barris"],5, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Sara Pedraza",   27, Ocupacion.TRABAJADOR, 600,  ["Poblenou","Sant Martí"],            12, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Arnau Esteve",   31, Ocupacion.FREELANCE,  750,  ["Gràcia","Eixample","Poblenou"],     18, EstiloConvivencia.MIXTO,     ToleranciaRuido.MEDIA, Horario.FLEXIBLE,  False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Montse Herrero", 44, Ocupacion.TRABAJADOR, 950,  ["Sarrià-Sant Gervasi","Les Corts"],  36, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    True,  False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Pol Oliveras",   20, Ocupacion.ESTUDIANTE, 310,  ["Nou Barris","Horta-Guinardó"],       4, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, PreferenciaGenero.SIN_PREFERENCIA),
    ("Júlia Campà",    25, Ocupacion.ESTUDIANTE, 500,  ["Barceloneta","El Born","Gràcia"],    9, EstiloConvivencia.SOCIAL,    ToleranciaRuido.ALTA,  Horario.NOCTURNO,  False, False, PreferenciaGenero.MISMO_GENERO),
    ("Ferran Coll",    34, Ocupacion.TRABAJADOR, 800,  ["Sant Andreu","Clot","Sant Martí"],  24, EstiloConvivencia.TRANQUILO, ToleranciaRuido.BAJA,  Horario.DIURNO,    False, False, PreferenciaGenero.SIN_PREFERENCIA),
]


def populate_database():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM households"); conn.execute("DELETE FROM listings")
    conn.execute("DELETE FROM candidates")
    try: conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('households','listings','candidates')")
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

    for idx, estilo, ruido, horario, ocu, emin, emax, dur, nconv, pgen, desc in HOUSEHOLDS_RAW:
        hh = Household(id=0, listing_id=listing_ids[idx], estilo_convivencia=estilo,
            tolerancia_ruido=ruido, horario_predominante=horario,
            perfil_buscado_ocupacion=ocu, perfil_buscado_edad_min=emin,
            perfil_buscado_edad_max=emax, duracion_preferida=dur,
            num_convivientes_actuales=nconv, preferencia_genero=pgen, descripcion=desc)
        insert_household(hh)

    for nombre, edad, ocu, presup, barrios, meses, estilo, ruido, horario, mascotas, fumador, pgen in CANDIDATES_RAW:
        dur = meses_a_duracion(meses)
        c = Candidate(id=0, nombre=nombre, edad=edad, ocupacion=ocu,
            presupuesto_max=presup, barrios_preferidos=barrios,
            meses_estancia=meses, duracion_deseada=dur, estilo_convivencia=estilo,
            tolerancia_ruido=ruido, horario=horario, acepta_mascotas=mascotas,
            fumador=fumador, preferencia_genero=pgen, descripcion="")
        insert_candidate(c)

    print(f"Dataset v3: {len(LISTINGS_RAW)} pisos, {len(HOUSEHOLDS_RAW)} hogares, {len(CANDIDATES_RAW)} candidatos.")


if __name__ == "__main__":
    populate_database()
