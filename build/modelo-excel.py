# -*- coding: utf-8 -*-
"""Genera la planilla financiera interactiva de Clima Baires Argentina.

    npm run modelo    →    dist/Modelo-Financiero-Clima-Baires-Argentina_v<version>.xlsx

Los supuestos salen de src/datos.json (la misma fuente que el PDF) y las cifras de
control salen de `node build/financiero.mjs`, para poder comparar lo que calcula
Excel contra lo que calcula el motor del documento.

Requisito duro: la planilla lleva **fórmulas de Excel reales**, no valores volcados.
Si un socio cambia una celda de «Supuestos», todo el libro recalcula solo. Por eso
casi ningún número se escribe: se escribe la fórmula que lo produce.
"""
import json, os, subprocess, sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import LineChart, BarChart, Reference

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = json.load(open(os.path.join(RAIZ, 'src', 'datos.json'), encoding='utf-8'))
FIN = DATOS['financiero']
VERSION = DATOS['meta']['version']
TC = DATOS['cambio']['eur_ars']
N = FIN['meses']

# Cifras de control del motor del PDF, para la hoja de verificación.
MOTOR = json.loads(subprocess.run([os.environ.get('NODE', 'node'), os.path.join(RAIZ, 'build', 'financiero.mjs')],
                                  capture_output=True, text=True, check=True).stdout)

# ---------- identidad visual ----------
AZUL, CELESTE, NAVY = '0058B3', '00A8FC', '00285A'
GRIS, EDITABLE, AMBAR = 'F2F7FC', 'FFF3CD', 'B8860B'

f_titulo = Font(name='Calibri', size=16, bold=True, color=NAVY)
f_h = Font(name='Calibri', size=10, bold=True, color='FFFFFF')
f_b = Font(name='Calibri', size=10, bold=True, color=NAVY)
f_n = Font(name='Calibri', size=10)
f_small = Font(name='Calibri', size=9, color='5A6675')
r_h = PatternFill('solid', fgColor=NAVY)
r_sub = PatternFill('solid', fgColor='D8E6F5')
r_edit = PatternFill('solid', fgColor=EDITABLE)
r_gris = PatternFill('solid', fgColor=GRIS)
borde = Border(*[Side(style='thin', color='DFE7F0')] * 4)

ARS = '"$" #,##0'
ARS2 = '"$" #,##0.00'
EUR = '"€" #,##0'
PCT = '0.0%'
NUM = '#,##0.0'

wb = Workbook()


def hoja(nombre, titulo, anchos):
    ws = wb.create_sheet(nombre)
    ws['A1'] = titulo
    ws['A1'].font = f_titulo
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'B4'
    for i, a in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = a
    return ws


def cabecera(ws, fila, valores, ancho_congelado='B'):
    for i, v in enumerate(valores, start=1):
        c = ws.cell(row=fila, column=i, value=v)
        c.font, c.fill, c.border = f_h, r_h, borde
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.freeze_panes = f'{ancho_congelado}{fila + 1}'


def celda(ws, fila, col, valor, fmt=None, negrita=False, editable=False, fondo=None):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font = f_b if negrita else f_n
    c.border = borde
    if fmt:
        c.number_format = fmt
    if editable:
        c.fill = r_edit
    elif fondo:
        c.fill = PatternFill('solid', fgColor=fondo)
    return c


# =====================================================================
# 1. LÉEME
# =====================================================================
ws = hoja('Léeme', 'Modelo financiero — Clima Baires Argentina', [110])
ws.freeze_panes = None
texto = [
    ('', None),
    (f'Versión {VERSION} · acompaña al «Plan de Acción 30 Días» · TC de referencia {TC:,.0f} ARS/EUR '
     f'({DATOS["cambio"]["tipo"]}, {DATOS["cambio"]["fecha"]})'.replace(',', '.'), f_small),
    ('', None),
    ('Cómo se usa', f_b),
    ('Solo se edita la hoja «Supuestos»: las celdas en amarillo. Todo lo demás son fórmulas que recalculan solas.', f_n),
    ('El resto de las hojas no se toca — si se pisa una fórmula con un número, el modelo deja de ser un modelo.', f_n),
    ('', None),
    ('Convención monetaria', f_b),
    (FIN['convencion'], f_n),
    ('En Argentina los precios de compra y de venta se indexan casi en paralelo, así que el margen porcentual se', f_n),
    ('sostiene y los valores nominales solo agregarían ruido. La conversión a euros es informativa para los socios.', f_n),
    ('', None),
    ('Qué NO hay que creerse', f_b),
    ('La curva de obras/mes es el supuesto más frágil del modelo: es un pronóstico, no un dato verificable.', f_n),
    ('Todo lo demás (márgenes, costos, alícuotas) está anclado en precios de mercado citados en el PDF.', f_n),
    ('Las cifras derivadas son proyecciones sobre supuestos editables, no compromisos.', f_n),
    ('', None),
    ('Hojas del libro', f_b),
    ('Supuestos — lo único editable. Mix de producto, costos, estructura, marketing y obras mes a mes.', f_n),
    ('Unit economics — qué deja cada obra, por categoría y en promedio ponderado.', f_n),
    ('P&L 24 meses — estado de resultados mensual y anual.', f_n),
    ('Flujo de caja — cobros, pagos y saldo mes a mes, con la seña y el descalce del saldo.', f_n),
    ('Break-even — obras/mes necesarias según qué estructura haya que cubrir.', f_n),
    ('Escenarios — conservador / base / optimista, con el selector de la celda Supuestos!B4.', f_n),
    ('Dashboard — las seis cifras que miran los socios, y la curva de caja.', f_n),
    ('Verificación — control cruzado contra el motor de cálculo del PDF.', f_n),
    ('', None),
    ('Cómo se regenera', f_b),
    ('npm run modelo — reconstruye esta planilla desde src/datos.json.', f_n),
    ('npm run build — reconstruye el PDF con las mismas cifras. Los dos leen build/financiero.mjs.', f_n),
]
for i, (t, f) in enumerate(texto, start=2):
    c = ws.cell(row=i, column=1, value=t)
    if f:
        c.font = f
    c.alignment = Alignment(wrap_text=False, vertical='top')

