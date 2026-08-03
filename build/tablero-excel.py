# -*- coding: utf-8 -*-
"""Genera el tablero semanal de gestión de Clima Baires Argentina.

    npm run tablero    →    dist/Tablero-Semanal-Clima-Baires_v<version>.xlsx

Los KPI del plan viven impresos en tres secciones del PDF, y nadie gestiona desde
un PDF. Esto es el instrumento: Ignacio carga **seis números por semana** y el resto
son fórmulas con semáforos.

Los objetivos no se escriben a mano: se vuelcan desde `build/marketing.mjs` y
`build/financiero.mjs`, para que el tablero no pueda pedirle un CAC distinto del
que dice el plan.
"""
import json, os, subprocess

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import LineChart, Reference

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = json.load(open(os.path.join(RAIZ, 'src', 'datos.json'), encoding='utf-8'))
VERSION = DATOS['meta']['version']
TC = DATOS['cambio']['eur_ars']
NODE = os.environ.get('NODE', 'node')

# Objetivos, calculados por los mismos motores que alimentan el documento.
MK = json.loads(subprocess.run([NODE, os.path.join(RAIZ, 'build', 'marketing.mjs')],
                               capture_output=True, text=True, check=True).stdout)
OBJ_CPL = MK['embudo']['totales']['cpl']
OBJ_CAC = MK['embudo']['totales']['cac']
TECHO_CPL = MK['sensibilidad'][1]['cpl']
TECHO_CAC = DATOS['financiero']['costos_instalacion']['cac_ars']

SEMANAS = 26  # medio año de carga: de septiembre al pico

AZUL, NAVY, GRIS, EDITABLE = '0058B3', '00285A', 'F2F7FC', 'FFF3CD'
VERDE, AMBAR_F, ROJO = 'C6EFCE', 'FFEB9C', 'FFC7CE'

f_titulo = Font(name='Calibri', size=16, bold=True, color=NAVY)
f_h = Font(name='Calibri', size=10, bold=True, color='FFFFFF')
f_b = Font(name='Calibri', size=10, bold=True, color=NAVY)
f_n = Font(name='Calibri', size=10)
f_small = Font(name='Calibri', size=9, color='5A6675')
r_h = PatternFill('solid', fgColor=NAVY)
r_edit = PatternFill('solid', fgColor=EDITABLE)
borde = Border(*[Side(style='thin', color='DFE7F0')] * 4)

ARS, PCT, NUM = '"$" #,##0', '0 %', '#,##0'

wb = Workbook()


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
# LÉEME
# =====================================================================
ws = wb.active
ws.title = 'Léeme'
ws.column_dimensions['A'].width = 108
ws.sheet_view.showGridLines = False
ws['A1'] = 'Tablero semanal — Clima Baires Argentina'
ws['A1'].font = f_titulo
texto = [
    ('', None),
    (f'Versión {VERSION} · acompaña al «Plan de Negocio» · se llena los lunes, en 20 minutos', f_small),
    ('', None),
    ('Cómo se usa', f_b),
    ('Cada lunes, en la hoja «Carga semanal», completá las seis columnas amarillas de la semana que terminó.', f_n),
    ('Todo lo demás se calcula solo, y las celdas se pintan de verde, amarillo o rojo según el objetivo.', f_n),
    ('', None),
    ('Los seis números', f_b),
    ('1. Leads: cuántas personas escribieron o llamaron pidiendo presupuesto.', f_n),
    ('2. Presupuestos enviados: de esos leads, a cuántos les mandaste un presupuesto.', f_n),
    ('3. Instalaciones cerradas: cuántos aceptaron y señaron.', f_n),
    ('4. Facturación: lo facturado en la semana, con IVA.', f_n),
    ('5. Gasto de pauta: lo gastado en Google y Meta esa semana.', f_n),
    ('6. Reseñas nuevas: cuántas reseñas de Google entraron.', f_n),
    ('', None),
    ('Los objetivos salen del plan, no de acá', f_b),
    (f'CPL objetivo $ {OBJ_CPL:,.0f} · alarma en $ {TECHO_CPL:,.0f}'.replace(',', '.'), f_n),
    (f'CAC objetivo $ {OBJ_CAC:,.0f} · techo tolerable $ {TECHO_CAC:,.0f}'.replace(',', '.'), f_n),
    ('Lead → presupuesto ≥ 60 % · Presupuesto → instalación ≥ 40 % (sección 21.7 del plan)', f_n),
    ('Los calculan build/marketing.mjs y el modelo financiero: si cambian ahí, cambian acá.', f_small),
    ('', None),
    ('Qué hacer cuando algo se pone rojo', f_b),
    ('CPL alto dos semanas seguidas → se corta el canal más caro, no se sube el presupuesto.', f_n),
    ('Lead → presupuesto bajo → el problema es la velocidad de respuesta, no el precio.', f_n),
    ('Presupuesto → instalación bajo → revisar el guion de venta de la sección 21 antes de tocar el precio.', f_n),
    ('Presupuesto → instalación por encima del 70 % → el precio está bajo.', f_n),
    ('', None),
    ('El primer lunes de cada mes', f_b),
    ('Además de cargar la semana, se miran los disparadores del plan B (sección 11.2).', f_n),
]
for i, (t, f) in enumerate(texto, start=2):
    c = ws.cell(row=i, column=1, value=t)
    if f:
        c.font = f
    c.alignment = Alignment(vertical='top')

