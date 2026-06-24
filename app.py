# =============================================================================
# PANEL DE CONTROL — QUIEBRA MTD
# =============================================================================
# Descripción : Dashboard interactivo para análisis de quiebra mensual (MTD)
#               dirigido al COO. Permite identificar rápidamente las causas
#               raíz del problema de quiebra por división, región, DM y tienda.
#
# Fuentes de datos:
#   - Quiebra_MTD.xlsx     : Exportado diariamente desde SAP BusinessObjects
#   - Objetivos_Quiebra.xlsx: Parámetros de objetivos mensuales (actualización mensual)
#   Ambos archivos están almacenados en Google Drive (privado).
#
# Estructura del dashboard:
#   Pestaña 1 — Resumen    : KPIs globales + tabla flash Top 3 divisiones/regiones/DMs
#   Pestaña 2 — Divisiones : Detalle y gráficos por categoría de producto
#   Pestaña 3 — Regiones   : Detalle y gráficos por región geográfica
#   Pestaña 4 — DM & Tiendas: Detalle por District Manager y tiendas críticas
#
# Tecnologías : Python 3.12 · Streamlit · Plotly · Pandas · gdown
# Repositorio : github.com/operaciones-transformacion/dashboard-quiebra
# =============================================================================

import streamlit as st
import pandas as pd
import gdown
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# Debe ser el primer comando de Streamlit en ejecutarse.
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Panel de Control — Quiebra MTD",
    page_icon="📊",
    layout="wide",                    # Usa todo el ancho de la pantalla
    initial_sidebar_state="expanded"  # Sidebar abierto por defecto
)