# =====================================================================
# 2. SUPUESTOS  (la única hoja editable)
# =====================================================================
sp = hoja('Supuestos', 'Supuestos — editar solo las celdas en amarillo', [46, 16, 16, 16, 16, 16, 46])
sp.freeze_panes = None
sp['A2'] = 'Cambiá un valor amarillo y todo el libro recalcula. El resto de las hojas son fórmulas.'
sp['A2'].font = f_small

r = 4
celda(sp, r, 1, 'Escenario activo', negrita=True)
sel = celda(sp, r, 2, 'Base', editable=True)
sel.alignment = Alignment(horizontal='center')
dv = DataValidation(type='list', formula1='"%s"' % ','.join(e['nombre'] for e in FIN['escenarios']), allow_blank=False)
sp.add_data_validation(dv)
dv.add(sel)
celda(sp, r, 7, 'Elegir de la lista: cambia obras y ticket de todo el modelo.')
FILA_ESC = r

r += 1
celda(sp, r, 1, 'Tipo de cambio (ARS por EUR)', negrita=True)
celda(sp, r, 2, TC, ARS, editable=True)
celda(sp, r, 7, 'Solo afecta a la lectura en euros; la operación es en pesos.')
FILA_TC = r

# --- multiplicadores de escenario ---
r += 2
celda(sp, r, 1, 'Multiplicadores de escenario', negrita=True, fondo='D8E6F5')
for c in range(2, 8):
    celda(sp, r, c, None, fondo='D8E6F5')
r += 1
cabecera(sp, r, ['Escenario', 'Obras ×', 'Ticket ×', '', '', '', 'Nota'])
sp.freeze_panes = None
FILA_MULT = r + 1
for e in FIN['escenarios']:
    r += 1
    celda(sp, r, 1, e['nombre'])
    celda(sp, r, 2, e['obras_mult'], PCT, editable=True)
    celda(sp, r, 3, e['ticket_mult'], PCT, editable=True)
    celda(sp, r, 7, e.get('nota', ''))
r += 1
celda(sp, r, 1, 'ACTIVO', negrita=True, fondo='D8E6F5')
celda(sp, r, 2, f'=INDEX(B{FILA_MULT}:B{FILA_MULT + 2},MATCH($B${FILA_ESC},$A${FILA_MULT}:$A${FILA_MULT + 2},0))', PCT, negrita=True, fondo='D8E6F5')
celda(sp, r, 3, f'=INDEX(C{FILA_MULT}:C{FILA_MULT + 2},MATCH($B${FILA_ESC},$A${FILA_MULT}:$A${FILA_MULT + 2},0))', PCT, negrita=True, fondo='D8E6F5')
celda(sp, r, 7, 'Lo que usa el resto del libro.', negrita=True, fondo='D8E6F5')
OBRAS_MULT, TICKET_MULT = f'Supuestos!$B${r}', f'Supuestos!$C${r}'

# --- mix de producto ---
r += 2
celda(sp, r, 1, 'Mix de producto y economía de la obra', negrita=True, fondo='D8E6F5')
for c in range(2, 8):
    celda(sp, r, c, None, fondo='D8E6F5')
r += 1
cabecera(sp, r, ['Categoría', 'Peso en el mix', 'Ticket (ARS)', 'Equipo (% del ticket)',
                 'Instalación (ARS)', 'Materiales (ARS)', 'Fuente'])
FILA_MIX = r + 1
for m in FIN['mix']:
    r += 1
    celda(sp, r, 1, m['tipo'])
    celda(sp, r, 2, m['peso'], PCT, editable=True)
    celda(sp, r, 3, m['ticket_ars'], ARS, editable=True)
    celda(sp, r, 4, m['costo_equipo_pct'], PCT, editable=True)
    celda(sp, r, 5, m['instalacion_ars'], ARS, editable=True)
    celda(sp, r, 6, m['materiales_ars'], ARS, editable=True)
    celda(sp, r, 7, m.get('fuente', ''))
FILA_MIX_FIN = r
r += 1
celda(sp, r, 1, 'Control: el mix tiene que sumar 100 %', negrita=True)
celda(sp, r, 2, f'=SUM(B{FILA_MIX}:B{FILA_MIX_FIN})', PCT, negrita=True)
celda(sp, r, 7, f'=IF(ABS(B{r}-1)<0.001,"OK","REVISAR: el mix no suma 100 %")', negrita=True)

# --- costos y alícuotas ---
r += 2
celda(sp, r, 1, 'Costos variables y alícuotas', negrita=True, fondo='D8E6F5')
for c in range(2, 8):
    celda(sp, r, c, None, fondo='D8E6F5')