# =====================================================================
# CARGA SEMANAL
# =====================================================================
cs = wb.create_sheet('Carga semanal')
cs.sheet_view.showGridLines = False
cs['A1'] = 'Carga semanal — completar solo las columnas amarillas'
cs['A1'].font = f_titulo
cs['A2'] = 'Cada lunes, los números de la semana que terminó. El resto son fórmulas.'
cs['A2'].font = f_small

CAB = ['Semana (lunes)', 'Leads', 'Presupuestos\nenviados', 'Instalaciones\ncerradas',
       'Facturación', 'Gasto de\npauta', 'Reseñas\nnuevas',
       'CPL', 'CAC', 'Lead →\npresupuesto', 'Presupuesto →\ninstalación', 'Ticket medio']
anchos = [16, 9, 12, 12, 15, 13, 10, 13, 13, 13, 14, 15]
for i, a in enumerate(anchos, start=1):
    cs.column_dimensions[get_column_letter(i)].width = a

FILA_CAB = 4
for i, v in enumerate(CAB, start=1):
    c = cs.cell(row=FILA_CAB, column=i, value=v)
    c.font, c.fill, c.border = f_h, r_h, borde
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
cs.freeze_panes = f'B{FILA_CAB + 1}'

F0 = FILA_CAB + 1
for i in range(SEMANAS):
    r = F0 + i
    celda(cs, r, 1, None, 'dd/mm/yyyy', editable=True)
    for col in range(2, 8):
        celda(cs, r, col, None, ARS if col in (5, 6) else NUM, editable=True)
    # Los IFERROR no son decorativos: con la hoja vacía, todas estas divisiones son por cero.
    celda(cs, r, 8,  f'=IFERROR(F{r}/B{r},"")', ARS)
    celda(cs, r, 9,  f'=IFERROR(F{r}/D{r},"")', ARS)
    celda(cs, r, 10, f'=IFERROR(C{r}/B{r},"")', PCT)
    celda(cs, r, 11, f'=IFERROR(D{r}/C{r},"")', PCT)
    celda(cs, r, 12, f'=IFERROR(E{r}/D{r},"")', ARS)

FIN = F0 + SEMANAS - 1
celda(cs, FIN + 1, 1, 'TOTAL', negrita=True, fondo='D8E6F5')
for col in range(2, 8):
    L = get_column_letter(col)
    celda(cs, FIN + 1, col, f'=SUM({L}{F0}:{L}{FIN})', ARS if col in (5, 6) else NUM, negrita=True, fondo='D8E6F5')
for col, f in ((8, f'=IFERROR(F{FIN + 1}/B{FIN + 1},"")'), (9, f'=IFERROR(F{FIN + 1}/D{FIN + 1},"")'),
               (10, f'=IFERROR(C{FIN + 1}/B{FIN + 1},"")'), (11, f'=IFERROR(D{FIN + 1}/C{FIN + 1},"")'),
               (12, f'=IFERROR(E{FIN + 1}/D{FIN + 1},"")')):
    celda(cs, FIN + 1, col, f, PCT if col in (10, 11) else ARS, negrita=True, fondo='D8E6F5')

