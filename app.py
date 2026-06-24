# =============================================================================
# PANEL DE CONTROL — QUIEBRA MTD
# =============================================================================
# Descripción : Dashboard operacional de quiebra para el COO.
#               Lee datos reales del CSV de tiendas y objetivos del Excel
#               de parámetros. Ambos archivos viven en Google Drive privado.
#
# Fuentes:
#   ID_TIENDAS : CSV tienda x división exportado de BO (diario)
#   ID_OBJ     : Excel de objetivos y Best Practice (mensual)
#
# Pestañas: Resumen · Divisiones · Regiones · DM y Tiendas
# =============================================================================

import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go

st.set_page_config(
    page_title="Quiebra MTD",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}
.main{background:#F4F5F7}
.block-container{padding:1.5rem 2rem!important;max-width:100%!important}
section[data-testid="stSidebar"]{background:#1A2540!important}
section[data-testid="stSidebar"] *{color:#C8D0E0!important}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label{
    color:#7B8FAE!important;font-size:10px!important;
    text-transform:uppercase;letter-spacing:.08em;font-weight:500}
.kpi{background:#fff;border-radius:8px;padding:1rem 1.2rem;
    border-left:3px solid #1A2540;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:4px}
.kpi.bad{border-left-color:#C5372C}
.kpi.good{border-left-color:#2D7A4F}
.kpi-lbl{font-size:10px;font-weight:500;color:#7B8FAE;text-transform:uppercase;
    letter-spacing:.08em;margin-bottom:6px}
.kpi-val{font-size:22px;font-weight:500;color:#1A2540;line-height:1.1}
.kpi-val.bad{color:#C5372C}
.kpi-val.good{color:#2D7A4F}
.kpi-note{font-size:11px;color:#7B8FAE;margin-top:4px}
.card{background:#fff;border-radius:8px;padding:1rem 1.2rem;
    border:0.5px solid #E2E5EC;box-shadow:0 1px 3px rgba(0,0,0,.04);margin-bottom:.75rem}
.card-title{font-size:10px;font-weight:500;color:#7B8FAE;text-transform:uppercase;
    letter-spacing:.08em;margin-bottom:10px;padding-bottom:8px;
    border-bottom:0.5px solid #F0F1F4}
.flash-row{display:flex;align-items:center;justify-content:space-between;
    padding:6px 0;border-bottom:0.5px solid #F4F5F7}
.flash-row:last-child{border-bottom:none}
.flash-name{font-size:12px;font-weight:500;color:#1A2540}
.flash-val{font-size:12px;font-weight:500}
.flash-sub{font-size:10px;color:#7B8FAE}
.ind-bad{display:inline-block;width:6px;height:6px;border-radius:50%;
    background:#C5372C;margin-right:6px;flex-shrink:0}
.ind-good{display:inline-block;width:6px;height:6px;border-radius:50%;
    background:#2D7A4F;margin-right:6px;flex-shrink:0}
.pill{display:inline-block;font-size:9px;padding:2px 7px;border-radius:3px;
    font-weight:500;margin-left:5px}
.pn{background:#FDF3DC;color:#7A5300}
.pc{background:#E4EEF9;color:#14488A}
.po{background:#F5E8F5;color:#6A2080}
.pa{background:#E3F2E8;color:#1B5C35}
.stTabs [data-baseweb="tab-list"]{background:transparent;border-bottom:1.5px solid #E2E5EC;gap:0}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:0;padding:8px 20px;
    font-size:12px;font-weight:500;color:#7B8FAE;border-bottom:2px solid transparent;margin-bottom:-1.5px}
.stTabs [aria-selected="true"]{color:#1A2540!important;border-bottom:2px solid #1A2540!important;
    background:transparent!important}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CARGA DE DATOS
# =============================================================================
@st.cache_data(ttl=3600)
def load_data():
    """
    Descarga y procesa los dos archivos desde Google Drive:
      - CSV de tiendas: datos reales por tienda x división (diario)
      - Excel de objetivos: objetivos y Best Practice por nivel (mensual)
    """
    url_tiendas = f"https://drive.google.com/uc?id={st.secrets['ID_TIENDAS']}"
    url_obj     = f"https://drive.google.com/uc?id={st.secrets['ID_OBJ']}"

    gdown.download(url_tiendas, '/tmp/tiendas.csv', quiet=True)
    gdown.download(url_obj,     '/tmp/obj.xlsx',    quiet=True)

    # ── CSV tiendas ───────────────────────────────────────────────────────────
    # Formato: una fila por tienda x división con datos reales e históricos
    raw = pd.read_csv('/tmp/tiendas.csv', encoding='latin-1', dtype=str)
    raw.columns = [
        'Unidad_Negocio','Zona','Region','District_Manager','Area_Manager',
        'Cod_Tienda','Desc_Tienda','Cod_Division','Desc_Division',
        'Ventas_Real','Ventas_Hist',
        'Quiebra_Real','Quiebra_Pct_Real',
        'Quiebra_Hist','Quiebra_Pct_Hist',
        'Dif_PP','Delta_Quiebra'
    ]

    # Filtrar filas válidas
    raw = raw[raw['Unidad_Negocio'].isin(['Ara','BdC','Ara Franquicia'])]
    raw = raw[~raw['Zona'].isin(['NO ASIGNADA','Total Ara sin BDC','Total Ara sin BDC y FRA'])]
    raw = raw[raw['Desc_Tienda'].notna() & raw['Desc_Division'].notna()]

    # Limpiar números
    def n(v):
        try: return float(str(v).replace(',','').strip())
        except: return None
    def p(v):
        try: return float(str(v).replace('%','').replace(',','').strip()) / 100
        except: return None

    for c in ['Ventas_Real','Ventas_Hist','Quiebra_Real','Quiebra_Hist','Dif_PP','Delta_Quiebra']:
        raw[c] = raw[c].apply(n)
    raw['Quiebra_Pct_Real'] = raw['Quiebra_Pct_Real'].apply(p)
    raw['Quiebra_Pct_Hist'] = raw['Quiebra_Pct_Hist'].apply(p)
    raw['Region'] = raw['Region'].apply(lambda x: str(x).zfill(2) if pd.notna(x) and str(x).strip().isdigit() else x)

    # ── Objetivos ─────────────────────────────────────────────────────────────
    # Hojas: Obj_Divisiones, Obj_Regiones, Obj_DM, Obj_AM, Obj_Tiendas, BP_Rangos
    obj_div     = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_Divisiones')
    obj_reg     = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_Regiones')
    obj_dm      = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_DM')
    obj_am      = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_AM')
    obj_tiendas = pd.read_excel('/tmp/obj.xlsx', sheet_name='Obj_Tiendas')
    bp_rangos   = pd.read_excel('/tmp/obj.xlsx', sheet_name='BP_Rangos')

    obj_reg['Cod. Region'] = obj_reg['Cod. Region'].astype(str).str.zfill(2)

    return raw, obj_div, obj_reg, obj_dm, obj_am, obj_tiendas, bp_rangos

# =============================================================================
# HELPERS
# =============================================================================
def fmm(v):
    """Formatea a millones con signo: -15297 → '-$15.297 M'"""
    if pd.isna(v) or v is None: return "N/A"
    return f"-${abs(v)/1e6:,.1f} M" if v < 0 else f"${v/1e6:,.1f} M"

def fmp(v):
    """Formatea decimal a porcentaje: -0.0138 → '-1.38%'"""
    if pd.isna(v) or v is None: return "N/A"
    return f"{v*100:.2f}%"

def pill(zona):
    cls = {'NORTE':'pn','CENTRO':'pc','OCCIDENTE':'po','ANTIOQUIA':'pa'}.get(str(zona).upper(),'pn')
    return f'<span class="pill {cls}">{zona}</span>'

def ind(real, obj):
    return '<span class="ind-bad"></span>' if (real is not None and obj is not None and real < obj) else '<span class="ind-good"></span>'

def agg(df, keys):
    """Agrega por las columnas clave sumando métricas numéricas."""
    g = df.groupby(keys, as_index=False).agg(
        Ventas_Real=('Ventas_Real','sum'),
        Ventas_Hist=('Ventas_Hist','sum'),
        Quiebra_Real=('Quiebra_Real','sum'),
        Quiebra_Hist=('Quiebra_Hist','sum'),
    )
    g['Pct_Real'] = g['Quiebra_Real'] / g['Ventas_Real']
    g['Pct_Hist'] = g['Quiebra_Hist'] / g['Ventas_Hist']
    return g

COLORS = {
    'red':   '#C5372C',
    'green': '#2D7A4F',
    'navy':  '#1A2540',
    'obj':   'rgba(26,37,64,.18)',
    'hist':  'rgba(26,37,64,.10)',
    'bp':    '#E67700',
}

def plotly_base():
    return dict(
        font=dict(family='Inter', size=11, color='#4A5568'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=8, r=8, t=24, b=8),
        xaxis=dict(gridcolor='#F0F1F4', linecolor='#E2E5EC', tickfont=dict(size=10)),
        yaxis=dict(gridcolor='#F0F1F4', linecolor='#E2E5EC', tickfont=dict(size=10)),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)),
    )

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem 0 1.5rem;border-bottom:0.5px solid #2D3A5A;margin-bottom:1.5rem">
        <div style="font-size:13px;font-weight:500;color:#fff;letter-spacing:.04em;text-transform:uppercase">Quiebra MTD</div>
        <div style="font-size:10px;color:#7B8FAE;margin-top:4px">Panel de control operacional</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Cargando datos..."):
        try:
            raw, obj_div, obj_reg, obj_dm, obj_am, obj_tiendas, bp_rangos = load_data()
            data_ok = True
        except Exception as e:
            st.error(f"Error: {e}")
            data_ok = False

    if data_ok:
        st.markdown('<p style="font-size:10px;font-weight:500;color:#7B8FAE;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Unidad de negocio</p>', unsafe_allow_html=True)
        unidades = ['Todas'] + sorted(raw['Unidad_Negocio'].dropna().unique().tolist())
        unidad_idx = unidades.index('Ara') if 'Ara' in unidades else 0
        unidad_sel = st.selectbox("", unidades, index=unidad_idx, key='unidad', label_visibility='collapsed')

        st.markdown('<div style="height:1px;background:#2D3A5A;margin:12px 0"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:10px;font-weight:500;color:#7B8FAE;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Filtros</p>', unsafe_allow_html=True)

        raw_u = raw[raw['Unidad_Negocio']==unidad_sel] if unidad_sel != 'Todas' else raw

        zonas = ['Todas'] + sorted(raw_u['Zona'].dropna().unique().tolist())
        zona_sel = st.selectbox("Zona", zonas)

        raw_z = raw_u[raw_u['Zona']==zona_sel] if zona_sel != 'Todas' else raw_u
        regs_disp = sorted(raw_z['Region'].dropna().unique().tolist())
        reg_sel = st.multiselect("Region", regs_disp)

        raw_r = raw_z[raw_z['Region'].isin(reg_sel)] if reg_sel else raw_z
        dms_disp = sorted(raw_r['District_Manager'].dropna().unique().tolist())
        dm_sel = st.multiselect("District Manager", dms_disp)

        divs_disp = sorted(raw_u['Desc_Division'].dropna().unique().tolist())
        div_sel = st.multiselect("Division", divs_disp)

        st.markdown('<div style="height:1px;background:#2D3A5A;margin:12px 0"></div>', unsafe_allow_html=True)
        if st.button("Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown(
            f'<p style="font-size:10px;color:#7B8FAE;margin-top:1rem">Actualizado:<br>'
            f'<span style="color:#9BAAC7">{pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")}</span></p>',
            unsafe_allow_html=True)

if not data_ok:
    st.stop()

# =============================================================================
# APLICAR FILTROS
# =============================================================================
f = raw.copy()
if unidad_sel != 'Todas': f = f[f['Unidad_Negocio'] == unidad_sel]
if zona_sel   != 'Todas': f = f[f['Zona'] == zona_sel]
if reg_sel:  f = f[f['Region'].isin(reg_sel)]
if dm_sel:   f = f[f['District_Manager'].isin(dm_sel)]
if div_sel:  f = f[f['Desc_Division'].isin(div_sel)]

# =============================================================================
# KPIs GLOBALES
# =============================================================================
q_total  = f['Quiebra_Real'].sum()
v_total  = f['Ventas_Real'].sum()
q_pct    = q_total / v_total if v_total else 0
q_hist   = f['Quiebra_Hist'].sum()
v_hist   = f['Ventas_Hist'].sum()
q_hist_p = q_hist / v_hist if v_hist else 0

# Objetivo: si hay filtro de zona usa promedio de regiones filtradas; si no, usa TOTAL de divisiones
if zona_sel != 'Todas' and len(reg_sel) > 0:
    regs_obj = obj_reg[obj_reg['Cod. Region'].isin(reg_sel)]
    obj_pct  = regs_obj['Objetivo Quiebra %'].mean() if len(regs_obj) else None
    obj_d    = regs_obj['Quiebra Objetivo $'].sum() if len(regs_obj) else None
    bp_pct   = regs_obj['Best Practice %'].mean() if len(regs_obj) else None
elif zona_sel != 'Todas':
    regs_zona = obj_reg  # todos, se filtrará por zona a través de tiendas
    obj_pct = obj_div['Objetivo Quiebra %'].mean()
    obj_d   = obj_div['Quiebra Objetivo $'].sum()
    bp_pct  = obj_div['Best Practice %'].mean()
else:
    obj_pct = obj_div['Objetivo Quiebra %'].mean()
    obj_d   = obj_div['Quiebra Objetivo $'].sum()
    bp_pct  = obj_div['Best Practice %'].mean()

brecha_d  = q_total - obj_d if obj_d else None
brecha_pp = q_pct - obj_pct if obj_pct else None

# =============================================================================
# HEADER
# =============================================================================
filtro_txt = zona_sel if zona_sel != 'Todas' else ('Todas las zonas')
unidad_txt = unidad_sel if unidad_sel != 'Todas' else 'Todas las unidades'
st.markdown(f"""
<div style="display:flex;align-items:baseline;justify-content:space-between;
    flex-wrap:wrap;gap:4px;margin-bottom:8px">
    <div style="font-size:16px;font-weight:500;color:#1A2540;white-space:nowrap">
        Panel de Control — Quiebra MTD
    </div>
    <div style="font-size:11px;color:#7B8FAE;white-space:nowrap">
        {unidad_txt}&nbsp;&nbsp;·&nbsp;&nbsp;{filtro_txt}&nbsp;&nbsp;·&nbsp;&nbsp;{f['Desc_Tienda'].nunique():,} tiendas&nbsp;&nbsp;·&nbsp;&nbsp;Ventas ${v_total/1e9:.1f} MM
    </div>
</div>
<div style="height:1px;background:#E2E5EC;margin-bottom:1rem"></div>
""", unsafe_allow_html=True)

# =============================================================================
# PESTAÑAS
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Divisiones", "Regiones", "DM y Tiendas"])


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 1: RESUMEN
# ─────────────────────────────────────────────────────────────────────────────
with tab1:

    # KPIs
    k1,k2,k3,k4,k5 = st.columns(5)
    kpis = [
        (k1,"Quiebra total",       fmm(q_total),          f"Obj: {fmm(obj_d)}",                           q_total < (obj_d or 0)),
        (k2,"% quiebra real",      fmp(q_pct),            f"Obj: {fmp(obj_pct)}",                         q_pct < (obj_pct or 0)),
        (k3,"Brecha vs objetivo",  fmm(brecha_d),         f"{brecha_pp*100:+.2f} pp" if brecha_pp else "", (brecha_d or 0) < 0),
        (k4,"Best practice",       fmp(bp_pct),           f"Real: {fmp(q_pct)}",                          q_pct < (bp_pct or 0)),
        (k5,"Historico",           fmp(q_hist_p),         f"vs real: {(q_pct-q_hist_p)*100:+.2f} pp",    False),
    ]
    for col, lbl, val, note, bad in kpis:
        est = 'bad' if bad else 'good'
        vc  = 'bad' if bad else ''
        with col:
            st.markdown(f"""
            <div class="kpi {est}">
                <div class="kpi-lbl">{lbl}</div>
                <div class="kpi-val {vc}">{val}</div>
                <div class="kpi-note">{note}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)

    # Tabla flash
    fc1,fc2,fc3 = st.columns(3)

    # Top 3 divisiones
    with fc1:
        divs_agg = agg(f, ['Desc_Division']).merge(
            obj_div[['Desc. Division','Objetivo Quiebra %','Best Practice %']],
            left_on='Desc_Division', right_on='Desc. Division', how='left')
        divs_agg['obj'] = divs_agg['Objetivo Quiebra %']
        top3d = divs_agg[divs_agg['Pct_Real'] < divs_agg['obj']].nsmallest(3,'Pct_Real')
        html = '<div class="card"><div class="card-title">Top 3 divisiones</div>'
        for _,r in top3d.iterrows():
            html += f"""<div class="flash-row">
                <span class="flash-name">{ind(r['Pct_Real'],r['obj'])}{r['Desc_Division']}</span>
                <span class="flash-val" style="color:#C5372C">{fmp(r['Pct_Real'])}
                <span class="flash-sub"> obj {fmp(r['obj'])}</span></span>
            </div>"""
        if len(top3d)==0: html += '<div style="font-size:12px;color:#7B8FAE;padding:8px 0">Sin divisiones criticas</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # Top 3 regiones
    with fc2:
        regs_agg = agg(f, ['Zona','Region']).merge(
            obj_reg[['Cod. Region','Objetivo Quiebra %','Best Practice %']],
            left_on='Region', right_on='Cod. Region', how='left')
        regs_agg['obj'] = regs_agg['Objetivo Quiebra %']
        top3r = regs_agg[regs_agg['Pct_Real'] < regs_agg['obj']].nsmallest(3,'Pct_Real')
        html = '<div class="card"><div class="card-title">Top 3 regiones</div>'
        for _,r in top3r.iterrows():
            html += f"""<div class="flash-row">
                <span class="flash-name">{ind(r['Pct_Real'],r['obj'])}Reg. {r['Region']}{pill(r['Zona'])}</span>
                <span class="flash-val" style="color:#C5372C">{fmp(r['Pct_Real'])}
                <span class="flash-sub"> obj {fmp(r['obj'])}</span></span>
            </div>"""
        if len(top3r)==0: html += '<div style="font-size:12px;color:#7B8FAE;padding:8px 0">Sin regiones criticas</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # Top 2 DM por region critica + peor tienda
    with fc3:
        dm_agg = agg(f, ['Zona','Region','District_Manager']).merge(
            obj_dm[['District Manager','Objetivo Quiebra %']],
            left_on='District_Manager', right_on='District Manager', how='left')
        dm_agg['obj'] = dm_agg['Objetivo Quiebra %']
        html = '<div class="card"><div class="card-title">Top 2 DM por region critica</div>'
        shown = 0
        for _,rr in top3r.iterrows():
            dm_reg = dm_agg[dm_agg['Region']==rr['Region']].nsmallest(2,'Pct_Real')
            if len(dm_reg)==0: continue
            html += f'<div style="font-size:9px;color:#7B8FAE;padding:4px 0 2px">Reg. {rr["Region"]}</div>'
            for _,d in dm_reg.iterrows():
                peor = f[f['District_Manager']==d['District_Manager']].nsmallest(1,'Quiebra_Real')
                tienda = peor['Desc_Tienda'].values[0][:20] if len(peor) else '—'
                nombre = d['District_Manager'].split()[0]+' '+d['District_Manager'].split()[-1]
                html += f"""<div class="flash-row">
                    <span class="flash-name">{ind(d['Pct_Real'],d['obj'])}{nombre}</span>
                    <span><span class="flash-val" style="color:#C5372C">{fmp(d['Pct_Real'])}</span>
                    <br><span class="flash-sub">&#x2937; {tienda}</span></span>
                </div>"""
                shown += 1
        if shown==0: html += '<div style="font-size:12px;color:#7B8FAE;padding:8px 0">Sin datos</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # Graficos
    g1,g2 = st.columns(2)

    with g1:
        st.markdown('<div class="card"><div class="card-title">% quiebra por zona — real vs objetivo vs best practice</div>', unsafe_allow_html=True)
        zd = agg(f,['Zona'])
        zo = obj_reg.groupby('Cod. Region').first().reset_index()
        # Objetivo promedio por zona usando tiendas como puente
        zona_obj = f.groupby('Zona').apply(lambda x: pd.Series({
            'Obj': obj_reg.loc[obj_reg['Cod. Region'].isin(x['Region'].unique()),'Objetivo Quiebra %'].mean(),
            'BP':  obj_reg.loc[obj_reg['Cod. Region'].isin(x['Region'].unique()),'Best Practice %'].mean(),
        })).reset_index()
        zd = zd.merge(zona_obj, on='Zona', how='left')

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real', x=zd['Zona'], y=zd['Pct_Real']*100,
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(zd['Pct_Real'], zd['Obj'])],
            text=[f"{v:.2f}%" for v in zd['Pct_Real']*100], textposition='outside', textfont=dict(size=10)))
        fig.add_trace(go.Bar(name='Objetivo', x=zd['Zona'], y=zd['Obj']*100,
            marker_color=COLORS['obj'],
            text=[f"{v:.2f}%" for v in zd['Obj']*100], textposition='outside', textfont=dict(size=10)))
        fig.add_trace(go.Scatter(name='Best Practice', x=zd['Zona'], y=zd['BP']*100,
            mode='markers+lines', line=dict(color=COLORS['bp'], dash='dot', width=1.5),
            marker=dict(color=COLORS['bp'], size=6)))
        fig.update_layout(**plotly_base(), barmode='group', height=240, yaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.markdown('<div class="card"><div class="card-title">top 7 divisiones — % real vs objetivo</div>', unsafe_allow_html=True)
        top7 = divs_agg.nsmallest(7,'Pct_Real')
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Real', y=top7['Desc_Division'], x=top7['Pct_Real']*100, orientation='h',
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(top7['Pct_Real'],top7['obj'])],
            text=[f"{v:.1f}%" for v in top7['Pct_Real']*100], textposition='outside', textfont=dict(size=10)))
        fig2.add_trace(go.Bar(name='Objetivo', y=top7['Desc_Division'], x=top7['obj']*100, orientation='h',
            marker_color=COLORS['obj'],
            text=[f"{v:.1f}%" for v in top7['obj']*100], textposition='outside', textfont=dict(size=10)))
        bp_col = 'Best Practice %' if 'Best Practice %' in top7.columns else 'obj'
        fig2.add_trace(go.Scatter(name='Best Practice', y=top7['Desc_Division'],
            x=top7[bp_col]*100, mode='markers',
            marker=dict(color=COLORS['bp'], size=8, symbol='diamond')))
        fig2.update_layout(**plotly_base(), barmode='group', height=240, xaxis_ticksuffix='%')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 2: DIVISIONES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    divs = agg(f,['Desc_Division']).merge(
        obj_div[['Desc. Division','Objetivo Quiebra %','Best Practice %','Quiebra Objetivo $']],
        left_on='Desc_Division', right_on='Desc. Division', how='left')
    divs['obj'] = divs['Objetivo Quiebra %']
    divs['bp']  = divs['Best Practice %']
    divs['Brecha_PP'] = divs['Pct_Real'] - divs['obj']
    divs_s = divs.nsmallest(10,'Pct_Real')

    d1,d2 = st.columns(2)
    with d1:
        st.markdown('<div class="card"><div class="card-title">Quiebra $ — top 10 divisiones</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(y=divs_s['Desc_Division'], x=divs_s['Quiebra_Real']/1e6, orientation='h',
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(divs_s['Pct_Real'],divs_s['obj'])],
            text=[f"-${abs(v):,.0f}M" for v in divs_s['Quiebra_Real']/1e6], textposition='outside', textfont=dict(size=10)))
        fig.update_layout(**plotly_base(), height=260, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with d2:
        st.markdown('<div class="card"><div class="card-title">% real vs objetivo vs best practice</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Real', y=divs_s['Desc_Division'], x=divs_s['Pct_Real']*100, orientation='h',
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(divs_s['Pct_Real'],divs_s['obj'])]))
        fig2.add_trace(go.Bar(name='Objetivo', y=divs_s['Desc_Division'], x=divs_s['obj']*100, orientation='h',
            marker_color=COLORS['obj']))
        fig2.add_trace(go.Scatter(name='Best Practice', y=divs_s['Desc_Division'],
            x=divs_s['bp']*100, mode='markers',
            marker=dict(color=COLORS['bp'], size=8, symbol='diamond')))
        fig2.update_layout(**plotly_base(), barmode='group', height=260, xaxis_ticksuffix='%')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    d3,d4 = st.columns(2)
    with d3:
        st.markdown('<div class="card"><div class="card-title">Liquidacion vs inventario — top 8</div>', unsafe_allow_html=True)
        liq = f.groupby('Desc_Division', as_index=False).agg(
            Liq=('Quiebra_Real','sum'), Inv=('Quiebra_Hist','sum')).nsmallest(8,'Liq')
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Liquidacion', x=liq['Desc_Division'], y=liq['Liq']/1e6, marker_color=COLORS['red']))
        fig3.update_layout(**plotly_base(), height=200, showlegend=False, yaxis_ticksuffix='M')
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with d4:
        st.markdown('<div class="card"><div class="card-title">Brecha PP vs objetivo por division</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Bar(
            x=divs_s['Desc_Division'], y=divs_s['Brecha_PP']*100,
            marker_color=[COLORS['red'] if v<0 else COLORS['green'] for v in divs_s['Brecha_PP']],
            text=[f"{v:+.2f}" for v in divs_s['Brecha_PP']*100], textposition='outside', textfont=dict(size=10)))
        fig4.add_hline(y=0, line_color='#E2E5EC', line_width=1)
        fig4.update_layout(**plotly_base(), height=200, showlegend=False, yaxis_ticksuffix=' pp')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla completa
    st.markdown('<div class="card"><div class="card-title">Detalle por division</div>', unsafe_allow_html=True)
    ef = st.selectbox("Estado", ['Todas','Critico','OK'], key='def')
    dt = divs.copy()
    dt['Estado'] = dt.apply(lambda r: 'Critico' if r['Pct_Real']<r['obj'] else 'OK', axis=1)
    if ef != 'Todas': dt = dt[dt['Estado']==ef]
    ds = dt[['Desc_Division','Ventas_Real','Quiebra_Real','Pct_Real','obj','bp','Brecha_PP','Pct_Hist','Estado']].copy()
    ds.columns = ['Division','Ventas $','Quiebra $','% Real','% Objetivo','% BP','Brecha PP','% Hist','Estado']
    ds['Ventas $']   = ds['Ventas $'].apply(lambda x: f"${x/1e9:.1f} MM")
    ds['Quiebra $']  = ds['Quiebra $'].apply(lambda x: f"-${abs(x)/1e6:,.0f}M")
    ds['% Real']     = ds['% Real'].apply(lambda x: f"{x*100:.2f}%")
    ds['% Objetivo'] = ds['% Objetivo'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
    ds['% BP']       = ds['% BP'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
    ds['Brecha PP']  = ds['Brecha PP'].apply(lambda x: f"{x*100:+.2f} pp" if pd.notna(x) else 'N/A')
    ds['% Hist']     = ds['% Hist'].apply(lambda x: f"{x*100:.2f}%")
    st.dataframe(ds, use_container_width=True, hide_index=True, height=320)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 3: REGIONES
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    regs = agg(f,['Zona','Region']).merge(
        obj_reg[['Cod. Region','Objetivo Quiebra %','Best Practice %','Quiebra Objetivo $']],
        left_on='Region', right_on='Cod. Region', how='left')
    regs['obj'] = regs['Objetivo Quiebra %']
    regs['bp']  = regs['Best Practice %']
    regs['Brecha_PP'] = regs['Pct_Real'] - regs['obj']
    regs_s = regs.sort_values('Pct_Real')

    r1,r2 = st.columns(2)
    with r1:
        st.markdown('<div class="card"><div class="card-title">% real vs objetivo vs best practice por region</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real', x='R'+regs_s['Region'], y=regs_s['Pct_Real']*100,
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(regs_s['Pct_Real'],regs_s['obj'])],
            text=[f"{v:.2f}%" for v in regs_s['Pct_Real']*100], textposition='outside', textfont=dict(size=10)))
        fig.add_trace(go.Bar(name='Objetivo', x='R'+regs_s['Region'], y=regs_s['obj']*100,
            marker_color=COLORS['obj']))
        fig.add_trace(go.Scatter(name='Best Practice', x='R'+regs_s['Region'], y=regs_s['bp']*100,
            mode='markers+lines', line=dict(color=COLORS['bp'], dash='dot', width=1.5),
            marker=dict(color=COLORS['bp'], size=6)))
        fig.update_layout(**plotly_base(), barmode='group', height=250, yaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2:
        st.markdown('<div class="card"><div class="card-title">Quiebra $ por region</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Bar(x='R'+regs_s['Region'], y=regs_s['Quiebra_Real']/1e6,
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(regs_s['Pct_Real'],regs_s['obj'])],
            text=[f"-${abs(v):,.0f}M" for v in regs_s['Quiebra_Real']/1e6],
            textposition='outside', textfont=dict(size=10)))
        fig2.update_layout(**plotly_base(), height=250, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r3,r4 = st.columns(2)
    with r3:
        st.markdown('<div class="card"><div class="card-title">Brecha PP vs objetivo</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(x='R'+regs_s['Region'], y=regs_s['Brecha_PP']*100,
            marker_color=[COLORS['red'] if v<0 else COLORS['green'] for v in regs_s['Brecha_PP']],
            text=[f"{v:+.2f}" for v in regs_s['Brecha_PP']*100], textposition='outside', textfont=dict(size=10)))
        fig3.add_hline(y=0, line_color='#E2E5EC', line_width=1)
        fig3.update_layout(**plotly_base(), height=200, showlegend=False, yaxis_ticksuffix=' pp')
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r4:
        st.markdown('<div class="card"><div class="card-title">Ventas reales por region</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Bar(x='R'+regs_s['Region'], y=regs_s['Ventas_Real']/1e9,
            marker_color=COLORS['navy'],
            text=[f"${v:.1f}MM" for v in regs_s['Ventas_Real']/1e9],
            textposition='outside', textfont=dict(size=10)))
        fig4.update_layout(**plotly_base(), height=200, showlegend=False, yaxis_ticksuffix='MM')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Detalle por region</div>', unsafe_allow_html=True)
    regs['Estado'] = regs.apply(lambda r: 'Critico' if r['Pct_Real']<r['obj'] else 'OK', axis=1)
    rs = regs[['Region','Zona','Ventas_Real','Quiebra_Real','Pct_Real','obj','bp','Brecha_PP','Pct_Hist','Estado']].copy()
    rs.columns = ['Region','Zona','Ventas $','Quiebra $','% Real','% Objetivo','% BP','Brecha PP','% Hist','Estado']
    rs['Region']     = 'Reg. ' + rs['Region']
    rs['Ventas $']   = rs['Ventas $'].apply(lambda x: f"${x/1e9:.1f} MM")
    rs['Quiebra $']  = rs['Quiebra $'].apply(lambda x: f"-${abs(x)/1e6:,.0f}M")
    rs['% Real']     = rs['% Real'].apply(lambda x: f"{x*100:.2f}%")
    rs['% Objetivo'] = rs['% Objetivo'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
    rs['% BP']       = rs['% BP'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
    rs['Brecha PP']  = rs['Brecha PP'].apply(lambda x: f"{x*100:+.2f} pp" if pd.notna(x) else 'N/A')
    rs['% Hist']     = rs['% Hist'].apply(lambda x: f"{x*100:.2f}%")
    st.dataframe(rs, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 4: DM Y TIENDAS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    dms = agg(f,['Zona','Region','District_Manager']).merge(
        obj_dm[['District Manager','Objetivo Quiebra %','Best Practice %','Quiebra Objetivo $']],
        left_on='District_Manager', right_on='District Manager', how='left')
    dms['obj'] = dms['Objetivo Quiebra %']
    dms['bp']  = dms['Best Practice %']
    dms['Brecha_PP'] = dms['Pct_Real'] - dms['obj']
    dms_s = dms.sort_values('Pct_Real')

    dm1,dm2 = st.columns(2)
    with dm1:
        st.markdown('<div class="card"><div class="card-title">% quiebra por DM — real vs objetivo</div>', unsafe_allow_html=True)
        top10dm = dms_s.head(10)
        nombres = top10dm['District_Manager'].apply(lambda x: x.split()[0]+' '+x.split()[-1])
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real', y=nombres, x=top10dm['Pct_Real']*100, orientation='h',
            marker_color=[COLORS['red'] if r<o else COLORS['green'] for r,o in zip(top10dm['Pct_Real'],top10dm['obj'])]))
        fig.add_trace(go.Bar(name='Objetivo', y=nombres, x=top10dm['obj']*100, orientation='h',
            marker_color=COLORS['obj']))
        fig.add_trace(go.Scatter(name='Best Practice', y=nombres, x=top10dm['bp']*100,
            mode='markers', marker=dict(color=COLORS['bp'], size=8, symbol='diamond')))
        fig.update_layout(**plotly_base(), barmode='group', height=280, xaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with dm2:
        st.markdown('<div class="card"><div class="card-title">Progreso vs objetivo</div>', unsafe_allow_html=True)
        for _,r in dms_s.head(8).iterrows():
            ratio = min(abs(r['Pct_Real'])/abs(r['obj'])*50,100) if r['obj'] else 0
            color = COLORS['red'] if r['Pct_Real']<r['obj'] else COLORS['green']
            nombre = r['District_Manager'].split()[0]+' '+r['District_Manager'].split()[-1]
            st.markdown(f"""
            <div style="margin-bottom:8px">
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
                    <span style="color:#1A2540;font-weight:500">{nombre}</span>
                    <span style="color:{color};font-weight:500">{fmp(r['Pct_Real'])}
                    <span style="color:#7B8FAE;font-weight:400"> obj {fmp(r['obj'])}</span></span>
                </div>
                <div style="background:#F4F5F7;border-radius:3px;height:4px">
                    <div style="width:{ratio}%;background:{color};height:4px;border-radius:3px"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    dm3,dm4 = st.columns(2)
    with dm3:
        st.markdown('<div class="card"><div class="card-title">Distribucion quiebra $ por zona</div>', unsafe_allow_html=True)
        zq = f.groupby('Zona')['Quiebra_Real'].sum().reset_index()
        zq['Quiebra_Real'] = zq['Quiebra_Real'].abs()
        fig3 = go.Figure(go.Pie(labels=zq['Zona'], values=zq['Quiebra_Real'],
            hole=.5, marker_colors=[COLORS['red'],'#8B4513',COLORS['navy'],COLORS['green']],
            textfont=dict(size=11)))
        fig3.update_layout(**plotly_base(), height=200)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with dm4:
        st.markdown('<div class="card"><div class="card-title">Top 8 tiendas por quiebra $</div>', unsafe_allow_html=True)
        tt = f.groupby(['Desc_Tienda','District_Manager','Region'], as_index=False).agg(
            Q=('Quiebra_Real','sum'), V=('Ventas_Real','sum')).nsmallest(8,'Q')
        fig4 = go.Figure(go.Bar(
            y=tt['Desc_Tienda'].apply(lambda x: x[:22]),
            x=tt['Q']/1e6, orientation='h',
            marker_color=COLORS['red'],
            text=[f"-${abs(v):,.0f}M" for v in tt['Q']/1e6],
            textposition='outside', textfont=dict(size=10)))
        fig4.update_layout(**plotly_base(), height=200, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    t1,t2 = st.columns(2)
    with t1:
        st.markdown('<div class="card"><div class="card-title">District Managers</div>', unsafe_allow_html=True)
        dms['Estado'] = dms.apply(lambda r: 'Critico' if r['Pct_Real']<r['obj'] else 'OK', axis=1)
        ds2 = dms[['District_Manager','Zona','Region','Quiebra_Real','Pct_Real','obj','bp','Brecha_PP','Estado']].copy()
        ds2.columns = ['DM','Zona','Reg','Quiebra $','% Real','% Objetivo','% BP','Brecha PP','Estado']
        ds2['Quiebra $']  = ds2['Quiebra $'].apply(lambda x: f"-${abs(x)/1e6:,.0f}M")
        ds2['% Real']     = ds2['% Real'].apply(lambda x: f"{x*100:.2f}%")
        ds2['% Objetivo'] = ds2['% Objetivo'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
        ds2['% BP']       = ds2['% BP'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A')
        ds2['Brecha PP']  = ds2['Brecha PP'].apply(lambda x: f"{x*100:+.2f} pp" if pd.notna(x) else 'N/A')
        st.dataframe(ds2, use_container_width=True, hide_index=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="card"><div class="card-title">Top 15 tiendas peores</div>', unsafe_allow_html=True)
        top15 = f.groupby(['Desc_Tienda','District_Manager','Area_Manager','Region'], as_index=False).agg(
            V=('Ventas_Real','sum'), Q=('Quiebra_Real','sum'), QH=('Quiebra_Hist','sum')
        ).nsmallest(15,'Q')
        top15['Pct']  = top15['Q'] / top15['V']
        top15['PctH'] = top15['QH'] / top15['V']
        ts = top15[['Desc_Tienda','District_Manager','Area_Manager','Region','V','Q','Pct','PctH']].copy()
        ts.columns = ['Tienda','DM','AM','Reg','Ventas $','Quiebra $','% Real','% Hist']
        ts['Tienda']    = ts['Tienda'].apply(lambda x: x[:24])
        ts['DM']        = ts['DM'].apply(lambda x: x.split()[0]+' '+x.split()[-1])
        ts['Ventas $']  = ts['Ventas $'].apply(lambda x: f"${x/1e6:,.0f}M")
        ts['Quiebra $'] = ts['Quiebra $'].apply(lambda x: f"-${abs(x)/1e6:,.1f}M")
        ts['% Real']    = ts['% Real'].apply(lambda x: f"{x*100:.2f}%")
        ts['% Hist']    = ts['% Hist'].apply(lambda x: f"{x*100:.2f}%")
        st.dataframe(ts, use_container_width=True, hide_index=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)