co = FIN['costos_obra']
vars_ = [
    ('Comisión de cobro (tarjeta / MP)', co['comision_cobro_pct'], PCT, 'Sobre la facturación.'),
    ('Ingresos Brutos (promedio CABA + PBA)', co['iibb_pct'], PCT, 'Encuadre «instalación con provisión de equipo».'),
    ('Costo de adquisición de cliente (CAC)', co['cac_ars'], ARS, 'Pauta dividida por obras cerradas.'),
    ('Seña cobrada al firmar', FIN['cobros']['sena_pct'], PCT, 'Lo que financia la compra del equipo.'),
    ('Días hasta cobrar el saldo', FIN['cobros']['dias_saldo'], NUM, 'Parte del saldo cae en el mes siguiente.'),
    ('Impuesto al cheque (débitos + créditos)', FIN['impuestos']['imp_cheque_pct'], PCT, 'Computable como pago a cuenta de Ganancias (MiPyME).'),
    ('Ganancias — 1er tramo', FIN['impuestos']['ganancias_escala_pct'][0], PCT, 'Escala del art. 73 LIG.'),
    ('Ganancias — límite del 1er tramo', FIN['impuestos']['ganancias_tramo1_ars'], ARS, 'Actualizado por IPC.'),
    ('Ganancias — 2º tramo', FIN['impuestos']['ganancias_escala_pct'][1], PCT, ''),
    ('Ganancias — límite del 2º tramo', FIN['impuestos']['ganancias_tramo2_ars'], ARS, ''),
    ('Ganancias — 3er tramo', FIN['impuestos']['ganancias_escala_pct'][2], PCT, ''),
    ('Costo empleador del 1er técnico', FIN['empleado']['costo_empleador_ars'], ARS, 'Mensual, con cargas y ART.'),
    ('Mes de alta del técnico (1 = primer mes)', FIN['empleado']['mes_alta_indice'] + 1, NUM, 'Poner 99 para no contratar.'),
    ('Capital aportado', DATOS['capital']['total_ars'], ARS, f'€ {DATOS["capital"]["total_eur"]:,}'.replace(',', '.')),
    ('Desembolsos únicos de puesta en marcha', MOTOR['puestaEnMarcha']['ars'], ARS, 'Bloques A y B del presupuesto; salen en el mes 1.'),
]
REF = {}
for nombre, valor, fmt, nota in vars_:
    r += 1
    celda(sp, r, 1, nombre)
    celda(sp, r, 2, valor, fmt, editable=True)
    celda(sp, r, 7, nota)
    REF[nombre] = f'Supuestos!$B${r}'

COMIS, IIBB = REF['Comisión de cobro (tarjeta / MP)'], REF['Ingresos Brutos (promedio CABA + PBA)']
CAC, SENA = REF['Costo de adquisición de cliente (CAC)'], REF['Seña cobrada al firmar']
DIAS_SALDO, CHEQUE = REF['Días hasta cobrar el saldo'], REF['Impuesto al cheque (débitos + créditos)']
G1, GL1 = REF['Ganancias — 1er tramo'], REF['Ganancias — límite del 1er tramo']
G2, GL2 = REF['Ganancias — 2º tramo'], REF['Ganancias — límite del 2º tramo']
G3 = REF['Ganancias — 3er tramo']
EMPL, EMPL_MES = REF['Costo empleador del 1er técnico'], REF['Mes de alta del técnico (1 = primer mes)']
CAPITAL, ARRANQUE = REF['Capital aportado'], REF['Desembolsos únicos de puesta en marcha']
TC_REF = f'Supuestos!$B${FILA_TC}'

# --- estructura fija ---
r += 2
celda(sp, r, 1, 'Estructura fija mensual', negrita=True, fondo='D8E6F5')
for c in range(2, 8):
    celda(sp, r, c, None, fondo='D8E6F5')
FILA_FIJOS = r + 1
for f in FIN['fijos_mensuales_ars']:
    r += 1
    celda(sp, r, 1, f.get('concepto', f.get('item', '')))
    celda(sp, r, 2, f['ars'], ARS, editable=True)
    celda(sp, r, 7, f.get('nota', ''))
FILA_FIJOS_FIN = r
r += 1
celda(sp, r, 1, 'TOTAL ESTRUCTURA / MES', negrita=True)
celda(sp, r, 2, f'=SUM(B{FILA_FIJOS}:B{FILA_FIJOS_FIN})', ARS, negrita=True)
celda(sp, r, 3, f'=B{r}/{TC_REF}', EUR, negrita=True)
FIJOS = f'Supuestos!$B${r}'

# --- series mensuales ---
r += 2
celda(sp, r, 1, 'Series mensuales (24 meses)', negrita=True, fondo='D8E6F5')
for c in range(2, 8):
    celda(sp, r, c, None, fondo='D8E6F5')
r += 1
FILA_SERIE_H = r
celda(sp, r, 1, 'Mes')
for i in range(N):
    celda(sp, r, 2 + i, MOTOR['proyeccion']['meses'][i]['etiqueta'], negrita=True, fondo='D8E6F5')
r += 1
FILA_OBRAS = r
celda(sp, r, 1, 'Obras del mes (antes del escenario)', negrita=True)
for i in range(N):
    celda(sp, r, 2 + i, FIN['obras_mes'][i], NUM, editable=True)
r += 1
FILA_MKT = r
celda(sp, r, 1, 'Marketing del mes (ARS)', negrita=True)
for i in range(N):
    celda(sp, r, 2 + i, FIN['marketing_ars'][i], ARS, editable=True)
for i in range(N):
    sp.column_dimensions[get_column_letter(2 + i)].width = 13

# =====================================================================
# 3. UNIT ECONOMICS
# =====================================================================
ue = hoja('Unit economics', 'Unit economics — qué deja cada obra', [40, 12, 15, 15, 15, 15, 15, 15, 15, 15])
ue['A2'] = 'Todo se calcula desde «Supuestos». La obra tipo es el promedio ponderado por el mix.'
ue['A2'].font = f_small
cabecera(ue, 4, ['Categoría', 'Mix', 'Ticket', 'Equipo', 'Instalación', 'Materiales',
                 'Margen bruto', '% MB', 'Comisión + IIBB', 'Contribución'])
