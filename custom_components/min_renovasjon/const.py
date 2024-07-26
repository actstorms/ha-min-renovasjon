from typing import Final

DOMAIN: Final = "min_renovasjon"

CONF_STREET_NAME: Final = "street_name"
CONF_STREET_CODE: Final = "street_code"
CONF_HOUSE_NO: Final = "house_no"
CONF_COUNTY_ID: Final = "county_id"
CONF_DATE_FORMAT: Final = "date_format"
CONF_FRACTIONS: Final = "fractions"
DEFAULT_DATE_FORMAT: Final = "%d/%m/%Y"

COORDINATOR: Final = "coordinator"

FRACTION_IDS: Final[dict[int, str]] = {
    1: "Restavfall",
    2: "Papir",
    3: "Matavfall",
    4: "Glass/Metallemballasje",
    5: "Drikkekartonger",
    6: "Spesialavfall",
    7: "Plastemballasje",
    8: "Trevirke",
    9: "Tekstiler",
    10: "Hageavfall",
    11: "Metaller",
    12: "Hvitevarer/EE-avfall",
    13: "Papp",
    14: "Møbler",
    19: "Plastemballasje",
    23: "Nedgravd løsning",
    24: "GlassIGLO",
    25: "Farlig avfall",
    26: "Matavfall hytter",
    27: "Restavfall hytter",
    28: "Papir hytter"
}