# Semáforos. El orden importa: la primera regla que se cumple es la que pinta.
def semaforo(rango, bueno, malo, sentido='menor'):
    """`menor`: valores bajos son buenos (CPL, CAC). `mayor`: al revés (conversión)."""
    if sentido == 'menor':
        cs.conditional_formatting.add(rango, CellIsRule(operator='greaterThan', formula=[str(malo)], fill=PatternFill('solid', bgColor=ROJO)))
        cs.conditional_formatting.add(rango, CellIsRule(operator='greaterThan', formula=[str(bueno)], fill=PatternFill('solid', bgColor=AMBAR_F)))
        cs.conditional_formatting.add(rango, CellIsRule(operator='lessThanOrEqual', formula=[str(bueno)], fill=PatternFill('solid', bgColor=VERDE)))
    else:
        cs.conditional_formatting.add(rango, CellIsRule(operator='lessThan', formula=[str(malo)], fill=PatternFill('solid', bgColor=ROJO)))
        cs.conditional_formatting.add(rango, CellIsRule(operator='lessThan', formula=[str(bueno)], fill=PatternFill('solid', bgColor=AMBAR_F)))
        cs.conditional_formatting.add(rango, CellIsRule(operator='greaterThanOrEqual', formula=[str(bueno)], fill=PatternFill('solid', bgColor=VERDE)))

semaforo(f'H{F0}:H{FIN}', round(OBJ_CPL), round(TECHO_CPL))
semaforo(f'I{F0}:I{FIN}', round(OBJ_CAC), round(TECHO_CAC))
semaforo(f'J{F0}:J{FIN}', 0.60, 0.45, 'mayor')
semaforo(f'K{F0}:K{FIN}', 0.40, 0.30, 'mayor')

celda(cs, FIN + 3, 1, 'Objetivos (del plan, no editar)', negrita=True)
for i, (nombre, valor, fmt) in enumerate([
        ('CPL objetivo', OBJ_CPL, ARS), ('CPL alarma', TECHO_CPL, ARS),
        ('CAC objetivo', OBJ_CAC, ARS), ('CAC techo', TECHO_CAC, ARS),
        ('Lead → presupuesto', 0.60, PCT), ('Presupuesto → instalación', 0.40, PCT)]):
    celda(cs, FIN + 4 + i, 1, nombre)
    celda(cs, FIN + 4 + i, 2, valor, fmt, negrita=True)

# =====================================================================
# EVOLUCIÓN
# =====================================================================
ev = wb.create_sheet('Evolución')
ev.sheet_view.showGridLines = False
ev['A1'] = 'Evolución — se dibuja sola a medida que se carga'
ev['A1'].font = f_titulo
ev['A2'] = 'Si una curva no aparece es porque esa columna todavía está vacía.'
ev['A2'].font = f_small

ch = LineChart()
ch.title = 'Leads, presupuestos e instalaciones por semana'
ch.height, ch.width = 9, 24
ch.add_data(Reference(cs, min_col=2, max_col=4, min_row=FILA_CAB, max_row=FIN), titles_from_data=True)
ch.set_categories(Reference(cs, min_col=1, min_row=F0, max_row=FIN))
ev.add_chart(ch, 'A4')

ch2 = LineChart()
ch2.title = 'Costo por lead y costo por instalación'
ch2.height, ch2.width = 9, 24
ch2.add_data(Reference(cs, min_col=8, max_col=9, min_row=FILA_CAB, max_row=FIN), titles_from_data=True)
ch2.set_categories(Reference(cs, min_col=1, min_row=F0, max_row=FIN))
ev.add_chart(ch2, 'A24')

salida = os.path.join(RAIZ, 'dist', f'Tablero-Semanal-Clima-Baires_v{VERSION}.xlsx')
os.makedirs(os.path.dirname(salida), exist_ok=True)
wb.save(salida)
print(f'OK  {salida}')
print(f'    {SEMANAS} semanas de carga · CPL objetivo $ {OBJ_CPL:,.0f} · CAC objetivo $ {OBJ_CAC:,.0f}'.replace(',', '.'))