r = 5
FILA_UE = r
for i in range(len(FIN['mix'])):
    m = FILA_MIX + i
    celda(ue, r, 1, f'=Supuestos!A{m}')
    celda(ue, r, 2, f'=Supuestos!B{m}', PCT)
    celda(ue, r, 3, f'=Supuestos!C{m}*{TICKET_MULT}', ARS)
    celda(ue, r, 4, f'=C{r}*Supuestos!D{m}', ARS)
    celda(ue, r, 5, f'=Supuestos!E{m}', ARS)
    celda(ue, r, 6, f'=Supuestos!F{m}', ARS)
    celda(ue, r, 7, f'=C{r}-D{r}-E{r}-F{r}', ARS)
    celda(ue, r, 8, f'=IF(C{r}=0,0,G{r}/C{r})', PCT)
    celda(ue, r, 9, f'=C{r}*({COMIS}+{IIBB})', ARS)
    celda(ue, r, 10, f'=G{r}-I{r}', ARS)
    r += 1
FILA_UE_FIN = r - 1
celda(ue, r, 1, 'OBRA TIPO (promedio ponderado)', negrita=True, fondo='D8E6F5')
celda(ue, r, 2, f'=SUM(B{FILA_UE}:B{FILA_UE_FIN})', PCT, negrita=True, fondo='D8E6F5')
for col in range(3, 11):
    L = get_column_letter(col)
    fmt = PCT if col == 8 else ARS
    f = (f'=IF(C{r}=0,0,G{r}/C{r})' if col == 8
         else f'=SUMPRODUCT(${L}${FILA_UE}:${L}${FILA_UE_FIN},$B${FILA_UE}:$B${FILA_UE_FIN})')
    celda(ue, r, col, f, fmt, negrita=True, fondo='D8E6F5')
FILA_TIPO = r
TICKET_TIPO, CONTRIB_TIPO = f"'Unit economics'!$C${r}", f"'Unit economics'!$J${r}"
EQUIPO_TIPO = f"'Unit economics'!$D${r}"
INST_TIPO, MAT_TIPO = f"'Unit economics'!$E${r}", f"'Unit economics'!$F${r}"

r += 2
celda(ue, r, 1, 'Menos costo de adquisición de cliente (CAC)', negrita=True)
celda(ue, r, 2, f'=-{CAC}', ARS)
r += 1
celda(ue, r, 1, 'CONTRIBUCIÓN NETA POR OBRA TIPO', negrita=True)
celda(ue, r, 2, f'={CONTRIB_TIPO}-{CAC}', ARS, negrita=True)
celda(ue, r, 3, f'=B{r}/{TC_REF}', EUR, negrita=True)
CONTRIB_NETA = f"'Unit economics'!$B${r}"
r += 1
celda(ue, r, 1, 'Seña que se cobra al firmar', negrita=True)
celda(ue, r, 2, f'={TICKET_TIPO}*{SENA}', ARS)
celda(ue, r, 7, '← tiene que alcanzar para pagar el equipo antes de pedirlo', negrita=True)
r += 1
celda(ue, r, 1, 'Costo del equipo de la obra tipo')
celda(ue, r, 2, f'={EQUIPO_TIPO}', ARS)
r += 1
celda(ue, r, 1, 'Colchón de la seña sobre el equipo', negrita=True)
celda(ue, r, 2, f'=B{r - 2}-B{r - 1}', ARS, negrita=True)
celda(ue, r, 7, f'=IF(B{r}>=0,"OK: la seña cubre el equipo","ALERTA: el equipo se financia con capital propio")', negrita=True)

# =====================================================================
# 4. P&L 24 MESES
# =====================================================================
pl = hoja('P&L 24 meses', 'Estado de resultados — 24 meses', [34] + [14] * (N + 2))
pl['A2'] = 'Fórmulas sobre «Supuestos» y «Unit economics». El año 1 son los meses 1-12; el año 2, los 13-24.'
pl['A2'].font = f_small
cab = ['Concepto'] + [MOTOR['proyeccion']['meses'][i]['etiqueta'] for i in range(N)] + ['Año 1', 'Año 2']
cabecera(pl, 4, cab)
COL_A1, COL_A2 = N + 2, N + 3

FILAS_PL = {}


def fila_pl(r, nombre, formula, fmt=ARS, negrita=False, fondo=None, total_signo=1):
    celda(pl, r, 1, nombre, negrita=negrita, fondo=fondo)
    for i in range(N):
        celda(pl, r, 2 + i, formula(i, get_column_letter(2 + i)), fmt, negrita=negrita, fondo=fondo)
    a, b = get_column_letter(2), get_column_letter(13)
    c, d = get_column_letter(14), get_column_letter(N + 1)
    celda(pl, r, COL_A1, f'=SUM({a}{r}:{b}{r})', fmt, negrita=True, fondo=fondo or 'D8E6F5')
    celda(pl, r, COL_A2, f'=SUM({c}{r}:{d}{r})', fmt, negrita=True, fondo=fondo or 'D8E6F5')
    FILAS_PL[nombre] = r
    return r + 1


