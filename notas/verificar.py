"""Comprobaciones del código sobre lo que dice el modelo (NOTE_READER_SPEC §5, regla N1 firmada 14 nov 2026).

El modelo solo propone. Aquí se decide qué cuenta:
1. la salida tiene la forma esperada;
2. la cita está, literalmente, en la nota (solo se normalizan espacios y comillas; nada difuso). Con la forma
   nueva el modelo no copia nada: señala el número de una frase y el código copia esa frase de la nota;
3. negaciones, planes y otras personas (N1d) se buscan en la FRASE ENTERA que contiene la cita, no solo en la cita;
4. «ya realizada»: la frase nombra la prueba; la fecha la lee el código (una sola fecha en la frase: si hay
   varias o un intervalo, es ambigua y no cuenta); el modelo solo da una pista que debe coincidir;
5. una nota con órdenes dirigidas al modelo no se usa (§5.6).
Cualquier fallo → verificada = 0 y sin efecto (N1e). Fechas en formato español (día/mes/año).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple

ETIQUETAS = {"ya_realizada", "rechazo", "nefrologia", "ninguna"}
PRUEBAS = {"CAC", "FGe"}

# N1a: palabras que nombran cada prueba. «Creatinina» sola NO nombra el FGe (puede ser urinaria).
# Vuelta 15, V2 (firmada por Ahmed, 16 nov 2026, docs/FIRMA_VUELTA_15.md): el CAC también se llama «índice», «ratio» o «relación»
# albúmina/creatinina, y «cociente microalbúmina/creatinina» (texto real, LivingNER held-out 2, error E-19).
_ALB_CREAT = r"(?:micro)?alb[uú]mina\s*[/\-]?\s*creat(?:inina)?\b"
_NOMBRE_CAC = rf"(?:(?:cociente|[íi]ndice|ratio|relaci[oó]n)\s+(?:de\s+)?{_ALB_CREAT}|microalb[uú]mina\s*/\s*creat(?:inina)?\b)"
NOMBRA = {
    "CAC": re.compile(rf"\b(cac|{_NOMBRE_CAC}|microalbuminuria|albuminuria)\b", re.I),
    "FGe": re.compile(r"\b(fge?|filtrado(\s+glomerular)?|creatinina\s+(s[eé]rica|en\s+sangre|plasm[aá]tica))\b", re.I),
}
NOMBRE_CAC = re.compile(rf"{_NOMBRE_CAC}(\s+en\s+orina)?", re.I)
# N1d (ampliada con pruebas adversarias, 14 nov): negación, plan o petición, cancelación.
NEGACION = re.compile(
    r"\b(no\s+(se\s+)?(le\s+)?(ha\s+|han\s+)?(realiz\w*|hizo|hecho|hace|hech\w*|consta\w*|aporta\w*|trae)|no\s+consta|"
    r"pendiente\s+de|sin\s+realizar|se\s+le\s+explica|programad\w*|solicit\w*|pid\w*|pedid\w*|petici[oó]n|"
    r"se\s+cursa|previst\w*|cancelad\w*|anulad\w*|suspendid\w*|ausente|falta\w*|realizar[aá]n?|har[aá]n?|"
    r"a\s+la\s+espera|en\s+espera|pendiente|sin\s+(cac|fge?|anal[ií]tica|resultado|realizar)|no\s+lleg\w*|no\s+pud\w*|"
    r"rechaz\w*|no\s+quiere|cita\s+para|"
    # Vuelta 6 (revisión externa, 14 nov): «Plan: CAC el …» y «Volante para CAC» son peticiones, no resultados.
    r"plan|volantes?)\b", re.I)
# Tiempo relativo («hace 2 años», «el año pasado»): la fecha no se puede fijar → no cuenta.
RELATIVO = re.compile(r"\bhace\s+(\d+|un|una|unos|unas|dos|tres|varios|varias|algunos|algunas|poco)\b|"
                      r"\b(año|mes|verano|invierno)\s+pasado\b|\bel\s+pasado\b|\banterior\b", re.I)
NO_SEGUIDO = re.compile(r"\bno\s+(est[aá]\s+|es\s+)?(seguid\w*|controlad\w*|vist\w*)\b", re.I)
# Vuelta 11 (revisor en bucle, ronda 4): faltaban determinantes («tu», «este», «esa», «nuestra», «del»…).
DETERMINANTE = r"(su|sus|tu|tus|la|el|las|los|una?|al|del|mi|mis|nuestr[oa]s?|vuestr[oa]s?|est[eoa]s?|es[eoa]s?|aquel(l[oa]s?)?|otr[oa]s?)"
POSESIVO = r"(su|sus|tu|tus|mi|mis|nuestr[oa]s?|vuestr[oa]s?)"
OTRA_PERSONA = re.compile(rf"\b{DETERMINANTE}\s+(madre|padre|padres|herman[oa]s?|hij[oa]s?|espos[oa]|"
                          r"marido|mujer|pareja|abuel[oa]s?|t[ií][oa]s?|prim[oa]s?|vecin[oa]s?|cuidador[a]?|"
                          # Vuelta 9 (ronda 3): estas solo con determinante: «médico de familia», «antecedentes familiares»,
                          # «enfermera tutora», «compañero de consulta», «pareja estable» o «Dr. Tito» hablan del paciente.
                          r"familia|familiar(es)?)\b|"
                          # «el compañero de consulta» es un colega: estas solo con posesivo.
                          rf"\b{POSESIVO}\s+(tutor(a|es|as)?|compañer[oa]s?|tit[oa]s?)\b|"
                          # «familiares» en plural, salvo «antecedentes familiares».
                          r"(?<!antecedentes\s)\bfamiliares\b|"
                          r"\bacompañante\b|"
                          # Vuelta 6: «Madre con CAC 12 mg/g» (sin artículo). «Mujer» no: «mujer de 60 años».
                          r"\b(madre|padre|herman[oa]s?|hij[oa]s?|espos[oa]|marido|abuel[oa]s?|"
                          # Vuelta 7 (revisor en bucle): el resto de familiares y cuidadores, también sin artículo.
                          r"t[ií][oa]s?|prim[oa]s?|c[oó]nyuges?|niet[oa]s?|suegr[oa]s?|cu[ñn]ad[oa]s?|"
                          r"vecin[oa]s?|yernos?|nueras?|sobrin[oa]s?|cuidador(a|es|as)?|"
                          # Vuelta 8 (revisor en bucle, ronda 2): más familiares, pareja, amigos y otras personas.
                          r"padres|mam[aá]|pap[aá]|mami|papi|amig[oa]s?|bisabuel[oa]s?|"
                          r"bisniet[oa]s?|padrastros?|madrastras?|hermanastr[oa]s?|hijastr[oa]s?|novi[oa]s?|gemel[oa]s?|"
                          r"melliz[oa]s?|ahijad[oa]s?|padrinos?|madrinas?|progenitor(a|es|as)?|"
                          r"convivientes?|parientes?|allegad[oa]s?|ex\s*c[oó]nyuges?|ex\s*pareja|consuegr[oa]s?|"
                          r"abuelit[oa]s?|yay[oa]s?|otr[oa]\s+paciente|persona\s+de\s+apoyo)\b", re.I)
# Vuelta 11 (revisor en bucle, ronda 4): sin determinante, estas palabras pueden ser del paciente («médico de familia»,
# «pareja estable») o de otra persona («Pareja: CAC 12 mg/g»). Ante la duda solo conserva su efecto un CAC ALTERADO,
# que nunca retira (N1a); un CAC normal, un rechazo o una derivación no retiran nada.
PERSONA_DUDOSA = re.compile(r"\b(familia|familiar(es)?|parejas?|tutor(a|es|as)?|compañer[oa]s?|tit[oa]s?|"
                            # Vuelta 12 (revisor, ronda 5): abreviaturas y palabras de pareja o expareja. Aquí sobran
                            # palabras sin riesgo: lo peor es un aviso de más («ex fumador» con un CAC normal no retira).
                            r"af|fam|hn[oa]s?|hij|sra?|señor(a|es|as)?|ex|ex-?(marido|mujer|espos[oa]|pareja|novi[oa]|c[oó]nyuge)s?|consangu\w*|parentesco|chic[oa]s?|"
                            r"suy[oa]s)(?!\w)|\bhij@", re.I)
# Umbrales firmados del CAC (rules/00_parametros.sql: cac_umbral_mg_g, cac_umbral_mg_mmol); un test los compara.
CAC_UMBRAL = {"mg/g": 30.0, "mg/mmol": 3.0}


def _cac_alterado(fila: Dict[str, Any]) -> bool:
    umbral = CAC_UMBRAL.get(fila.get("unidad") or "")
    return fila.get("prueba") == "CAC" and fila.get("valor") is not None and umbral is not None \
        and fila["valor"] >= umbral


# §5.6: órdenes dirigidas al modelo (no instrucciones clínicas como «instrucciones del inhalador»).
INSTRUCCIONES = re.compile(
    r"\b(ignor\w*|olvid\w*|omit\w*)\b.{0,60}\b(instrucci\w*|indicaci\w*|reglas)\b|"
    r"\b(responde|contesta|devuelve|marca|escribe)\b.{0,40}\b(ya_realizada|json|etiqueta|con\s+la\s+cita)\b|"
    r"\b(ya_realizada|fecha_en_nota|prompt)\b|\betiqueta\s*[:=]|\bignore\b.{0,40}\binstructions?\b|"
    r"</?\s*nota\s*>|\bnueva\s+orden\b|\bclasifica\b.{0,30}\b(realizad\w*|como)\b|\bcopia\b.{0,20}\b(cita|frase|texto)\b|"
    # Bucle de estrés 2 (14 nov): «olvida todo lo anterior», fichas de plantilla de chat y «responde con la frase».
    r"\b(olvid\w*|ignor\w*)\b.{0,30}\b(todo\s+lo\s+anterior|lo\s+anterior|lo\s+dicho|previous|above)\b|"
    r"<\|[^|>]{0,30}\|>|\b(responde|contesta|devuelve)\b.{0,30}\bfrase\b", re.I | re.S)

MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"], start=1)}
FECHA_NUM = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})\b")
FECHA_MES = re.compile(r"\b(" + "|".join(MESES) + r")\s+(?:de\s+|del\s+)?(\d{4})\b", re.I)
FECHA_DIA_MES = re.compile(r"\b(\d{1,2})\s+de\s+(" + "|".join(MESES) + r")\s+(?:de\s+|del\s+)?(\d{4})\b", re.I)
HOY_EN_NOTA = re.compile(r"\b(hoy|esta\s+mañana|esta\s+manana)\b", re.I)
INTERVALO = re.compile(r"\b(entre|desde)\b.{0,30}\b(y|hasta|a)\b", re.I)
# Valor en la cita: «CAC 110 mg/g», «microalbuminuria de 45 mg/g», «cociente albúmina/creatinina: 3,5 mg/mmol», «FGe 60».
VALOR_CAC = re.compile(r"(?:cac|albuminuria|microalbuminuria|creatinina)\D{0,20}?(\d+(?:[.,]\d+)?)\s*(mg\s*/\s*(?:g|mmol))\b", re.I)
NUMERO_CAC = re.compile(r"(?:cac|albuminuria|microalbuminuria)\D{0,20}?\d", re.I)
# Bucle de estrés 1 (14 nov): el valor puede estar lejos de «CAC» («Repetido CAC en el H. de Manises el …: 180 mg/g»).
# Cualquier resultado con unidad de CAC en la frase cuenta; si hay más de uno distinto, es ambiguo.
# Vuelta 4 (ataques de GPT-6.1 Sol, 14 nov): la frase no describe un resultado válido del propio paciente.
NO_ES_RESULTADO = re.compile(r"\b(invalidad\w*|err[oó]ne\w*|hemoli[sz]ad\w*|no\s+v[aá]lid\w*|no\s+corresponde\w*|ejemplo|docente|"
                             r"transcrit\w*|copiad\w*)\b", re.I)
# …o el número no es el resultado del CAC: desigualdad, notación científica, valor de referencia, proteinuria.
VALOR_NO_FIABLE = re.compile(r"[<>≤≥]\s*\d|\b(inferior|superior|menor|mayor)\s+(a|de|que)\s+\d|\d[eE][-+]?\d|"
                             r"\b(referencia|rango|valores?\s+normal\w*|vn|l[ií]mite)\b|\bprote[ií]n\w*|"
                             # Vuelta 6: un valor «previo» o «anterior» no es el resultado de esta frase.
                             r"\b(previ[oa]s?|anterior(es)?)\b|"
                             # Vuelta 15, V6 (firmada 16 nov 2026, E-42, E-45): límites dichos con palabras.
                             r"\b(menos|m[aá]s)\s+de\s+\d|\bpor\s+(encima|debajo)\s+de\s+\d|\bhasta\s+\d|[‹›]\s*\d", re.I)
# Un mes sin año («del análisis de enero»): no se sabe a qué fecha se refiere la frase → sin fecha.
MES_SIN_ANIO = re.compile(r"\b(" + "|".join(MESES) + r")\b(?!\s+(?:de\s+|del\s+)?\d{4})", re.I)
# Vuelta 7 (revisor en bucle): un CAC alterado dicho con palabras («CAC alterado», «elevado», «en rango A2») o con
# la cifra escrita en letras («ochenta y cinco mg/g»). N1a enmendada: un CAC alterado nunca retira → dudoso.
NUMERO_EN_LETRAS = (r"un[oa]?|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|"
                    r"diecis\w+|veinti?\w*|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|cien|ciento|"
                    r"\w*cientos|\w*cientas|mil")
CAC_ALTERADO_TEXTO = re.compile(
    r"\b(alterad\w*|elevad\w*|alt[oa]s?|positiv\w*|aumentad\w*|patol[oó]gic\w*|anormal\w*|macroalbuminuria|"
    r"a[23]|fuera\s+de\s+rango)\b|"
    rf"\b({NUMERO_EN_LETRAS})\b[\w\s]{{0,30}}?mg\s*/", re.I)
# «CAC con microalbuminuria» sin cifra es un resultado alterado; «informe con microalbuminuria 104 mg/g» nombra la
# prueba y trae su valor. Por eso esta solo cuenta cuando la frase no trae un valor legible.
CON_ALBUMINURIA = re.compile(r"\bcon\s+(micro|macro)?albuminuria\b", re.I)
# Vuelta 8 · N1a firmada de nuevo (Ahmed, 14 nov 2026): un CAC SIN VALOR LEGIBLE solo retira si la frase dice
# «normal», sin negarlo ni matizarlo. Cualquier otra cosa («realizado», «moderado», «no normal», «normal-alto»…) es
# dudosa y no tiene efecto. Una lista de palabras «alteradas» nunca está completa: por eso se invierte la regla.
NORMAL = re.compile(r"\bnormal(es|idad)?\b", re.I)
NORMAL_MATIZADO = re.compile(
    r"\b(no|nada|casi|poco|lo|pero|aunque|ni)\s+(es\s+|est[aá]\s+|era\s+|fue\s+)?(del\s+todo\s+)?normal|"
    r"\bnormal(es)?\s*[-‐–/]\s*\w|\bnormal(es)?\s+(alt|baj|l[ií]m)\w*|\bnormal(es|idad)?\b.{0,60}\b(pero|aunque|salvo|excepto)\b",
    re.I)


# Vuelta 9 (revisor en bucle, ronda 3): «normal» solo cuenta en una FRASE LLANA. Quitadas la prueba, la fecha,
# «normal», «(A1)», «en rango» y estas palabras neutras, no puede quedar nada: ni «según el paciente», ni «parece»,
# ni «¿…?», ni «sin confirmar», ni «y albuminuria». Es la lectura estricta de N1a («normal» sin negar ni matizar).
NEUTRAS = {"trae", "traen", "aporta", "aportan", "aportado", "informe", "informes", "analitica", "analítica", "resultado",
           "resultados", "de", "del", "la", "el", "los", "las", "en", "con", "un", "una", "al", "mutua", "privada", "privado",
           "laboratorio", "empresa", "hospital", "h", "centro", "realizado", "realizada", "realizados", "hecho", "hecha",
           "se", "le", "hizo", "hoy", "esta", "mañana", "manana", "orina", "a1", "rango", "normal", "normales", "normalidad",
           "dentro"}


def dice_normal_limpio(texto: str) -> bool:
    if not NORMAL.search(texto) or NORMAL_MATIZADO.search(texto) or CAC_ALTERADO_TEXTO.search(texto) \
            or CON_ALBUMINURIA.search(texto) or re.search(r"[?¿]", texto):
        return False
    resto = re.sub(r"\bA1\b", " ", NOMBRA["CAC"].sub(" ", NOMBRE_CAC.sub(" ", sin_fechas(texto))), flags=re.I)
    palabras = re.findall(r"[^\W\d_]+|\d+", resto.lower())
    return all(w in NEUTRAS for w in palabras)


MILES = re.compile(r"\b\d{1,3}(?:[.,]\d{3})+(?![\d.,])\s*mg\s*/", re.I)
VALOR_CAC_LIBRE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg\s*/\s*(?:g|mmol))\b", re.I)
# Causas transitorias de albuminuria que KDIGO pide tener en cuenta: con ellas no se habla de persistencia.
TRANSITORIA = re.compile(r"\b(itu|infecci[oó]n\s+(urinaria|de\s+orina)|cistitis|pielonefritis|prostatitis|uretritis|sondaje|sondad\w*|"
                         r"fiebre|febril|febr[ií]cula|ejercicio|menstrua\w*|bacteriuria|sonda\s+vesical|infecci[oó]n\s+del\s+tracto\s+urinario|"
                         r"regla|hematuria|hiperglucemia|descompensad\w*)\b", re.I)
VALOR_FGE = re.compile(r"\b(?:fge?|filtrado(?:\s+glomerular)?)\b\D{0,12}?(\d+(?:[.,]\d+)?)", re.I)
# Vuelta 11 (16 nov, firmada por Ahmed el 16 nov; test con texto real, CodiEsp): «FGe MDRD (Modification of Diet in
# Renal Disease) 34 ml/min/1,73m2». Con la unidad ml/min detrás, el valor puede estar más lejos del nombre (≤60 letras).
VALOR_FGE_UNIDAD = re.compile(r"\b(?:fge?|filtrado(?:\s+glomerular)?)\b\D{0,60}?(\d+(?:[.,]\d+)?)\s*ml\s*/\s*min", re.I)
# Vuelta 11 (firmada 16 nov): µg/mg es la misma cifra que mg/g («Cociente albúmina/creatinina: 0,6µg/mgr»).
MICRO_POR_MG = re.compile(r"(?:µ|μ|mc|u)g\s*/\s*mgr?\b", re.I)
# Vuelta 11 (firmada 16 nov): otra medida de orina en la misma frase («… 261,9 mg/g y proteinuria/creatininuria 1,1»)
# no hace ambiguo el CAC: se quita antes de leerlo. Sin esto, su cifra también podría leerse como un CAC en mg/g.
OTRA_MEDIDA_ORINA = re.compile(r"\bprote[ií]n\w*\s*(?:/\s*creatinin\w*)?\s*(?:de\s+|:\s*)?\d+(?:[.,]\d+)?"
                               r"(?:\s*(?:mg|g)(?:\s*/\s*(?:g|mg|24\s*h|d[ií]a|dl))?)?", re.I)

COMILLAS = str.maketrans({"«": '"', "»": '"', "“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "`": "'"})
# Rechazo y Nefrología: la frase tiene que decirlo (no basta con que el modelo la señale).
DICE_RECHAZO = re.compile(r"\b(rechaz\w*|no\s+(quiere|desea|acepta)|se\s+niega|declina|prefiere\s+no)\b", re.I)
RECHAZO_NEGADO = re.compile(r"\bno\s+(lo\s+|la\s+|le\s+)?rechaz\w*|(?<!\bno\s)\bacepta\b", re.I)
DICE_NEFROLOGIA = re.compile(r"\bnefrolog\w*", re.I)
# Vuelta 11 (16 nov, firmada por Ahmed el 16 nov; test con texto real, CodiEsp: 7 de 14 «Nefrología» aceptados eran una
# derivación, una interconsulta, un diagnóstico o una línea de afiliación). «Seguido en Nefrología» exige que la frase
# diga seguimiento o control; «consultas de Nefrología» cuenta solo si la frase no es una derivación o una valoración.
SEGUIMIENTO = re.compile(r"\b(seguimiento|seguid[oa]s?|segu[ií]an?|control\w*|revisiones)\b", re.I)
EN_CONSULTAS = re.compile(r"\b(consultas?(\s+externas)?|policl[ií]nico|hospital\s+de\s+d[ií]a)\b", re.I)
SOLO_DERIVACION = re.compile(r"\b(derivad[oa]s?|deriva|remitid[oa]s?|remite|env[ií]a\w*|valorad[oa]s?|valoraci[oó]n|"
                             r"interconsulta\w*|consultad[oa]s?|confirma\w*|ingres\w*)\b", re.I)
# Vuelta 13 (Ahmed, 16 nov 2026), N1: la palabra de seguimiento tiene que referirse a Nefrología: misma cláusula (sin
# coma, punto y coma, dos puntos ni paréntesis entre medias) y a 8 palabras o menos. Caso real (CodiEsp, held-out):
# «Se ingresó en Nefrología con … IRA prerrenal, …, reposición hidroelectrolítica controlada» se aceptaba.
SEGUIMIENTO_DISTANCIA = 8


# Vuelta 14 (Ahmed, 16 nov 2026, «Yes, both»): una palabra de ingreso en la misma cláusula anula la de seguimiento
# («Ingresó en Nefrología para control de la tensión arterial» no es seguimiento). Error E-13 (revisión de código).
INGRESO = re.compile(r"\b(ingres\w*|hospitaliz\w*)\b", re.I)


def seguimiento_de_nefrologia(frase: str) -> bool:
    for clausula in re.split(r"[,;:()]", frase):
        if INGRESO.search(clausula):
            continue
        palabras = re.findall(r"\w+", clausula)
        nef = [i for i, w in enumerate(palabras) if DICE_NEFROLOGIA.fullmatch(w)]
        seg = [i for i, w in enumerate(palabras) if SEGUIMIENTO.fullmatch(w)]
        if any(abs(a - b) <= SEGUIMIENTO_DISTANCIA for a in nef for b in seg):
            return True
    return False


# Vuelta 11 (firmada 16 nov): un rechazo cuenta si es de la prueba; «rechazo … a otro tratamiento inmunosupresor» no.
OBJETO_NO_PRUEBA = re.compile(r"\b(tratamiento|medicaci[oó]n|f[aá]rmaco|insulina|cirug[ií]a|intervenci[oó]n|ingreso|"
                              r"transfusi[oó]n|di[aá]lisis|vacuna\w*|biopsia|trasplante|inmunosupresor\w*)\b", re.I)
NOMBRA_PRUEBA = re.compile(r"\b(cac|orina|muestra|anal[ií]tica|an[aá]lisis|prueba|microalbuminuria|albuminuria|cociente|"
                           r"sangre|extracci[oó]n|filtrado|fge?)\b", re.I)

# Fin de frase; «H. La Fe», «Dra. Pérez» o «Sr. Gil» no cortan la frase.
ABREVIATURAS = ("Dr", "Dra", "Sr", "Sra", "Dña", "H", "Hosp", "Gral", "Enf", "aprox", "núm", "pág")
FIN_FRASE = re.compile("".join(rf"(?<!\b{a}(?=\.))" for a in ABREVIATURAS) + r"[.;!?](?=\s+[A-ZÁÉÍÓÚÑ¿¡]|\s*$)")


def normalizar(texto: str) -> str:
    """Solo espacios y comillas: la cita tiene que estar en la nota, palabra por palabra."""
    return " ".join(unicodedata.normalize("NFC", texto).translate(COMILLAS).split())


def frase_de(cita: str, nota: str) -> str:
    """La frase (o frases) de la nota que contienen la cita: ahí se buscan negaciones, planes y otras personas."""
    i = nota.find(cita)
    if i < 0:
        return cita
    inicio = max((m.end() for m in FIN_FRASE.finditer(nota, 0, i)), default=0)
    fin_m = FIN_FRASE.search(nota, i + len(cita))
    return nota[inicio:fin_m.end() if fin_m else len(nota)].strip()


def frases(nota: str) -> List[str]:
    """La nota partida en frases, en orden (mismos cortes que frase_de). El modelo señala una por su número."""
    nota = normalizar(nota)
    trozos, inicio = [], 0
    for fin in [m.end() for m in FIN_FRASE.finditer(nota)] + [len(nota)]:
        trozo = nota[inicio:fin].strip()
        if trozo:
            trozos.append(trozo)
        inicio = fin
    return trozos


def fechas_en(texto: str, note_date: str) -> Tuple[Set[str], bool]:
    """Fechas que encuentra el código (dd/mm/aaaa, d-m-aa, «octubre de 2026» = día 1, «hoy») y si alguna es inválida."""
    encontradas: Set[str] = set()
    invalida = False
    for d, mes, a in FECHA_NUM.findall(texto):
        anio = int(a) + 2000 if len(a) == 2 else int(a)
        try:
            encontradas.add(date(anio, int(mes), int(d)).isoformat())
        except ValueError:
            invalida = True
    for d, nombre, anio in FECHA_DIA_MES.findall(texto):
        try:
            encontradas.add(date(int(anio), MESES[nombre.lower()], int(d)).isoformat())
        except ValueError:
            invalida = True
    for nombre, anio in FECHA_MES.findall(FECHA_DIA_MES.sub(" ", texto)):
        try:
            encontradas.add(date(int(anio), MESES[nombre.lower()], 1).isoformat())
        except ValueError:
            invalida = True
    if HOY_EN_NOTA.search(texto):
        encontradas.add(note_date)
    return encontradas, invalida


def fecha_en_cita(texto: str, note_date: str) -> Optional[str]:
    """Una sola fecha válida y sin intervalo → esa fecha; si no, None (ambigua: no retira nada)."""
    fechas, invalida = fechas_en(texto, note_date)
    if invalida or len(fechas) != 1 or INTERVALO.search(texto) or RELATIVO.search(texto) or MES_SIN_ANIO.search(texto):
        return None
    return next(iter(fechas))


def sin_fechas(texto: str) -> str:
    """Quita las fechas para que sus cifras no se lean como resultados."""
    return FECHA_MES.sub(" ", FECHA_DIA_MES.sub(" ", FECHA_NUM.sub(" ", texto)))


# Vuelta 6: códigos con cifras que no son resultados («DM2», «HbA1c», «E11.9»).
CODIGO_ALFANUMERICO = re.compile(r"\b[^\W\d_]+\d[\w.,]*", re.I)


def _orina(texto: str) -> str:
    """µg/mg → mg/g (misma cifra) y fuera otras medidas de orina (proteinuria…). Vuelta 11, firmada 16 nov."""
    return OTRA_MEDIDA_ORINA.sub(" ", MICRO_POR_MG.sub("mg/g", texto))


# Vuelta 15: V1 (las cifras de otras pruebas con su unidad no bloquean el CAC) NO está firmada: falló tres pruebas
# ciegas (docs/FIRMA_VUELTA_15.md, errores E-42, E-45, E-46, E-47, E-50). Una cifra más en la frase sigue bloqueando.


def cifras_sueltas(texto: str) -> bool:
    """¿Quedan cifras en la frase (sin fechas) tras quitar el FGe, los códigos y los resultados con unidad de CAC?
    «CAC 1 020 mg/g», «CAC 35-20 mg/g» o «cociente … 450 mg/L»: el número no se puede leer con seguridad."""
    resto = VALOR_FGE_UNIDAD.sub(" ", VALOR_FGE.sub(" ", ECUACION.sub(" ", NOMBRE_CAC.sub(" ", _orina(sin_fechas(texto))))))
    resto = VALOR_CAC_LIBRE.sub(" ", CODIGO_ALFANUMERICO.sub(" ", resto))
    return bool(re.search(r"\d", resto))


# Vuelta 15, V5 (firmada 16 nov 2026, amendments 12 y 14): el nombre de la ecuación con su año o número no es el valor
# («FGe CKD-EPI 2021 de 57» se leía 2021; «FG MDRD-4 38»).
# Solo un año (19xx/20xx) o «MDRD-4/-6» con guion: «CKD-EPI 93 ml/min» y «MDRD 45» son valores y se leen.
ECUACION = re.compile(r"\(?\b(?:mdrd-[46]\b|(?:ckd[\s-]*epi|mdrd|cockcroft[\s-]*gault)(?:[\s-]*(?:19|20)\d\d\b)*)\)?", re.I)
OTRA_UNIDAD_TRAS_FGE = re.compile(r"\s*(?:kg|cm|años|%|lpm|mm\s*hg|(?:mg|g|µg|μg|ng|pg|mmol|meq|u|ui)\s*/)", re.I)
# Vuelta 15, V4 (firmada 16 nov 2026): signo o palabra de límite entre el nombre del FGe y la cifra (error E-16).
LIMITE = re.compile(r"[<>≤≥]|&[lg]t;|\b(?:mayor|menor|superior|inferior)\w*\s+(?:a|de|que)\b", re.I)
FGE_LIMITE = re.compile(r"\b(?:fge?|filtrado(?:\s+glomerular)?)\b\D{0,12}?(?:[<>≤≥]|&[lg]t;|\b(?:mayor|menor|superior|"
                        r"inferior)\w*\s+(?:a|de|que)\b)\s*\d", re.I)
# Vuelta 15, V3 (firmada 16 nov 2026): una tira reactiva («albuminuria ++++») o una albúmina de 24 h o en concentración
# («albuminuria, 4.5 g/24 h», «microalbuminuria 25 mg/l») no es un CAC (errores E-14, E-15), salvo que la frase nombre
# el CAC o traiga un resultado en mg/g o mg/mmol.
NO_ES_CAC = re.compile(
    r"\b(?:micro)?alb[uú]min\w*\s*(?:en\s+orina\s*)?:?\s*\+{1,4}|\btira\w*|\+{1,4}\s*(?:de\s+)?(?:micro)?alb[uú]min"
    # V3, amendment 12: the gap may not cross a comma, semicolon or parenthesis («sin microalbuminuria, colesterol 136 mg/dl»).
    # …but a comma right before the number is fine («albuminuria, 4.5 g/24 h», E-15).
    r"|\b(?:micro)?alb[uú]min\w*(?:\s*,\s*(?=\d)|[^.;,()\d]{0,30}?)\d+(?:[.,]\d+)?\s*(?:mg|g)\s*/\s*(?:24\s*h\w*|d[ií]a|l|dl)\b", re.I)


def no_es_cac(frase: str) -> bool:
    frase = MICRO_POR_MG.sub("mg/g", frase)
    return bool(NO_ES_CAC.search(frase)) and not (NOMBRE_CAC.search(frase) or re.search(r"\bcac\b", frase, re.I)
                                                   or VALOR_CAC_LIBRE.search(frase))


def valor_en(cita: str, prueba: str) -> Tuple[Optional[float], Optional[str]]:
    cita = sin_fechas(cita)
    if prueba == "CAC":
        cita = _orina(cita)
        # Revisión de código (14 nov): «1.200 mg/g» o «1,200 mg/g» (miles) no se puede leer con seguridad → dudoso.
        if MILES.search(cita) or VALOR_NO_FIABLE.search(cita) or cifras_sueltas(cita) or CAC_ALTERADO_TEXTO.search(cita):
            return None, None
        valores = {(float(v.replace(",", ".")), re.sub(r"\s+", "", u).lower()) for v, u in VALOR_CAC.findall(cita)}
        valores |= {(float(v.replace(",", ".")), re.sub(r"\s+", "", u).lower()) for v, u in VALOR_CAC_LIBRE.findall(cita)}
        return next(iter(valores)) if len(valores) == 1 else (None, None)   # dos resultados en la cita: ambiguo
    sin_cac = ECUACION.sub(" ", NOMBRE_CAC.sub(" ", cita))
    m = VALOR_FGE.search(sin_cac) or VALOR_FGE_UNIDAD.search(sin_cac)
    if m and LIMITE.search(sin_cac[m.start():m.start(1)]):     # Vuelta 15, V4: «FG > 60» es un límite, no un valor
        return None, None
    if m and OTRA_UNIDAD_TRAS_FGE.match(sin_cac, m.end(1)):    # amendment 14: «Cockcroft-Gault (peso 90 kg) 57»
        return None, None
    return (float(m.group(1).replace(",", ".")), None) if m else (None, None)


def _fila(etiqueta: str, verificada: int, motivo: Optional[str] = None, prueba: Optional[str] = None,
          fecha: Optional[str] = None, cita: Optional[str] = None, valor: Optional[float] = None,
          unidad: Optional[str] = None) -> Dict[str, Any]:
    return {"etiqueta": etiqueta, "prueba": prueba, "fecha_cita": fecha, "cita": cita, "valor": valor,
            "unidad": unidad, "verificada": verificada, "motivo_rechazo": motivo}


def _rechazo(motivo: str, etiqueta: str = "ninguna", cita: Optional[str] = None) -> List[Dict[str, Any]]:
    return [_fila(etiqueta, 0, motivo, cita=cita)]


CLAVES = {"etiqueta", "prueba", "fecha_en_nota", "cita"}          # forma antigua: el modelo copia la cita
CLAVES_FRASE = {"etiqueta", "prueba", "fecha_en_nota", "frase"}   # forma actual: el modelo da el nº de frase
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _forma_valida(salida: Any) -> Optional[str]:
    if not isinstance(salida, dict):
        return "salida no es un objeto JSON"
    if set(salida) not in (CLAVES, CLAVES_FRASE):
        return "claves distintas del esquema"
    if salida.get("etiqueta") not in ETIQUETAS:
        return "etiqueta no válida"
    if "cita" in salida and not isinstance(salida["cita"], str):
        return "falta la cita"
    if salida.get("prueba") not in PRUEBAS | {None, "null", ""}:
        return "prueba no válida"
    pista = salida.get("fecha_en_nota")
    if pista not in (None, "null", ""):
        if not isinstance(pista, str) or not ISO.match(pista):
            return "fecha_en_nota no válida"
        try:
            date.fromisoformat(pista)
        except ValueError:
            return "fecha_en_nota no válida"
    return None


def _pruebas_nombradas(texto: str) -> Set[str]:
    nombradas = {"CAC"} if NOMBRA["CAC"].search(texto) else set()
    if NOMBRA["FGe"].search(NOMBRE_CAC.sub(" ", texto)):
        nombradas.add("FGe")
    return nombradas


def _frase_entera(lista: List[str], k: int) -> str:
    """Los trozos que el divisor separó en «; » + mayúscula, juntos: «CAC 18 mg/g (…); CAC 52 mg/g (…)» es una frase."""
    i = j = k - 1
    while i > 0 and lista[i - 1].rstrip().endswith(";"):
        i -= 1
    while j < len(lista) - 1 and lista[j].rstrip().endswith(";"):
        j += 1
    return " ".join(lista[i:j + 1])


def verificar(note_text: str, note_date: str, salida: Any, hoy: str) -> List[Dict[str, Any]]:
    """Una o más filas para nota_hallazgo. Solo las de verificada = 1 tienen algún efecto."""
    error = _forma_valida(salida)
    if error:
        return _rechazo(error)
    etiqueta = salida["etiqueta"]
    nota = normalizar(note_text)
    if INSTRUCCIONES.search(nota):
        return _rechazo("la nota contiene órdenes para el modelo: no se usa (§5.6)", etiqueta)
    if etiqueta == "ninguna":
        return _rechazo("el modelo no encontró nada")
    if "frase" in salida:
        lista, k = frases(nota), salida["frase"]
        if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= len(lista):
            return _rechazo("la frase señalada no existe en la nota", etiqueta)
        cita = contexto = lista[k - 1]          # la cita la copia el código: no puede tener erratas ni inventos
        if etiqueta == "ya_realizada":          # Vuelta 15, V7 (firmada 16 nov 2026, E-43): la frase entera
            contexto = _frase_entera(lista, k)
    else:
        cita = normalizar(salida["cita"])
        if not cita or cita not in nota:
            return _rechazo("la cita no está en la nota", etiqueta, salida["cita"])
        contexto = frase_de(cita, nota)
    if OTRA_PERSONA.search(contexto):
        return _rechazo("la frase habla de otra persona (N1d)", etiqueta, cita)
    if PERSONA_DUDOSA.search(contexto) and etiqueta in ("rechazo", "nefrologia"):
        return _rechazo("la frase puede hablar de otra persona (familia, pareja…): no retira", etiqueta, cita)
    if etiqueta == "rechazo":
        if not DICE_RECHAZO.search(contexto) or RECHAZO_NEGADO.search(contexto):
            return _rechazo("la frase no dice que rechace la prueba", etiqueta, cita)
        if OBJETO_NO_PRUEBA.search(contexto) and not NOMBRA_PRUEBA.search(contexto):
            return _rechazo("rechaza otra cosa (un tratamiento…), no la prueba", etiqueta, cita)
        return [_fila("rechazo", 1, cita=cita)]
    if etiqueta == "nefrologia":
        if not DICE_NEFROLOGIA.search(contexto):
            return _rechazo("la frase no habla de Nefrología", etiqueta, cita)
        if NO_SEGUIDO.search(contexto):
            return _rechazo("negación (N1d)", etiqueta, cita)
        if not seguimiento_de_nefrologia(contexto) and not (EN_CONSULTAS.search(contexto) and not SOLO_DERIVACION.search(contexto)):
            return _rechazo("la frase no dice que esté en seguimiento por Nefrología (derivación, valoración o mención)",
                            etiqueta, cita)
        return [_fila("nefrologia", 1, cita=cita)]
    filas = _ya_realizada(cita, contexto, note_date, salida, hoy)
    if PERSONA_DUDOSA.search(contexto):
        motivo = "la frase puede hablar de otra persona (familia, pareja…): solo cuenta un CAC alterado"
        filas = [f if f["verificada"] == 0 or _cac_alterado(f) else _fila("ya_realizada", 0, motivo, cita=cita)
                 for f in filas]
    return filas


def _ya_realizada(cita: str, contexto: str, note_date: str, salida: Dict[str, Any], hoy: str) -> List[Dict[str, Any]]:
    if NEGACION.search(contexto):
        return _rechazo("negación, plan o petición en la frase (N1d)", "ya_realizada", cita)
    if NO_ES_RESULTADO.search(contexto):
        return _rechazo("la frase no describe un resultado válido del paciente (invalidado, ejemplo, transcripción)",
                        "ya_realizada", cita)
    nombradas = _pruebas_nombradas(cita)
    prueba = salida.get("prueba") if salida.get("prueba") in PRUEBAS else None
    if "CAC" in nombradas and no_es_cac(contexto):
        if prueba in (None, "CAC") and nombradas == {"CAC"} or prueba == "CAC":
            return _rechazo("no es un CAC: tira reactiva, orina de 24 h o concentración (vuelta 15, V3)", "ya_realizada", cita)
        nombradas = nombradas - {"CAC"}
    if not nombradas or (prueba and prueba not in nombradas):
        return _rechazo("la cita no nombra la prueba (N1a)", "ya_realizada", cita)
    fecha = fecha_en_cita(contexto, note_date)
    pista = salida.get("fecha_en_nota")
    if fecha and pista not in (None, "null", "") and str(pista)[:7] != fecha[:7]:
        return _rechazo("la fecha del modelo no coincide con la de la cita", "ya_realizada", cita)
    if fecha and (fecha > note_date or fecha > hoy):
        return _rechazo("fecha posterior a la nota: no puede estar hecha", "ya_realizada", cita)
    principal = prueba or sorted(nombradas)[0]
    # La otra prueba solo cuenta si la cita trae también su resultado («FGe 60 y CAC 20 mg/g»).
    otras = [p for p in sorted(nombradas - {principal}) if valor_en(cita, p)[0] is not None]
    filas = []
    for p in [principal, *otras]:
        # Bucle 1 (14 nov): el resultado se lee en la FRASE ENTERA, no en la cita del modelo: una cita recortada
        # («Repetido CAC … el 15/09/2026», sin el «45 mg/g» que sigue) no puede esconder un CAC alterado.
        valor, unidad = valor_en(contexto, p)
        fecha_p, observacion = fecha, None
        sin_a1 = re.sub(r"\bA1\b", " ", sin_fechas(contexto))     # «CAC normal (A1)»: la categoría normal no es una cifra
        if p == "CAC" and valor is None and (NUMERO_CAC.search(sin_a1) or VALOR_CAC_LIBRE.search(sin_a1)
                                             or cifras_sueltas(contexto) or not dice_normal_limpio(contexto)):
            fecha_p, observacion = None, "valor del CAC dudoso (sin valor legible ni «normal», sin unidad o con varios resultados)"
        elif p == "CAC" and TRANSITORIA.search(contexto):
            observacion = "posible causa transitoria en la nota"
        elif p == "FGe" and valor is None and FGE_LIMITE.search(ECUACION.sub(" ", sin_fechas(contexto))):
            observacion = "límite, no valor"
        fila = _fila("ya_realizada", 1, prueba=p, fecha=fecha_p, cita=cita, valor=valor, unidad=unidad)
        filas.append({**fila, "motivo_rechazo": observacion})   # en filas verificadas: observación, no rechazo
    return filas