# -----------------------------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS
# Se inyecta CSS directamente en la app para lograr un diseño corporativo limpio.
# Paleta: fondo #F7F8FA (gris claro), sidebar #1A2540 (azul marino), 
#         rojo #E03131 para críticos, verde #2F9E44 para OK.
# -----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Fuente global */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* Fondo principal gris muy claro */
.main { background-color: #F7F8FA; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; max-width: 100% !important; }

/* Sidebar azul marino oscuro */
section[data-testid="stSidebar"] {
    background: #1A2540 !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: #E8EDF5 !important; }
section[data-testid="stSidebar"] .stSelectbox label { 
    color: #9BAAC7 !important; font-size: 11px !important; 
    text-transform: uppercase; letter-spacing: .06em; 
}
section[data-testid="stSidebar"] .stMultiSelect label { 
    color: #9BAAC7 !important; font-size: 11px !important; 
    text-transform: uppercase; letter-spacing: .06em; 
}

/* Tarjetas KPI — fondo blanco con borde sutil */
.kpi-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    border: 1px solid #EAEDF2;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
    margin-bottom: 4px;
}
.kpi-label { 
    font-size: 11px; font-weight: 500; color: #8A93A6; 
    text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; 
}
.kpi-value { font-size: 26px; font-weight: 700; line-height: 1.1; }
.kpi-note  { font-size: 11px; color: #8A93A6; margin-top: 4px; }

/* Colores semánticos para valores */
.kpi-red   { color: #E03131; }  /* Fuera de objetivo — crítico  */
.kpi-green { color: #2F9E44; }  /* En objetivo — OK             */
.kpi-blue  { color: #1971C2; }  /* Informativo / neutro         */

/* Tarjetas de sección (contenedores de gráficos y tablas) */
.section-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #EAEDF2;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
    margin-bottom: 1rem;
}
.section-title {
    font-size: 11px; font-weight: 600; color: #8A93A6;
    text-transform: uppercase; letter-spacing: .06em;
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 1px solid #F0F2F5;
}

/* Filas de la tabla flash (resumen ejecutivo) */
.flash-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: 7px 0; border-bottom: 1px solid #F5F6F8;
}
.flash-item:last-child { border-bottom: none; }
.flash-name { font-size: 12px; font-weight: 500; color: #1A2540; }
.flash-val  { font-size: 12px; font-weight: 600; }
.flash-sub  { font-size: 10px; color: #8A93A6; }

/* Puntos de color para indicar estado */
.dot-red   { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #E03131; margin-right: 6px; }
.dot-green { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #2F9E44; margin-right: 6px; }
.dot-amber { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #E67700; margin-right: 6px; }

/* Píldoras de zona geográfica */
.zona-pill      { display: inline-block; font-size: 9px; padding: 2px 7px; border-radius: 20px; font-weight: 600; margin-left: 4px; }
.zona-norte     { background: #FFF3BF; color: #7F6000; }
.zona-centro    { background: #E7F5FF; color: #1864AB; }
.zona-occidente { background: #FFF0F6; color: #862E9C; }
.zona-antioquia { background: #EBFBEE; color: #1B4332; }

/* Badges de estado */
.badge-red   { background: #FFF5F5; color: #C92A2A; font-size: 10px; padding: 2px 7px; border-radius: 20px; font-weight: 600; border: 1px solid #FFE3E3; }
.badge-green { background: #F4FCF7; color: #1B4332; font-size: 10px; padding: 2px 7px; border-radius: 20px; font-weight: 600; border: 1px solid #D3F9D8; }

/* Encabezado principal del dashboard */
.dash-header { 
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.2rem; padding-bottom: .8rem;
    border-bottom: 1px solid #EAEDF2;
}
.dash-title { font-size: 20px; font-weight: 700; color: #1A2540; }
.dash-sub   { font-size: 12px; color: #8A93A6; margin-top: 2px; }

/* Pestañas de navegación */
.stTabs [data-baseweb="tab-list"] {
    background: transparent; gap: 4px; border-bottom: 2px solid #EAEDF2;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 8px 8px 0 0;
    padding: 8px 18px; font-size: 13px; font-weight: 500;
    color: #8A93A6; border: none;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important; color: #1A2540 !important;
    border-bottom: 2px solid #1971C2 !important; font-weight: 600;
}

/* Tablas de datos */
div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
.stDataFrame { border: 1px solid #EAEDF2 !important; }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CARGA DE DATOS DESDE GOOGLE DRIVE
# -----------------------------------------------------------------------------
# Los archivos están en Google Drive privado. Se accede con gdown usando
# los IDs de los archivos (parte de la URL de Drive).
#
# IDs de los archivos:
#   BO (datos reales diarios)  : 1i2a0XaB9hR8o9Kk0lCCEWx7O1uTF5dvx
#   Objetivos (mensual)        : 1hDJaYJ6bu8uiRr4RFp1tyRNHqu-oQifc
#
# @st.cache_data(ttl=3600): cachea los datos por 1 hora para no descargar
# en cada interacción del usuario. Para forzar actualización usar el botón
# "Actualizar datos" en el sidebar.
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    """
    Descarga y procesa todos los archivos de datos desde Google Drive.
    
    Retorna:
        divisiones  : DataFrame con quiebra por división de producto
        regiones    : DataFrame con quiebra por región geográfica
        dm          : DataFrame con quiebra por District Manager
        tiendas     : DataFrame con quiebra por tienda (nivel más granular)
        am          : DataFrame con quiebra por Area Manager
        obj_div     : DataFrame con objetivos de quiebra por división
        obj_reg     : DataFrame con objetivos de quiebra por región
        obj_dm      : DataFrame con objetivos de quiebra por DM
        obj_tiendas : DataFrame con objetivos de quiebra por tienda
    """
    # URLs de descarga directa desde Google Drive
    url_bo  = "https://drive.google.com/uc?id=1i2a0XaB9hR8o9Kk0lCCEWx7O1uTF5dvx"
    url_obj = "https://drive.google.com/uc?id=1hDJaYJ6bu8uiRr4RFp1tyRNHqu-oQifc"

    # Descarga los archivos a rutas temporales en el servidor
    gdown.download(url_bo,  '/tmp/bo.xlsx',  quiet=True, fuzzy=True)
    gdown.download(url_obj, '/tmp/obj.xlsx', quiet=True, fuzzy=True)

    # ── HOJA: DIVISIONES JMC ──────────────────────────────────────────────────
    # Contiene quiebra agregada por división de producto (Fruta, Carne, etc.)
    # El encabezado real está en la fila 3 del Excel (índice 2), se salta con header=2.
    # Se filtran filas vacías, totales y la fila de encabezado duplicada.
    divisiones = pd.read_excel('/tmp/bo.xlsx', sheet_name='DIVISIONES JMC', header=2)
    divisiones.columns = [
        'Cod Division', 'Desc Division', 'Ventas Real', 'Ventas Historico',
        'Quiebra Real', 'Quiebra Pct Real', 'Quiebra Historico',
        'Quiebra Pct Historico', 'Dif Quiebra PP'
    ]
    divisiones = divisiones.dropna(subset=['Desc Division'])
    divisiones = divisiones[~divisiones['Desc Division'].isin(['Grand Total','Total JMC','Desc. Division'])]
    divisiones = divisiones[divisiones['Cod Division'].notna()]

    # ── HOJA: JMC (REGIONES) ─────────────────────────────────────────────────
    # Contiene quiebra por zona y región. Se filtran las filas de subtotal
    # de zona (solo tienen texto en Zona, no tienen número en Region).
    # La columna Region se formatea como string con cero a la izquierda (01, 02...).
    regiones = pd.read_excel('/tmp/bo.xlsx', sheet_name='JMC', header=2)
    regiones.columns = [
        'Zona', 'Region', 'Ventas Real', 'Ventas Historico',
        'Quiebra Real', 'Quiebra Pct Real', 'Quiebra Historico',
        'Quiebra Pct Historico', 'Dif Quiebra PP'
    ]
    regiones = regiones.dropna(subset=['Region'])
    regiones = regiones[pd.to_numeric(regiones['Region'], errors='coerce').notna()]
    regiones['Region'] = regiones['Region'].astype(int).astype(str).str.zfill(2)

    # ── HOJA: DISTRICT MANAGER ───────────────────────────────────────────────
    # Contiene quiebra por DM. Un DM puede aparecer en múltiples regiones
    # si maneja tiendas en zonas distintas.
    dm = pd.read_excel('/tmp/bo.xlsx', sheet_name='DISTRICT MANAGER', header=2)
    dm.columns = [
        'Zona', 'Region', 'District Manager', 'Ventas Real', 'Ventas Historico',
        'Quiebra Real', 'Quiebra Pct Real', 'Quiebra Historico',
        'Quiebra Pct Historico', 'Dif Quiebra PP'
    ]
    dm = dm.dropna(subset=['District Manager'])
    dm = dm[~dm['District Manager'].isin(['Grand Total','Total ARA sin BDC y FRA'])]

    # ── HOJA: TIENDAS (tabla más granular) ───────────────────────────────────
    # Una fila por tienda. Es la base para los filtros de zona, región y DM
    # ya que contiene todas las dimensiones geográficas y de gestión.
    tiendas = pd.read_excel('/tmp/bo.xlsx', sheet_name='TIENDAS.', header=2)
    tiendas.columns = [
        'Zona', 'Region', 'District Manager', 'Area Manager',
        'Cod Tienda', 'Tienda', 'Ventas Real', 'Ventas Historico',
        'Quiebra Real', 'Quiebra Pct Real', 'Quiebra Historico',
        'Quiebra Pct Historico', 'Dif Quiebra PP'
    ]
    tiendas = tiendas.dropna(subset=['Tienda'])
    tiendas = tiendas[tiendas['Quiebra Real'].notna()]

    # ── HOJA: AREA MANAGER ───────────────────────────────────────────────────
    # Nivel entre DM y tienda. Un AM gestiona entre 8 y 12 tiendas.
    am = pd.read_excel('/tmp/bo.xlsx', sheet_name='AREA MANAGER', header=2)
    am.columns = [
        'Zona', 'Region', 'District Manager', 'Area Manager',
        'Ventas Real', 'Ventas Historico', 'Quiebra Real', 'Quiebra Pct Real',
        'Quiebra Historico', 'Quiebra Pct Historico', 'Dif Quiebra PP'
    ]
    am = am.dropna(subset=['Area Manager'])
    am = am[~am['Area Manager'].str.contains('Total', na=False)]

    # ── ARCHIVO DE OBJETIVOS ─────────────────────────────────────────────────
    # Generado mensualmente desde MTD_Panel_de_Control_Divisiones.xlsx
    # usando el script actualizar_objetivos.py.
    # Contiene solo las columnas de objetivo: Quiebra Objetivo $ y Objetivo Quiebra %
    obj_div     = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_Divisiones')
    obj_reg     = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_Regiones')
    obj_dm      = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_DM')
    obj_tiendas = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_Tiendas')

    # Formatear región como string con cero a la izquierda para hacer join
    obj_reg['Cod. Region'] = obj_reg['Cod. Region'].astype(str).str.zfill(2)

    return divisiones, regiones, dm, tiendas, am, obj_div, obj_reg, obj_dm, obj_tiendas


# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES DE FORMATO
# -----------------------------------------------------------------------------

def fmt_mill(v):
    """Formatea un valor en pesos a millones con símbolo $. Ej: -15296831 → '$-15.297 M'"""
    if pd.isna(v): return "N/A"
    return f"${v/1e6:,.1f} M"

def fmt_pct(v):
    """Formatea un decimal como porcentaje con 2 decimales. Ej: -0.0138 → '-1.38%'"""
    if pd.isna(v): return "N/A"
    return f"{v*100:.2f}%"

def semaforo(real, obj):
    """
    Retorna emoji de semáforo comparando valor real vs objetivo.
    En quiebra, real < obj significa que está peor (más quiebra que lo permitido).
    """
    if pd.isna(real) or pd.isna(obj): return "⚪"
    return "🔴" if real < obj else "🟢"

def zona_pill(zona):
    """Genera HTML de píldora de color para la zona geográfica."""
    cls = {
        'NORTE': 'zona-norte',
        'CENTRO': 'zona-centro',
        'OCCIDENTE': 'zona-occidente',
        'ANTIOQUIA': 'zona-antioquia'
    }.get(str(zona).upper(), 'zona-norte')
    return f'<span class="zona-pill {cls}">{zona}</span>'


# -----------------------------------------------------------------------------
# SIDEBAR — FILTROS Y CONTROLES
# -----------------------------------------------------------------------------
with st.sidebar:
    # Logo y título del sidebar
    st.markdown("""
    <div style="padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #2D3A5A; margin-bottom: 1.5rem;">
        <div style="font-size:18px; font-weight:700; color:#FFFFFF; letter-spacing:-.3px;">📊 Quiebra MTD</div>
        <div style="font-size:11px; color:#6B7FA3; margin-top:3px;">Panel de Control Operacional</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:10px;font-weight:600;color:#6B7FA3;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Filtros</p>', unsafe_allow_html=True)

    # Carga de datos con indicador de progreso
    with st.spinner("Cargando datos..."):
        try:
            divisiones, regiones, dm, tiendas, am, obj_div, obj_reg, obj_dm, obj_tiendas = load_data()
            data_ok = True
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            data_ok = False

    if data_ok:
        # ── Filtro 1: Zona ────────────────────────────────────────────────────
        # Afecta todos los cálculos de KPIs y todas las pestañas.
        # Al seleccionar una zona, los filtros de región y DM se restringen.
        zonas = ['Todas'] + sorted(tiendas['Zona'].dropna().unique().tolist())
        zona_sel = st.selectbox("Zona", zonas)

        # ── Filtro 2: Región ──────────────────────────────────────────────────
        # Multiselecta. Se filtra según la zona seleccionada.
        if zona_sel != 'Todas':
            regs_disp = sorted(tiendas[tiendas['Zona']==zona_sel]['Region'].dropna().unique().tolist())
        else:
            regs_disp = sorted(tiendas['Region'].dropna().unique().tolist())
        reg_sel = st.multiselect("Región", regs_disp)

        # ── Filtro 3: District Manager ────────────────────────────────────────
        # Multiselecta. Se filtra según la zona seleccionada.
        if zona_sel != 'Todas':
            dms_disp = sorted(tiendas[tiendas['Zona']==zona_sel]['District Manager'].dropna().unique().tolist())
        else:
            dms_disp = sorted(tiendas['District Manager'].dropna().unique().tolist())
        dm_sel = st.multiselect("District Manager", dms_disp)

        # ── Filtro 4: Estado ──────────────────────────────────────────────────
        estado_sel = st.selectbox("Estado", ['Todos','🔴 Crítico','🟢 OK'])

        st.markdown("---")

        # Botón para limpiar caché y forzar recarga de datos desde Drive
        if st.button("🔄 Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(
            f'<p style="font-size:10px;color:#6B7FA3;margin-top:1rem">Última actualización:<br>'
            f'<span style="color:#9BAAC7">{pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")}</span></p>',
            unsafe_allow_html=True
        )

# Si los datos no cargaron, detener la ejecución de la app
if not data_ok:
    st.stop()


# -----------------------------------------------------------------------------
# APLICAR FILTROS A LOS DATAFRAMES
# -----------------------------------------------------------------------------
# Se crean copias filtradas para no modificar los datos originales cacheados.
# Los filtros se aplican en cascada: zona → región → DM.
# La tabla 'divisiones' no tiene columna de zona, por eso los filtros de zona
# se aplican a través de 'tiendas' para los KPIs globales.
# -----------------------------------------------------------------------------
tiendas_f  = tiendas.copy()
dm_f       = dm.copy()
regiones_f = regiones.copy()

# Aplicar filtro de zona
if zona_sel != 'Todas':
    tiendas_f  = tiendas_f[tiendas_f['Zona'] == zona_sel]
    dm_f       = dm_f[dm_f['Zona'] == zona_sel]
    regiones_f = regiones_f[regiones_f['Zona'] == zona_sel]

# Aplicar filtro de región (multiselecta, solo si hay selección)
if reg_sel:
    tiendas_f = tiendas_f[tiendas_f['Region'].isin(reg_sel)]
    dm_f      = dm_f[dm_f['Region'].isin(reg_sel)]

# Aplicar filtro de DM (multiselecta, solo si hay selección)
if dm_sel:
    tiendas_f = tiendas_f[tiendas_f['District Manager'].isin(dm_sel)]
    dm_f      = dm_f[dm_f['District Manager'].isin(dm_sel)]


# -----------------------------------------------------------------------------
# CRUCE CON OBJETIVOS (MERGE)
# -----------------------------------------------------------------------------
# Se une cada tabla de datos reales con su tabla de objetivos correspondiente.
# La clave de unión es el nombre de la dimensión (División, Región, DM).
# Se usa left join para conservar todos los registros aunque no tengan objetivo.
# -----------------------------------------------------------------------------

# Regiones filtradas + objetivos por región
reg_con_obj = regiones_f.merge(
    obj_reg[['Cod. Region', 'Quiebra Objetivo $', 'Objetivo Quiebra %']],
    left_on='Region', right_on='Cod. Region', how='left'
)

# DMs filtrados + objetivos por DM
dm_con_obj = dm_f.merge(
    obj_dm[['District Manager', 'Quiebra Objetivo $', 'Objetivo Quiebra %']],
    on='District Manager', how='left'
)

# Divisiones (sin filtro de zona) + objetivos por división
# Nota: divisiones no tiene zona, siempre muestra el total nacional
div_con_obj = divisiones.merge(
    obj_div[['Desc. Division', 'Quiebra Objetivo $', 'Objetivo Quiebra %']],
    left_on='Desc Division', right_on='Desc. Division', how='left'
)


# -----------------------------------------------------------------------------
# CÁLCULO DE KPIs GLOBALES
# -----------------------------------------------------------------------------
# Base: tabla 'tiendas' porque tiene la dimensión de zona para filtrar.
# El objetivo global viene de la fila 'TOTAL' en Obj_Divisiones cuando
# no hay filtro de zona. Con filtro de zona se promedia por las regiones
# de esa zona.
# -----------------------------------------------------------------------------
q_total    = tiendas_f['Quiebra Real'].sum()           # Quiebra total en pesos
v_total    = tiendas_f['Ventas Real'].sum()             # Ventas totales en pesos
q_pct      = q_total / v_total if v_total else 0        # % quiebra real
q_hist     = tiendas_f['Quiebra Historico'].sum()       # Quiebra histórico
v_hist     = tiendas_f['Ventas Historico'].sum()        # Ventas histórico
q_hist_pct = q_hist / v_hist if v_hist else 0           # % quiebra histórico

# Objetivo: cuando hay filtro de zona se usa el promedio de las regiones de esa zona.
# Sin filtro se usa la fila TOTAL del archivo de objetivos (más preciso).
if zona_sel != 'Todas':
    obj_pct    = reg_con_obj['Objetivo Quiebra %'].mean()
    obj_dollar = reg_con_obj['Quiebra Objetivo $'].sum()
else:
    obj_row    = obj_div[obj_div['Desc. Division'] == 'TOTAL']
    obj_pct    = obj_row['Objetivo Quiebra %'].values[0]    if len(obj_row) else -0.0124
    obj_dollar = obj_row['Quiebra Objetivo $'].values[0]    if len(obj_row) else -11455695584

# Brecha: diferencia entre real y objetivo
brecha_dollar = q_total - obj_dollar   # En pesos
brecha_pp     = q_pct - obj_pct        # En puntos porcentuales


# -----------------------------------------------------------------------------
# ENCABEZADO PRINCIPAL
# -----------------------------------------------------------------------------
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    filtro_activo = zona_sel if zona_sel != 'Todas' else 'Nacional'
    st.markdown(f"""
    <div class="dash-header">
        <div>
            <div class="dash-title">Panel de Control — Quiebra MTD</div>
            <div class="dash-sub">Vista: {filtro_activo} · {len(tiendas_f):,} tiendas · Ventas ${v_total/1e9:.1f} MM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PLANTILLA DE GRÁFICOS PLOTLY
# -----------------------------------------------------------------------------
# Configuración base para todos los gráficos: fondo transparente, fuente Inter,
# márgenes compactos y colores de ejes coherentes con el diseño.
# -----------------------------------------------------------------------------
COLORS = {
    'red':        '#E03131',  # Crítico / fuera de objetivo
    'green':      '#2F9E44',  # OK / en objetivo
    'blue':       '#1971C2',  # Informativo / ventas
    'blue_light': '#74C0FC',  # Acento azul claro
    'red_light':  '#FFA8A8',  # Rojo suave
    'gray':       '#868E96',  # Histórico / referencia
    'bg':         '#F7F8FA',  # Fondo general
    'navy':       '#1A2540'   # Azul marino (sidebar)
}

PLOTLY_TEMPLATE = dict(
    layout=dict(
        font=dict(family='Inter', size=11, color='#4A5568'),
        paper_bgcolor='rgba(0,0,0,0)',   # Fondo transparente (hereda de la tarjeta)
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=8, r=8, t=30, b=8),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1, font=dict(size=10)
        ),
        xaxis=dict(gridcolor='#F0F2F5', linecolor='#EAEDF2', tickfont=dict(size=10)),
        yaxis=dict(gridcolor='#F0F2F5', linecolor='#EAEDF2', tickfont=dict(size=10)),
    )
)


# =============================================================================
# PESTAÑAS DE NAVEGACIÓN
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Resumen",
    "📦  Divisiones",
    "🗺️  Regiones",
    "👤  DM & Tiendas"
])


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 1: RESUMEN — Vista ejecutiva para el COO
# ─────────────────────────────────────────────────────────────────────────────
with tab1:

    # ── KPIs (5 tarjetas en fila) ─────────────────────────────────────────────
    # Cada tarjeta muestra un indicador clave con color según estado (rojo/verde).
    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "Quiebra Total",      fmt_mill(q_total),          f"Obj: {fmt_mill(obj_dollar)}",                       q_total < obj_dollar),
        (k2, "% Quiebra Real",     f"{q_pct*100:.2f}%",        f"Obj: {obj_pct*100:.2f}%",                          q_pct < obj_pct),
        (k3, "Brecha vs Objetivo", fmt_mill(brecha_dollar),    f"{brecha_pp*100:+.2f} pp",                           brecha_dollar < 0),
        (k4, "% Histórico",        f"{q_hist_pct*100:.2f}%",   f"vs real: {(q_pct-q_hist_pct)*100:+.2f} pp",        q_pct < q_hist_pct),
        (k5, "Tiendas",            f"{len(tiendas_f):,}",      f"de {len(tiendas):,} total",                        False),
    ]
    for col, label, val, note, is_bad in kpis:
        color = 'kpi-red' if is_bad else 'kpi-green'
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value {color}">{val}</div>
                <div class="kpi-note">{note}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)

    # ── Tabla flash — Top críticos ────────────────────────────────────────────
    # 3 columnas: Top 3 divisiones / Top 3 regiones / Top 2 DM por región crítica
    # Cada fila es clickeable en el dashboard real (aquí solo visual).
    fc1, fc2, fc3 = st.columns(3)

    # Top 3 divisiones con mayor quiebra vs objetivo
    with fc1:
        top_div = div_con_obj.copy()
        top_div['Pct']    = top_div['Quiebra Real'] / top_div['Ventas Real']
        top_div['ObjPct'] = top_div['Objetivo Quiebra %'].fillna(0)
        # Solo muestra divisiones que están fuera de objetivo (real < obj en quiebra)
        top_div = top_div[top_div['Pct'] < top_div['ObjPct']].nsmallest(3, 'Pct')
        html = '<div class="section-card"><div class="section-title">🔴 Top 3 divisiones críticas</div>'
        for _, r in top_div.iterrows():
            html += f"""<div class="flash-item">
                <span class="flash-name"><span class="dot-red"></span>{r['Desc Division']}</span>
                <span><span class="flash-val" style="color:#E03131">{r['Pct']*100:.2f}%</span>
                <span class="flash-sub"> obj {r['ObjPct']*100:.2f}%</span></span>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # Top 3 regiones con mayor quiebra vs objetivo
    with fc2:
        top_reg = reg_con_obj.copy()
        top_reg['Pct']    = top_reg['Quiebra Real'] / top_reg['Ventas Real']
        top_reg['ObjPct'] = top_reg['Objetivo Quiebra %'].fillna(0)
        top_reg = top_reg[top_reg['Pct'] < top_reg['ObjPct']].nsmallest(3, 'Pct')
        html = '<div class="section-card"><div class="section-title">🔴 Top 3 regiones críticas</div>'
        for _, r in top_reg.iterrows():
            pill = zona_pill(r.get('Zona',''))
            html += f"""<div class="flash-item">
                <span class="flash-name"><span class="dot-red"></span>Reg. {r['Region']} {pill}</span>
                <span><span class="flash-val" style="color:#E03131">{r['Pct']*100:.2f}%</span>
                <span class="flash-sub"> obj {r['ObjPct']*100:.2f}%</span></span>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # Top 2 DM por cada una de las top 3 regiones críticas + peor tienda de cada DM
    with fc3:
        top_regs_ids = top_reg['Region'].tolist() if len(top_reg) > 0 else []
        html = '<div class="section-card"><div class="section-title">🔴 Top 2 DM por región crítica</div>'
        dm_top        = dm_con_obj.copy()
        dm_top['Pct']    = dm_top['Quiebra Real'] / dm_top['Ventas Real']
        dm_top['ObjPct'] = dm_top['Objetivo Quiebra %'].fillna(0)
        shown = 0
        for reg in top_regs_ids[:3]:
            dm_reg = dm_top[dm_top['Region'] == reg].nsmallest(2, 'Pct')
            if len(dm_reg) > 0:
                html += f'<div style="font-size:10px;color:#8A93A6;padding:4px 0 2px">Reg. {reg}</div>'
                for _, r in dm_reg.iterrows():
                    # Identifica la peor tienda del DM (mayor quiebra en pesos)
                    peor       = tiendas_f[tiendas_f['District Manager']==r['District Manager']].nsmallest(1,'Quiebra Real')
                    tienda_txt = peor['Tienda'].values[0][:18] if len(peor) else '—'
                    nombre_dm  = r['District Manager'].split()[0]+' '+r['District Manager'].split()[-1]
                    html += f"""<div class="flash-item">
                        <span class="flash-name"><span class="dot-red"></span>{nombre_dm}</span>
                        <span><span class="flash-val" style="color:#E03131">{r['Pct']*100:.2f}%</span>
                        <br><span class="flash-sub">↳ {tienda_txt}</span></span>
                    </div>"""
                    shown += 1
        if shown == 0:
            html += '<div style="font-size:12px;color:#8A93A6;padding:8px 0">Sin datos críticos</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # ── Gráficos de contexto ──────────────────────────────────────────────────
    g1, g2 = st.columns(2)

    # Gráfico 1: % quiebra por zona — real vs objetivo (barras agrupadas)
    with g1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">% quiebra por zona — real vs objetivo</div>', unsafe_allow_html=True)
        zona_data        = tiendas_f.groupby('Zona').agg(Quiebra=('Quiebra Real','sum'), Ventas=('Ventas Real','sum')).reset_index()
        zona_data['Pct'] = zona_data['Quiebra'] / zona_data['Ventas'] * 100
        zona_obj         = reg_con_obj.groupby('Zona')['Objetivo Quiebra %'].mean().reset_index()
        zona_obj.columns = ['Zona','ObjPct']
        zona_data        = zona_data.merge(zona_obj, on='Zona', how='left')
        zona_data['ObjPct'] = zona_data['ObjPct'] * 100

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Real', x=zona_data['Zona'], y=zona_data['Pct'],
            marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(zona_data['Pct'], zona_data['ObjPct'])],
            text=[f"{v:.2f}%" for v in zona_data['Pct']], textposition='outside', textfont=dict(size=10)
        ))
        fig.add_trace(go.Bar(
            name='Objetivo', x=zona_data['Zona'], y=zona_data['ObjPct'],
            marker_color='rgba(25,113,194,.2)',
            text=[f"{v:.2f}%" for v in zona_data['ObjPct']], textposition='outside', textfont=dict(size=10)
        ))
        fig.update_layout(**PLOTLY_TEMPLATE['layout'], barmode='group', height=240, yaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Gráfico 2: Top 7 divisiones con mayor quiebra % vs objetivo (barras horizontales)
    with g2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">top 7 divisiones — % real vs objetivo</div>', unsafe_allow_html=True)
        top7         = div_con_obj.copy()
        top7['Pct']    = top7['Quiebra Real'] / top7['Ventas Real'] * 100
        top7['ObjPct'] = top7['Objetivo Quiebra %'].fillna(0) * 100
        top7           = top7.nsmallest(7, 'Pct')   # Las 7 con mayor quiebra (más negativas)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name='Real', y=top7['Desc Division'], x=top7['Pct'], orientation='h',
            marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(top7['Pct'], top7['ObjPct'])],
            text=[f"{v:.1f}%" for v in top7['Pct']], textposition='outside', textfont=dict(size=10)
        ))
        fig2.add_trace(go.Bar(
            name='Objetivo', y=top7['Desc Division'], x=top7['ObjPct'], orientation='h',
            marker_color='rgba(25,113,194,.2)',
            text=[f"{v:.1f}%" for v in top7['ObjPct']], textposition='outside', textfont=dict(size=10)
        ))
        fig2.update_layout(**PLOTLY_TEMPLATE['layout'], barmode='group', height=240, xaxis_ticksuffix='%')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 2: DIVISIONES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    # Preparar datos de divisiones con métricas calculadas
    div_c            = div_con_obj.copy()
    div_c['Pct']     = div_c['Quiebra Real'] / div_c['Ventas Real'] * 100
    div_c['ObjPct']  = div_c['Objetivo Quiebra %'].fillna(0) * 100
    div_c['Brecha PP']  = div_c['Pct'] - div_c['ObjPct']
    div_c['Hist Pct'] = div_c['Quiebra Historico'] / div_c['Ventas Historico'] * 100
    div_sorted       = div_c.nsmallest(10, 'Pct')   # Top 10 peores

    d1, d2 = st.columns(2)

    # Gráfico: Quiebra en pesos — top 10 divisiones
    with d1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Quiebra $ — top 10 divisiones</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            y=div_sorted['Desc Division'], x=div_sorted['Quiebra Real']/1e6, orientation='h',
            marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(div_sorted['Pct'], div_sorted['ObjPct'])],
            text=[f"${v:,.0f}M" for v in div_sorted['Quiebra Real']/1e6], textposition='outside', textfont=dict(size=10)
        ))
        fig.update_layout(**PLOTLY_TEMPLATE['layout'], height=260, showlegend=False, xaxis_tickprefix='$', xaxis_ticksuffix='M')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Gráfico: % real vs objetivo — top 10 (barras agrupadas horizontales)
    with d2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">% real vs objetivo — top 10</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Real',     y=div_sorted['Desc Division'], x=div_sorted['Pct'],    orientation='h', marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(div_sorted['Pct'], div_sorted['ObjPct'])]))
        fig2.add_trace(go.Bar(name='Objetivo', y=div_sorted['Desc Division'], x=div_sorted['ObjPct'], orientation='h', marker_color='rgba(25,113,194,.25)'))
        fig2.update_layout(**PLOTLY_TEMPLATE['layout'], barmode='group', height=260, xaxis_ticksuffix='%')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    d3, d4 = st.columns(2)

    # Gráfico: Quiebra por liquidación (perecederos vencidos/dañados) — top 8
    with d3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Quiebra liquidación — top 8</div>', unsafe_allow_html=True)
        div_liq = div_c.nsmallest(8, 'Pct')
        fig3 = go.Figure(go.Bar(
            name='Liquidación', x=div_liq['Desc Division'], y=div_liq['Quiebra Real']/1e6,
            marker_color=COLORS['red']
        ))
        fig3.update_layout(**PLOTLY_TEMPLATE['layout'], height=200, yaxis_tickprefix='$', yaxis_ticksuffix='M', showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Gráfico: Comparativo real vs histórico vs objetivo — top 6
    with d4:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Real vs histórico vs objetivo</div>', unsafe_allow_html=True)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name='Real',      x=div_sorted['Desc Division'][:6], y=div_sorted['Pct'][:6],      marker_color=COLORS['red']))
        fig4.add_trace(go.Bar(name='Histórico', x=div_sorted['Desc Division'][:6], y=div_sorted['Hist Pct'][:6], marker_color='rgba(134,142,150,.4)'))
        fig4.add_trace(go.Bar(name='Objetivo',  x=div_sorted['Desc Division'][:6], y=div_sorted['ObjPct'][:6],   marker_color='rgba(25,113,194,.25)'))
        fig4.update_layout(**PLOTLY_TEMPLATE['layout'], barmode='group', height=200, yaxis_ticksuffix='%')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla completa de divisiones con filtro de estado
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Todas las divisiones</div>', unsafe_allow_html=True)

    estado_filter = st.selectbox("Filtrar por estado", ['Todas','🔴 Crítico','🟢 OK'], key='div_estado')
    div_tabla        = div_c.copy()
    div_tabla['Estado'] = div_tabla.apply(lambda r: '🔴 Crítico' if r['Pct'] < r['ObjPct'] else '🟢 OK', axis=1)
    if estado_filter != 'Todas':
        div_tabla = div_tabla[div_tabla['Estado'] == estado_filter]

    # Formatear columnas para presentación
    df_show = div_tabla[['Desc Division','Ventas Real','Quiebra Real','Pct','ObjPct','Brecha PP','Hist Pct','Estado']].rename(columns={
        'Desc Division':'División', 'Ventas Real':'Ventas $', 'Quiebra Real':'Quiebra $',
        'Pct':'% Real', 'ObjPct':'% Obj', 'Brecha PP':'Brecha PP', 'Hist Pct':'% Hist'
    })
    df_show['Ventas $']   = df_show['Ventas $'].apply(lambda x: f"${x/1e9:.1f} MM")
    df_show['Quiebra $']  = df_show['Quiebra $'].apply(lambda x: f"${x/1e6:,.0f} M")
    df_show['% Real']     = df_show['% Real'].apply(lambda x: f"{x:.2f}%")
    df_show['% Obj']      = df_show['% Obj'].apply(lambda x: f"{x:.2f}%")
    df_show['Brecha PP']  = df_show['Brecha PP'].apply(lambda x: f"{x:+.2f} pp")
    df_show['% Hist']     = df_show['% Hist'].apply(lambda x: f"{x:.2f}%")
    st.dataframe(df_show, use_container_width=True, hide_index=True, height=320)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 3: REGIONES
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    # Preparar datos de regiones con métricas calculadas
    reg_c               = reg_con_obj.copy()
    reg_c['Pct']        = reg_c['Quiebra Real'] / reg_c['Ventas Real'] * 100
    reg_c['ObjPct']     = reg_c['Objetivo Quiebra %'].fillna(0) * 100
    reg_c['Hist Pct']   = reg_c['Quiebra Historico'] / reg_c['Ventas Historico'] * 100
    reg_c['Brecha PP']  = reg_c['Pct'] - reg_c['ObjPct']
    reg_sorted          = reg_c.sort_values('Pct')  # Ordenar de peor a mejor

    r1, r2 = st.columns(2)

    # Gráfico: % real vs objetivo vs histórico — todas las regiones (barras agrupadas)
    with r1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">% real vs objetivo vs histórico por región</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real',      x='Reg '+reg_sorted['Region'], y=reg_sorted['Pct'],      marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(reg_sorted['Pct'], reg_sorted['ObjPct'])]))
        fig.add_trace(go.Bar(name='Objetivo',  x='Reg '+reg_sorted['Region'], y=reg_sorted['ObjPct'],   marker_color='rgba(25,113,194,.25)'))
        fig.add_trace(go.Bar(name='Histórico', x='Reg '+reg_sorted['Region'], y=reg_sorted['Hist Pct'], marker_color='rgba(134,142,150,.3)'))
        fig.update_layout(**PLOTLY_TEMPLATE['layout'], barmode='group', height=250, yaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Gráfico: Quiebra en pesos por región
    with r2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Quiebra $ por región</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Bar(
            x='Reg '+reg_sorted['Region'], y=reg_sorted['Quiebra Real']/1e6,
            marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(reg_sorted['Pct'], reg_sorted['ObjPct'])],
            text=[f"${v:,.0f}M" for v in reg_sorted['Quiebra Real']/1e6], textposition='outside', textfont=dict(size=10)
        ))
        fig2.update_layout(**PLOTLY_TEMPLATE['layout'], height=250, yaxis_tickprefix='$', yaxis_ticksuffix='M', showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r3, r4 = st.columns(2)

    # Gráfico: Brecha PP (real - objetivo) — barras con línea de cero
    with r3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Brecha PP vs objetivo por región</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(
            x='Reg '+reg_sorted['Region'], y=reg_sorted['Brecha PP'],
            marker_color=[COLORS['red'] if v < 0 else COLORS['green'] for v in reg_sorted['Brecha PP']],
            text=[f"{v:+.2f}" for v in reg_sorted['Brecha PP']], textposition='outside', textfont=dict(size=10)
        ))
        fig3.add_hline(y=0, line_color='#CCCCCC', line_width=1)  # Línea de referencia en cero
        fig3.update_layout(**PLOTLY_TEMPLATE['layout'], height=200, yaxis_ticksuffix=' pp', showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Gráfico: Ventas reales por región (contexto de tamaño de cada región)
    with r4:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Ventas reales por región $MM</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Bar(
            x='Reg '+reg_sorted['Region'], y=reg_sorted['Ventas Real']/1e9,
            marker_color=COLORS['blue'],
            text=[f"${v:.1f}MM" for v in reg_sorted['Ventas Real']/1e9], textposition='outside', textfont=dict(size=10)
        ))
        fig4.update_layout(**PLOTLY_TEMPLATE['layout'], height=200, yaxis_tickprefix='$', yaxis_ticksuffix='MM', showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla detalle regiones
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Detalle por región</div>', unsafe_allow_html=True)
    reg_display          = reg_sorted.copy()
    reg_display['Estado'] = reg_display.apply(lambda r: '🔴 Crítico' if r['Pct'] < r['ObjPct'] else '🟢 OK', axis=1)
    reg_display['Región'] = 'Reg. ' + reg_display['Region']
    df_reg = reg_display[['Región','Zona','Ventas Real','Quiebra Real','Pct','ObjPct','Brecha PP','Hist Pct','Estado']].rename(columns={
        'Ventas Real':'Ventas $', 'Quiebra Real':'Quiebra $', 'Pct':'% Real',
        'ObjPct':'% Obj', 'Brecha PP':'Brecha PP', 'Hist Pct':'% Hist'
    })
    df_reg['Ventas $']  = df_reg['Ventas $'].apply(lambda x: f"${x/1e9:.1f} MM")
    df_reg['Quiebra $'] = df_reg['Quiebra $'].apply(lambda x: f"${x/1e6:,.0f} M")
    df_reg['% Real']    = df_reg['% Real'].apply(lambda x: f"{x:.2f}%")
    df_reg['% Obj']     = df_reg['% Obj'].apply(lambda x: f"{x:.2f}%")
    df_reg['Brecha PP'] = df_reg['Brecha PP'].apply(lambda x: f"{x:+.2f} pp")
    df_reg['% Hist']    = df_reg['% Hist'].apply(lambda x: f"{x:.2f}%")
    st.dataframe(df_reg, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 4: DM & TIENDAS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    # Preparar datos de DMs — agrupa por DM porque un DM puede tener
    # registros en múltiples regiones en la tabla fuente
    dm_c              = dm_con_obj.copy()
    dm_c['Pct']       = dm_c['Quiebra Real'] / dm_c['Ventas Real'] * 100
    dm_c['ObjPct']    = dm_c['Objetivo Quiebra %'].fillna(0) * 100
    dm_c['Brecha PP'] = dm_c['Pct'] - dm_c['ObjPct']

    dm_sorted = dm_c.groupby(['District Manager','Zona','Region']).agg(
        Quiebra=('Quiebra Real','sum'),
        Ventas=('Ventas Real','sum'),
        ObjPct=('ObjPct','mean')
    ).reset_index()
    dm_sorted['Pct']      = dm_sorted['Quiebra'] / dm_sorted['Ventas'] * 100
    dm_sorted['Brecha PP'] = dm_sorted['Pct'] - dm_sorted['ObjPct']
    dm_sorted             = dm_sorted.sort_values('Pct')  # De peor a mejor

    dm1, dm2 = st.columns(2)

    # Gráfico: % quiebra por DM — top 10 peores (barras horizontales agrupadas)
    with dm1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">% quiebra por DM — real vs objetivo</div>', unsafe_allow_html=True)
        top_dm = dm_sorted.head(10)
        # Acortar nombre del DM para el eje (primer nombre + apellido)
        top_dm_names = top_dm['District Manager'].apply(lambda x: x.split()[0]+' '+x.split()[-1])
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real',     y=top_dm_names, x=top_dm['Pct'],    orientation='h', marker_color=[COLORS['red'] if r < o else COLORS['green'] for r,o in zip(top_dm['Pct'], top_dm['ObjPct'])]))
        fig.add_trace(go.Bar(name='Objetivo', y=top_dm_names, x=top_dm['ObjPct'], orientation='h', marker_color='rgba(25,113,194,.25)'))
        fig.update_layout(**PLOTLY_TEMPLATE['layout'], barmode='group', height=280, xaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Barras de progreso: muestra visualmente qué tan lejos está cada DM del objetivo
    with dm2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Progreso vs objetivo por DM</div>', unsafe_allow_html=True)
        for _, r in dm_sorted.head(8).iterrows():
            # ratio > 1 significa que superó el objetivo (está peor)
            ratio  = min(abs(r['Pct']) / abs(r['ObjPct']) * 50, 100) if r['ObjPct'] != 0 else 0
            color  = COLORS['red'] if r['Pct'] < r['ObjPct'] else COLORS['green']
            nombre = r['District Manager'].split()[0]+' '+r['District Manager'].split()[-1]
            st.markdown(f"""
            <div style="margin-bottom:8px">
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
                    <span style="color:#4A5568;font-weight:500">{nombre}</span>
                    <span style="color:{color};font-weight:600">{r['Pct']:.2f}% <span style="color:#8A93A6;font-weight:400">obj {r['ObjPct']:.2f}%</span></span>
                </div>
                <div style="background:#F0F2F5;border-radius:4px;height:5px">
                    <div style="width:{ratio}%;background:{color};height:5px;border-radius:4px"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    dm3, dm4 = st.columns(2)

    # Gráfico: Distribución de quiebra $ por zona (donut)
    with dm3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Distribución quiebra $ por zona</div>', unsafe_allow_html=True)
        zona_q              = tiendas_f.groupby('Zona')['Quiebra Real'].sum().reset_index()
        zona_q['Quiebra Real'] = zona_q['Quiebra Real'].abs()  # Valores positivos para el gráfico
        fig3 = go.Figure(go.Pie(
            labels=zona_q['Zona'], values=zona_q['Quiebra Real'],
            hole=.5,  # Donut chart
            marker_colors=[COLORS['red'],'#E67700',COLORS['blue'],COLORS['green']],
            textfont=dict(size=11)
        ))
        fig3.update_layout(**PLOTLY_TEMPLATE['layout'], height=200)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Gráfico: Top 8 tiendas con mayor quiebra en pesos
    with dm4:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 8 tiendas por quiebra $</div>', unsafe_allow_html=True)
        top_tiendas = tiendas_f.nsmallest(8, 'Quiebra Real')
        fig4 = go.Figure(go.Bar(
            y=top_tiendas['Tienda'].apply(lambda x: x[:20]),   # Acortar nombre si es muy largo
            x=top_tiendas['Quiebra Real']/1e6, orientation='h',
            marker_color=COLORS['red'],
            text=[f"${v:,.0f}M" for v in top_tiendas['Quiebra Real']/1e6], textposition='outside', textfont=dict(size=10)
        ))
        fig4.update_layout(**PLOTLY_TEMPLATE['layout'], height=200, xaxis_tickprefix='$', xaxis_ticksuffix='M', showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tablas de detalle — DMs y tiendas en columnas lado a lado
    t1, t2 = st.columns(2)

    # Tabla de District Managers con todas las métricas
    with t1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">District Managers</div>', unsafe_allow_html=True)
        dm_display          = dm_sorted.copy()
        dm_display['Estado'] = dm_display.apply(lambda r: '🔴' if r['Pct'] < r['ObjPct'] else '🟢', axis=1)
        df_dm               = dm_display[['District Manager','Zona','Region','Quiebra','Pct','ObjPct','Brecha PP','Estado']].copy()
        df_dm.columns       = ['DM','Zona','Reg','Quiebra $','% Real','% Obj','Brecha PP','Estado']
        df_dm['Quiebra $']  = df_dm['Quiebra $'].apply(lambda x: f"${x/1e6:,.0f}M")
        df_dm['% Real']     = df_dm['% Real'].apply(lambda x: f"{x:.2f}%")
        df_dm['% Obj']      = df_dm['% Obj'].apply(lambda x: f"{x:.2f}%")
        df_dm['Brecha PP']  = df_dm['Brecha PP'].apply(lambda x: f"{x:+.2f}")
        st.dataframe(df_dm, use_container_width=True, hide_index=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla de top 15 tiendas peores con DM, AM y métricas de quiebra
    with t2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 15 tiendas peores</div>', unsafe_allow_html=True)
        top15 = tiendas_f.nsmallest(15, 'Quiebra Real')[
            ['Tienda','District Manager','Area Manager','Region',
             'Ventas Real','Quiebra Real','Quiebra Pct Real','Quiebra Pct Historico','Dif Quiebra PP']
        ].copy()
        top15.columns       = ['Tienda','DM','AM','Reg','Ventas $','Quiebra $','% Real','% Hist','Dif PP']
        top15['Ventas $']   = top15['Ventas $'].apply(lambda x: f"${x/1e6:,.0f}M")
        top15['Quiebra $']  = top15['Quiebra $'].apply(lambda x: f"${x/1e6:,.1f}M")
        top15['% Real']     = top15['% Real'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
        top15['% Hist']     = top15['% Hist'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
        top15['Dif PP']     = top15['Dif PP'].apply(lambda x: f"{x*100:+.2f}" if pd.notna(x) else 'N/A')
        st.dataframe(top15, use_container_width=True, hide_index=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