r = 5
R_OBRAS = r
r = fila_pl(r, 'Obras', lambda i, L: f'=Supuestos!{L}${FILA_OBRAS}*{OBRAS_MULT}', NUM, negrita=True)
R_ING = r
r = fila_pl(r, 'Facturación', lambda i, L: f'={L}{R_OBRAS}*{TICKET_TIPO}')
R_EQ = r
r = fila_pl(r, 'Costo de equipos', lambda i, L: f'=-{L}{R_OBRAS}*{EQUIPO_TIPO}')
R_INST = r
r = fila_pl(r, 'Instalación subcontratada', lambda i, L: f'=-{L}{R_OBRAS}*{INST_TIPO}')
R_MAT = r
r = fila_pl(r, 'Materiales', lambda i, L: f'=-{L}{R_OBRAS}*{MAT_TIPO}')
R_MB = r
r = fila_pl(r, 'MARGEN BRUTO', lambda i, L: f'=SUM({L}{R_ING}:{L}{R_MAT})', negrita=True, fondo='D8E6F5')
R_MBP = r
r = fila_pl(r, '% margen bruto', lambda i, L: f'=IF({L}{R_ING}=0,0,{L}{R_MB}/{L}{R_ING})', PCT)
pl.cell(row=R_MBP, column=COL_A1).value = f'=IF({get_column_letter(COL_A1)}{R_ING}=0,0,{get_column_letter(COL_A1)}{R_MB}/{get_column_letter(COL_A1)}{R_ING})'
pl.cell(row=R_MBP, column=COL_A2).value = f'=IF({get_column_letter(COL_A2)}{R_ING}=0,0,{get_column_letter(COL_A2)}{R_MB}/{get_column_letter(COL_A2)}{R_ING})'
R_COM = r
r = fila_pl(r, 'Comisiones de cobro', lambda i, L: f'=-{L}{R_ING}*{COMIS}')
R_IIBB = r
r = fila_pl(r, 'Ingresos Brutos', lambda i, L: f'=-{L}{R_ING}*{IIBB}')
R_FIJ = r
r = fila_pl(r, 'Estructura fija', lambda i, L: f'=-{FIJOS}')
R_MKT = r
r = fila_pl(r, 'Marketing', lambda i, L: f'=-Supuestos!{L}${FILA_MKT}')
R_EMP = r
r = fila_pl(r, 'Técnico en dependencia', lambda i, L: f'=IF({i + 1}>={EMPL_MES},-{EMPL},0)')
R_RO = r
r = fila_pl(r, 'RESULTADO OPERATIVO', lambda i, L: f'={L}{R_MB}+SUM({L}{R_COM}:{L}{R_EMP})', negrita=True, fondo='D8E6F5')

# Ganancias por la escala progresiva, solo en la columna anual.
r += 1
celda(pl, r, 1, 'Impuesto a las ganancias', negrita=True)
for col in (COL_A1, COL_A2):
    L = get_column_letter(col)
    celda(pl, r, col, f'=-IF({L}{R_RO}<=0,0,IF({L}{R_RO}<={GL1},{L}{R_RO}*{G1},'
                      f'IF({L}{R_RO}<={GL2},{GL1}*{G1}+({L}{R_RO}-{GL1})*{G2},'
                      f'{GL1}*{G1}+({GL2}-{GL1})*{G2}+({L}{R_RO}-{GL2})*{G3})))', ARS, negrita=True, fondo='D8E6F5')
R_IMP = r
celda(pl, r, 2, 'devengado al cierre de cada año')
r += 1
celda(pl, r, 1, 'RESULTADO NETO', negrita=True, fondo='D8E6F5')
for col in (COL_A1, COL_A2):
    L = get_column_letter(col)
    celda(pl, r, col, f'={L}{R_RO}+{L}{R_IMP}', ARS, negrita=True, fondo='D8E6F5')
R_NETO = r
r += 1
celda(pl, r, 1, 'Resultado neto en euros', negrita=True)
for col in (COL_A1, COL_A2):
    L = get_column_letter(col)
    celda(pl, r, col, f'={L}{R_NETO}/{TC_REF}', EUR, negrita=True)
R_NETO_EUR = r

# =====================================================================
# 5. FLUJO DE CAJA
# =====================================================================
fc = hoja('Flujo de caja', 'Flujo de caja mensual', [34] + [15] * (N + 1))
fc['A2'] = ('El cliente paga seña al firmar y saldo al terminar; el mayorista cobra contado. '
            'Ese descalce es lo que consume el capital de trabajo.')
fc['A2'].font = f_small
cabecera(fc, 4, ['Concepto'] + [MOTOR['proyeccion']['meses'][i]['etiqueta'] for i in range(N)])

r = 5
celda(fc, r, 1, 'Saldo inicial', negrita=True)
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f'={CAPITAL}' if i == 0 else f'={get_column_letter(1 + i)}{r + 11}', ARS, negrita=True)
R_SI = r

r += 1
celda(fc, r, 1, 'Cobro de señas del mes')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f"='P&L 24 meses'!{L}{R_ING}*{SENA}", ARS)
R_CS = r
r += 1
celda(fc, r, 1, 'Cobro de saldos del mes')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f"='P&L 24 meses'!{L}{R_ING}*(1-{SENA})*(1-{DIAS_SALDO}/30)", ARS)
R_CSA = r
r += 1
celda(fc, r, 1, 'Cobro de saldos del mes anterior')
for i in range(N):
    L, Lp = get_column_letter(2 + i), get_column_letter(1 + i)
    celda(fc, r, 2 + i, 0 if i == 0 else f"='P&L 24 meses'!{Lp}{R_ING}*(1-{SENA})*({DIAS_SALDO}/30)", ARS)
R_CSP = r
r += 1
celda(fc, r, 1, 'TOTAL COBROS', negrita=True, fondo='D8E6F5')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f'=SUM({L}{R_CS}:{L}{R_CSP})', ARS, negrita=True, fondo='D8E6F5')
R_COB = r

r += 1
celda(fc, r, 1, 'Pagos operativos')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f"=-('P&L 24 meses'!{L}{R_EQ}+'P&L 24 meses'!{L}{R_INST}+'P&L 24 meses'!{L}{R_MAT}"
                        f"+'P&L 24 meses'!{L}{R_COM}+'P&L 24 meses'!{L}{R_IIBB}+'P&L 24 meses'!{L}{R_FIJ}"
                        f"+'P&L 24 meses'!{L}{R_MKT}+'P&L 24 meses'!{L}{R_EMP})", ARS)
R_PO = r
r += 1
celda(fc, r, 1, 'Puesta en marcha (bloques A y B)')
for i in range(N):
    celda(fc, r, 2 + i, f'={ARRANQUE}' if i == 0 else 0, ARS)
R_PM = r
r += 1
celda(fc, r, 1, 'TOTAL PAGOS', negrita=True, fondo='D8E6F5')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f'={L}{R_PO}+{L}{R_PM}', ARS, negrita=True, fondo='D8E6F5')
R_PAG = r

r += 1
celda(fc, r, 1, 'Impuesto al cheque')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f'=({L}{R_COB}+{L}{R_PAG})*{CHEQUE}*0.5', ARS)
R_CHQ = r
r += 1
celda(fc, r, 1, 'Pago de Ganancias (neto de pago a cuenta)')
for i in range(N):
    L = get_column_letter(2 + i)
    if i == 12:
        v = (f"=MAX(0,-'P&L 24 meses'!{get_column_letter(COL_A1)}{R_IMP}-SUM(B{R_CHQ}:M{R_CHQ}))")
    elif i == N - 1:
        v = (f"=MAX(0,-'P&L 24 meses'!{get_column_letter(COL_A2)}{R_IMP}-SUM(N{R_CHQ}:{get_column_letter(N + 1)}{R_CHQ}))")
    else:
        v = 0
    celda(fc, r, 2 + i, v, ARS)
R_GAN = r
r += 1
celda(fc, r, 1, 'FLUJO NETO DEL MES', negrita=True, fondo='D8E6F5')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f'={L}{R_COB}-{L}{R_PAG}-{L}{R_CHQ}-{L}{R_GAN}', ARS, negrita=True, fondo='D8E6F5')
R_NETO_M = r
r += 1
celda(fc, r, 1, 'SALDO FINAL', negrita=True, fondo='D8E6F5')
for i in range(N):
    L = get_column_letter(2 + i)
    celda(fc, r, 2 + i, f'={L}{R_SI}+{L}{R_NETO_M}', ARS, negrita=True, fondo='D8E6F5')
R_SF = r
assert R_SF == R_SI + 11, f'el saldo inicial encadena con R_SI+11; quedó en {R_SF}'

r += 2
celda(fc, r, 1, 'Caja mínima del período', negrita=True)
celda(fc, r, 2, f'=MIN(B{R_SF}:{get_column_letter(N + 1)}{R_SF})', ARS, negrita=True)
CAJA_MIN = f"'Flujo de caja'!$B${r}"
celda(fc, r, 3, f'=INDEX(B4:{get_column_letter(N + 1)}4,MATCH(B{r},B{R_SF}:{get_column_letter(N + 1)}{R_SF},0))')
celda(fc, r, 4, f'=IF(B{r}<0,"ALERTA: el capital no alcanza","OK: la caja nunca se agota")', negrita=True)
r += 1
celda(fc, r, 1, 'Caja al mes 24', negrita=True)
celda(fc, r, 2, f'={get_column_letter(N + 1)}{R_SF}', ARS, negrita=True)
CAJA_FIN = f"'Flujo de caja'!$B${r}"
r += 1
celda(fc, r, 1, 'Recupero del aporte (primer mes con caja ≥ capital)', negrita=True)
celda(fc, r, 2, f'=IFERROR(INDEX(B4:{get_column_letter(N + 1)}4,MATCH(TRUE,INDEX(B{R_SF}:{get_column_letter(N + 1)}{R_SF}>={CAPITAL},0),0)),"no en 24 meses")', negrita=True)
PAYBACK = f"'Flujo de caja'!$B${r}"

# =====================================================================
# 6. BREAK-EVEN
# =====================================================================
be = hoja('Break-even', 'Punto de equilibrio — cuántas obras hay que hacer', [46, 20, 20, 18, 52])
be['A2'] = 'Obras/mes necesarias para cubrir cada nivel de estructura, con la contribución de la obra tipo.'
be['A2'].font = f_small
cabecera(be, 4, ['Escenario de estructura', 'Costo a cubrir / mes', 'Contribución por obra', 'Obras/mes', 'Lectura'])
mkt_valle = f'MIN(Supuestos!B{FILA_MKT}:M{FILA_MKT})'
mkt_pico = f'MAX(Supuestos!B{FILA_MKT}:M{FILA_MKT})'
filas_be = [
    ('Solo estructura fija', f'={FIJOS}', f'={CONTRIB_TIPO}', 'Contador, stack, seguros, autónomos, movilidad y bancarios.'),
    ('Estructura + marketing de valle', f'={FIJOS}+{mkt_valle}', f'={CONTRIB_NETA}', 'Meses de invierno, con la pauta al mínimo.'),
    ('Estructura + marketing de temporada', f'={FIJOS}+{mkt_pico}', f'={CONTRIB_NETA}', 'Pico de diciembre-enero, con la pauta al máximo.'),
    ('… + primer técnico en dependencia', f'={FIJOS}+{mkt_pico}+{EMPL}', f'={CONTRIB_NETA}', 'Costo empleador completo (Rama 17 UOM + cargas + ART).'),
]
r = 5
for nombre, costo, contrib, nota in filas_be:
    celda(be, r, 1, nombre, negrita=True)
    celda(be, r, 2, costo, ARS)
    celda(be, r, 3, contrib, ARS)
    celda(be, r, 4, f'=IF(C{r}<=0,"—",B{r}/C{r})', NUM, negrita=True)
    celda(be, r, 5, nota)
    r += 1
BE_PICO, BE_EMPL = f"'Break-even'!$D$7", f"'Break-even'!$D$8"
r += 1
celda(be, r, 1, 'Facturación de equilibrio / mes (solo estructura)', negrita=True)
celda(be, r, 2, f'=IF({CONTRIB_TIPO}=0,0,{FIJOS}/({CONTRIB_TIPO}/{TICKET_TIPO}))', ARS, negrita=True)
r += 1
celda(be, r, 1, 'Obras mínimas del mes valle proyectado', negrita=True)
celda(be, r, 2, f'=MIN(Supuestos!B{FILA_OBRAS}:M{FILA_OBRAS})*{OBRAS_MULT}', NUM, negrita=True)
celda(be, r, 5, f'=IF(B{r}>={BE_EMPL},"El valle sostiene un técnico en planta",'
                f'"El valle NO sostiene un técnico en planta: subcontratar")', negrita=True)

# =====================================================================
# 7. ESCENARIOS
# =====================================================================
es = hoja('Escenarios', 'Escenarios — comparativa', [40, 22, 22, 22])
es['A2'] = ('Los tres escenarios se calculan cambiando Supuestos!B4. Esta hoja guarda el resultado del escenario '
            'activo en la columna correspondiente; para completarla, seleccioná cada escenario y copiá los valores.')
es['A2'].font = f_small
cabecera(es, 4, ['Métrica', 'Escenario activo', 'Referencia del motor (base)', 'Diferencia'])
metricas = [
    ('Obras año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_OBRAS}", MOTOR['proyeccion']['anios'][0]['obras'], NUM),
    ('Facturación año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_ING}", MOTOR['proyeccion']['anios'][0]['ingresos'], ARS),
    ('Margen bruto año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_MB}", MOTOR['proyeccion']['anios'][0]['margenBruto'], ARS),
    ('Resultado operativo año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_RO}", MOTOR['proyeccion']['anios'][0]['resultadoOperativo'], ARS),
    ('Resultado neto año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_NETO}", MOTOR['proyeccion']['anios'][0]['resultadoNeto'], ARS),
    ('Resultado neto año 2', f"='P&L 24 meses'!{get_column_letter(COL_A2)}{R_NETO}", MOTOR['proyeccion']['anios'][1]['resultadoNeto'], ARS),
    ('Caja mínima', f'={CAJA_MIN}', MOTOR['caja']['minimo']['saldo'], ARS),
    ('Caja al mes 24', f'={CAJA_FIN}', MOTOR['caja']['saldoFinal'], ARS),
]
r = 5
FILA_ES = r
for nombre, formula, ref, fmt in metricas:
    celda(es, r, 1, nombre, negrita=True)
    celda(es, r, 2, formula, fmt)
    celda(es, r, 3, ref, fmt)
    celda(es, r, 4, f'=IF(C{r}=0,0,(B{r}-C{r})/C{r})', PCT)
    r += 1
r += 1
celda(es, r, 1, 'Escenario activo', negrita=True)
celda(es, r, 2, f'=Supuestos!B{FILA_ESC}', negrita=True)
# SUMPRODUCT en vez de MAX(ABS(...)): evita la fórmula matricial, que sin Ctrl+Mayús+Enter da #VALUE!
celda(es, r, 4, f'=IF(Supuestos!B{FILA_ESC}="Base",IF(SUMPRODUCT(MAX(ABS(D{FILA_ES}:D{FILA_ES + 7})))<0.005,'
                f'"OK: coincide con el motor del PDF","REVISAR: diverge del motor"),'
                f'"Cambiá a «Base» para contrastar contra el motor")', negrita=True)

# =====================================================================
# 8. DASHBOARD
# =====================================================================
db = hoja('Dashboard', 'Dashboard — las cifras que miran los socios', [42, 24, 24, 42])
db.freeze_panes = None
db['A2'] = 'Todo se mueve con el escenario elegido en Supuestos!B4 y con las series mensuales.'
db['A2'].font = f_small
kpis = [
    ('Escenario activo', f'=Supuestos!B{FILA_ESC}', None, 'Cambiar en la hoja «Supuestos».'),
    ('Obras del año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_OBRAS}", NUM, 'Suma de los primeros 12 meses.'),
    ('Facturación del año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_ING}", ARS, ''),
    ('Margen bruto del año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_MBP}", PCT, 'Después de equipo, instalación y materiales.'),
    ('Resultado neto del año 1', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_NETO}", ARS, ''),
    ('Resultado neto del año 1 (EUR)', f"='P&L 24 meses'!{get_column_letter(COL_A1)}{R_NETO_EUR}", EUR, 'Al TC de la hoja «Supuestos».'),
    ('Resultado neto del año 2 (EUR)', f"='P&L 24 meses'!{get_column_letter(COL_A2)}{R_NETO_EUR}", EUR, ''),
    ('Caja mínima del período', f'={CAJA_MIN}', ARS, 'Si es negativa, el capital no alcanza.'),
    ('Caja al mes 24', f'={CAJA_FIN}', ARS, ''),
    ('Recupero del aporte', f'={PAYBACK}', None, 'Primer mes con caja ≥ capital aportado.'),
    ('Contribución por obra tipo', f'={CONTRIB_TIPO}', ARS, 'Antes del CAC.'),
    ('Break-even en temporada', f'={BE_PICO}', NUM, 'Obras/mes con la pauta al máximo.'),
    ('Break-even con técnico en planta', f'={BE_EMPL}', NUM, 'La razón para subcontratar.'),
]
r = 4
for nombre, formula, fmt, nota in kpis:
    celda(db, r, 1, nombre, negrita=True, fondo=GRIS)
    celda(db, r, 2, formula, fmt, negrita=True)
    celda(db, r, 4, nota)
    r += 1

r += 1
celda(db, r, 1, 'Curva de caja y resultado operativo', negrita=True)
graf_fila = r + 1
# datos auxiliares para el gráfico (mismas fórmulas, en vertical)
celda(db, graf_fila, 1, 'Mes', negrita=True)
celda(db, graf_fila, 2, 'Saldo de caja', negrita=True)
celda(db, graf_fila, 3, 'Resultado operativo', negrita=True)
for i in range(N):
    L = get_column_letter(2 + i)
    celda(db, graf_fila + 1 + i, 1, f"='Flujo de caja'!{L}4")
    celda(db, graf_fila + 1 + i, 2, f"='Flujo de caja'!{L}{R_SF}", ARS)
    celda(db, graf_fila + 1 + i, 3, f"='P&L 24 meses'!{L}{R_RO}", ARS)

ch = LineChart()
ch.title = 'Saldo de caja (ARS)'
ch.height, ch.width = 8, 22
ch.add_data(Reference(db, min_col=2, min_row=graf_fila, max_row=graf_fila + N), titles_from_data=True)
ch.set_categories(Reference(db, min_col=1, min_row=graf_fila + 1, max_row=graf_fila + N))
db.add_chart(ch, 'F4')

ch2 = BarChart()
ch2.title = 'Resultado operativo mensual (ARS)'
ch2.height, ch2.width = 8, 22
ch2.add_data(Reference(db, min_col=3, min_row=graf_fila, max_row=graf_fila + N), titles_from_data=True)
ch2.set_categories(Reference(db, min_col=1, min_row=graf_fila + 1, max_row=graf_fila + N))
db.add_chart(ch2, 'F22')

# =====================================================================
# 9. VERIFICACIÓN
# =====================================================================
vf = hoja('Verificación', 'Verificación — Excel contra el motor del PDF', [46, 24, 24, 18, 40])
vf.freeze_panes = None
vf['A2'] = ('Con los supuestos originales y el escenario en «Base», estas dos columnas coinciden al centavo: '
            'es la prueba de que la planilla y el PDF cuentan lo mismo. En cuanto se edita un supuesto la '
            'planilla se separa del PDF a propósito — ahí «HAY DIVERGENCIAS» significa «estás modelando algo '
            'distinto de lo publicado», no que haya un error.')
vf['A2'].font = f_small
cabecera(vf, 4, ['Cifra de control', 'Planilla', 'Motor del PDF', 'Desvío', 'Estado'])
r = 5
for nombre, formula, ref, fmt in metricas:
    celda(vf, r, 1, nombre, negrita=True)
    celda(vf, r, 2, formula, fmt)
    celda(vf, r, 3, ref, fmt)
    celda(vf, r, 4, f'=IF(C{r}=0,0,(B{r}-C{r})/C{r})', PCT)
    celda(vf, r, 5, f'=IF(ABS(D{r})<0.005,"OK","REVISAR")', negrita=True)
    r += 1
celda(vf, r, 1, 'Contribución por obra tipo', negrita=True)
celda(vf, r, 2, f'={CONTRIB_TIPO}', ARS)
celda(vf, r, 3, MOTOR['unitEconomics']['blended']['contribucion'], ARS)
celda(vf, r, 4, f'=IF(C{r}=0,0,(B{r}-C{r})/C{r})', PCT)
celda(vf, r, 5, f'=IF(ABS(D{r})<0.005,"OK","REVISAR")', negrita=True)
r += 1
celda(vf, r, 1, 'Break-even en temporada (obras/mes)', negrita=True)
celda(vf, r, 2, f'={BE_PICO}', NUM)
celda(vf, r, 3, MOTOR['breakEven']['conMarketingPico'], NUM)
celda(vf, r, 4, f'=IF(C{r}=0,0,(B{r}-C{r})/C{r})', PCT)
celda(vf, r, 5, f'=IF(ABS(D{r})<0.005,"OK","REVISAR")', negrita=True)
r += 2
celda(vf, r, 1, 'RESULTADO GLOBAL', negrita=True, fondo='D8E6F5')
celda(vf, r, 2, f'=IF(COUNTIF(E5:E{r - 2},"REVISAR")=0,"OK — planilla y PDF cuentan lo mismo",'
                f'"La planilla ya no refleja el PDF (esperable si editaste supuestos)")', negrita=True, fondo='D8E6F5')

del wb['Sheet']
salida = os.path.join(RAIZ, 'dist', f'Modelo-Financiero-Clima-Baires-Argentina_v{VERSION}.xlsx')
os.makedirs(os.path.dirname(salida), exist_ok=True)
wb.save(salida)
print(f'OK  {salida}')
print(f'    {len(wb.sheetnames)} hojas · {N} meses · escenario base del motor: '
      f'neto año 1 $ {MOTOR["proyeccion"]["anios"][0]["resultadoNeto"]:,.0f}'.replace(',', '.'))
