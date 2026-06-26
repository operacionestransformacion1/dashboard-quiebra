# =============================================================================
# PANEL DE CONTROL — QUIEBRA MTD
# =============================================================================
# Descripción : Dashboard operacional de quiebra para el COO.
#               Navegación tipo browser con historial — botones atrás/adelante.
#               Drill-down desde resumen hasta tienda pasando por división,
#               región y DM.
#
# Fuentes (2 archivos en Google Drive):
#   ID_TIENDAS : CSV tienda x división exportado de BO (diario)
#   ID_OBJ     : Excel de objetivos y Best Practice por nivel (mensual)
#
# Pestañas: Resumen · Divisiones · Regiones · DM y Tiendas
# Navegación: historial tipo browser con ← →
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from styles import CSS
from nav import nav_init, nav_back, nav_fwd, nav_go, nav_reset
from data import load_data
from helpers import fmm, fmp, pill, dot, dot_txt, agg, pb, C

st.set_page_config(
    page_title="Quiebra MTD",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CSS, unsafe_allow_html=True)

nav_init()
cur = st.session_state.hist[st.session_state.pos]

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 1.2rem;border-bottom:0.5px solid #2D3A5A;margin-bottom:1.2rem">
        <div style="font-size:12px;font-weight:500;color:#fff;text-transform:uppercase;letter-spacing:.04em">Quiebra MTD</div>
        <div style="font-size:10px;color:#7B8FAE;margin-top:3px">Panel de control operacional</div>
    </div>""", unsafe_allow_html=True)

    with st.spinner("Cargando..."):
        try:
            raw, obj_div, obj_reg, obj_dm = load_data()
            data_ok = True
        except Exception as e:
            st.error(f"Error: {e}")
            data_ok = False

    if data_ok:
        TABS = ['Resumen','Divisiones','Regiones','DM y Tiendas']

        # Unidad de negocio — siempre visible
        st.markdown("<p>Unidad de negocio</p>", unsafe_allow_html=True)
        unidades = ['Todas'] + sorted(raw['Unidad'].dropna().unique().tolist())
        uid = unidades.index(cur['unidad']) if cur['unidad'] in unidades else (unidades.index('Ara') if 'Ara' in unidades else 0)
        unidad_sel = st.selectbox("", unidades, index=uid, key=f'sb_unidad_{st.session_state.pos}', label_visibility='collapsed')
        raw_u = raw[raw['Unidad']==unidad_sel] if unidad_sel != 'Todas' else raw

        st.markdown('<div style="height:1px;background:#2D3A5A;margin:10px 0"></div>', unsafe_allow_html=True)

        # Filtros según pestaña activa
        tab_idx = cur['tab']
        zona_sel = cur['zonas']
        reg_sel  = cur['regs']
        dm_sel   = cur['dms']
        div_sel  = cur['divs']

        if tab_idx == 1:  # Divisiones
            st.markdown("<p>Division</p>", unsafe_allow_html=True)
            divs_opts = sorted(raw_u['Div'].dropna().unique().tolist())
            div_sel = st.multiselect("", divs_opts, default=[d for d in cur['divs'] if d in divs_opts], key=f'sb_div_{st.session_state.pos}', label_visibility='collapsed')

        elif tab_idx == 2:  # Regiones
            st.markdown("<p>Zona</p>", unsafe_allow_html=True)
            zonas_opts = sorted(raw_u['Zona'].dropna().unique().tolist())
            zona_sel = st.multiselect("", zonas_opts, default=[z for z in cur['zonas'] if z in zonas_opts], key=f'sb_zona_{st.session_state.pos}', label_visibility='collapsed')
            raw_z = raw_u[raw_u['Zona'].isin(zona_sel)] if zona_sel else raw_u
            st.markdown("<p style='margin-top:8px'>Region</p>", unsafe_allow_html=True)
            regs_opts = sorted(raw_z['Region'].dropna().unique().tolist())
            reg_sel = st.multiselect("", regs_opts, default=[r for r in cur['regs'] if r in regs_opts], key=f'sb_reg_{st.session_state.pos}', label_visibility='collapsed')

        elif tab_idx == 3:  # DM y Tiendas
            st.markdown("<p>Zona</p>", unsafe_allow_html=True)
            zonas_opts = sorted(raw_u['Zona'].dropna().unique().tolist())
            zona_sel = st.multiselect("", zonas_opts, default=[z for z in cur['zonas'] if z in zonas_opts], key=f'sb_zona_dm_{st.session_state.pos}', label_visibility='collapsed')
            raw_z = raw_u[raw_u['Zona'].isin(zona_sel)] if zona_sel else raw_u
            st.markdown("<p style='margin-top:8px'>Region</p>", unsafe_allow_html=True)
            regs_opts = sorted(raw_z['Region'].dropna().unique().tolist())
            reg_sel = st.multiselect("", regs_opts, default=[r for r in cur['regs'] if r in regs_opts], key=f'sb_reg_dm_{st.session_state.pos}', label_visibility='collapsed')
            raw_r = raw_z[raw_z['Region'].isin(reg_sel)] if reg_sel else raw_z
            st.markdown("<p style='margin-top:8px'>District Manager</p>", unsafe_allow_html=True)
            dms_opts = sorted(raw_r['DM'].dropna().unique().tolist())
            dm_sel = st.multiselect("", dms_opts, default=[d for d in cur['dms'] if d in dms_opts], key=f'sb_dm_{st.session_state.pos}', label_visibility='collapsed')

        else:  # Resumen
            st.markdown('<p style="font-style:italic;color:#7B8FAE!important">Vista ejecutiva</p>', unsafe_allow_html=True)

        st.markdown('<div style="height:1px;background:#2D3A5A;margin:10px 0"></div>', unsafe_allow_html=True)
        if st.button("Reestablecer todo", use_container_width=True, help="Borra todos los filtros e historial de navegacion"):
            nav_reset()
        if st.button("Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown(f'<p style="margin-top:1rem">Actualizado:<br><span style="color:#9BAAC7!important">{pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")}</span></p>', unsafe_allow_html=True)

if not data_ok:
    st.stop()

# =============================================================================
# FILTRAR DATOS
# =============================================================================
f = raw.copy()
if unidad_sel != 'Todas': f = f[f['Unidad'] == unidad_sel]
if zona_sel:  f = f[f['Zona'].isin(zona_sel)]
if reg_sel:  f = f[f['Region'].isin(reg_sel)]
if dm_sel:   f = f[f['DM'].isin(dm_sel)]
if div_sel:  f = f[f['Div'].isin(div_sel)]

# =============================================================================
# BARRA DE NAVEGACIÓN
# =============================================================================
can_back = st.session_state.pos > 0
can_fwd  = st.session_state.pos < len(st.session_state.hist) - 1

# Breadcrumb
bc_parts = ['Resumen']
if cur['unidad'] != 'Todas': bc_parts.append(cur['unidad'])
if cur['zonas']:  bc_parts.append(', '.join(cur['zonas']))
if cur['regs']:  bc_parts.append('Reg. '+', '.join(cur['regs']))
if cur['dms']:   bc_parts.append(', '.join([d.split()[0]+' '+d.split()[-1] for d in cur['dms']]))
if cur['divs']:  bc_parts.append(', '.join(cur['divs']))

nav1, nav2, nav3, nav4 = st.columns([0.06, 0.06, 0.68, 0.20])
with nav1:
    if st.button("←", disabled=not can_back, key='back', use_container_width=True):
        nav_back()
with nav2:
    if st.button("→", disabled=not can_fwd, key='fwd', use_container_width=True):
        nav_fwd()
with nav3:
    st.markdown(f'<div class="nav-title">Panel de Control — Quiebra MTD</div>', unsafe_allow_html=True)
with nav4:
    tiendas_n = f['Tienda'].nunique()
    v_total   = f['Ventas'].sum()
    st.markdown(f'<div class="nav-sub" style="text-align:right;padding-top:4px">{tiendas_n:,} tiendas · ${v_total/1e9:.1f} MM</div>', unsafe_allow_html=True)

# Breadcrumb
st.markdown(f'<div class="breadcrumb">{" › ".join(bc_parts)}</div>', unsafe_allow_html=True)

# Línea separadora
st.markdown('<div style="height:1px;background:#E2E5EC;margin-bottom:.8rem"></div>', unsafe_allow_html=True)

# =============================================================================
# KPIs GLOBALES
# =============================================================================
q_total = f['Quiebra'].sum()
v_total = f['Ventas'].sum()
q_pct   = q_total / v_total if v_total else 0
q_hist  = f['QuiebraH'].sum()
v_hist  = f['VentasH'].sum()
q_histp = q_hist / v_hist if v_hist else 0

obj_pct = obj_div['Objetivo Quiebra %'].mean()
obj_d   = obj_div['Quiebra Objetivo $'].sum()
bp_pct  = obj_div['Best Practice %'].mean()
brecha_d  = q_total - obj_d
brecha_pp = q_pct - obj_pct

# =============================================================================
# PESTAÑAS
# =============================================================================
TABS = ['Resumen','Divisiones','Regiones','DM y Tiendas']
tab1, tab2, tab3, tab4 = st.tabs(TABS)

# Activar la pestaña del estado actual
# (Streamlit no permite seleccionar tab programáticamente,
#  se usa el radio del sidebar como fuente de verdad)

# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 1: RESUMEN
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # KPIs
    k1,k2,k3,k4,k5 = st.columns(5)
    for col,lbl,val,note,bad in [
        (k1,"Quiebra total",    fmm(q_total),     f"Obj: {fmm(obj_d)}",                    q_total < obj_d),
        (k2,"% quiebra real",   fmp(q_pct),       f"Obj: {fmp(obj_pct)}",                  q_pct < obj_pct),
        (k3,"Brecha vs obj",    fmm(brecha_d),    f"{brecha_pp*100:+.2f} pp",              brecha_d < 0),
        (k4,"Best practice",    fmp(bp_pct),      f"Real: {fmp(q_pct)}",                   q_pct < bp_pct),
        (k5,"Historico",        fmp(q_histp),     f"vs real: {(q_pct-q_histp)*100:+.2f} pp", False),
    ]:
        with col:
            st.markdown(f"""<div class="kpi {'bad' if bad else 'good'}">
                <div class="kpi-lbl">{lbl}</div>
                <div class="kpi-val {'bad' if bad else ''}">{val}</div>
                <div class="kpi-note">{note}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.4rem'></div>", unsafe_allow_html=True)

    # Calcular tops
    divs_agg = agg(f,['Div']).merge(obj_div[['Desc. Division','Objetivo Quiebra %','Best Practice %']],
        left_on='Div', right_on='Desc. Division', how='left')
    divs_agg['obj'] = divs_agg['Objetivo Quiebra %']
    top3d = divs_agg[divs_agg['Pct'] < divs_agg['obj']].nsmallest(3,'Pct')

    regs_agg = agg(f,['Zona','Region']).merge(
        obj_reg[['Cod. Region','Objetivo Quiebra %','Best Practice %']],
        left_on='Region', right_on='Cod. Region', how='left')
    regs_agg['obj'] = regs_agg['Objetivo Quiebra %']
    top3r = regs_agg[regs_agg['Pct'] < regs_agg['obj']].nsmallest(3,'Pct')

    dm_agg = agg(f,['Zona','Region','DM']).merge(
        obj_dm[['District Manager','Objetivo Quiebra %']],
        left_on='DM', right_on='District Manager', how='left')
    dm_agg['obj'] = dm_agg['Objetivo Quiebra %']

    fc1,fc2,fc3 = st.columns(3)

    # Flash: Top 3 divisiones — clic navega a Divisiones filtrada
    with fc1:
        html = '<div class="card"><div class="card-title">Top 3 divisiones</div>'
        for _,r in top3d.iterrows():
            html += f"""<div class="frow" onclick="window.parent.postMessage({{type:'nav',tab:1,div:'{r['Div']}'}}, '*')">
                <span class="fn">{dot(r['Pct'],r['obj'])}{r['Div']}</span>
                <span class="fv" style="color:#C5372C">{fmp(r['Pct'])} <span class="fs">obj {fmp(r['obj'])}</span></span>
            </div>"""
        if len(top3d)==0: html += '<div style="font-size:12px;color:#7B8FAE;padding:6px 0">Sin divisiones criticas</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        # Drill-down: botones invisibles superpuestos sobre cada fila
        for _,r in top3d.iterrows():
            if st.button(f"► {r['Div']}", key=f"d_{r['Div']}", use_container_width=True,
                help=f"Ver detalle de {r['Div']}"):
                nav_go(1, unidad=unidad_sel, divs=[r['Div']])

    # Flash: Top 3 regiones — clic navega a Regiones filtrada
    with fc2:
        html = '<div class="card"><div class="card-title">Top 3 regiones</div>'
        for _,r in top3r.iterrows():
            html += f"""<div class="frow">
                <span class="fn">{dot(r['Pct'],r['obj'])}Reg. {r['Region']}{pill(r['Zona'])}</span>
                <span class="fv" style="color:#C5372C">{fmp(r['Pct'])} <span class="fs">obj {fmp(r['obj'])}</span></span>
            </div>"""
        if len(top3r)==0: html += '<div style="font-size:12px;color:#7B8FAE;padding:6px 0">Sin regiones criticas</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        for _,r in top3r.iterrows():
            if st.button(f"► Reg. {r['Region']}", key=f"r_{r['Region']}", use_container_width=True,
                help=f"Ver detalle de Región {r['Region']}"):
                nav_go(2, unidad=unidad_sel, zonas=[r['Zona']], regs=[r['Region']])

    # Flash: Top 2 DM por region critica — clic navega a DM filtrado
    with fc3:
        html = '<div class="card"><div class="card-title">Top 2 DM por region</div>'
        shown = 0
        dm_buttons = []
        for _,rr in top3r.iterrows():
            dm_reg = dm_agg[dm_agg['Region']==rr['Region']].nsmallest(2,'Pct')
            if len(dm_reg)==0: continue
            html += f'<div style="font-size:9px;color:#7B8FAE;padding:3px 0 2px">Reg. {rr["Region"]}</div>'
            for _,d in dm_reg.iterrows():
                peor = f[f['DM']==d['DM']].nsmallest(1,'Quiebra')
                tienda = peor['Tienda'].values[0][:20] if len(peor) else '—'
                nombre = d['DM'].split()[0]+' '+d['DM'].split()[-1]
                html += f"""<div class="frow">
                    <span class="fn">{dot(d['Pct'],d['obj'])}{nombre}</span>
                    <span><span class="fv" style="color:#C5372C">{fmp(d['Pct'])}</span>
                    <br><span class="fs">&#x2937; {tienda}</span></span>
                </div>"""
                dm_buttons.append((d['DM'], rr['Region'], rr['Zona']))
                shown += 1
        if shown==0: html += '<div style="font-size:12px;color:#7B8FAE;padding:6px 0">Sin datos</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        for dm_name, reg, zona in dm_buttons:
            nombre_corto = dm_name.split()[0]+' '+dm_name.split()[-1]
            if st.button(f"► {nombre_corto}", key=f"dm_{dm_name}_{reg}", use_container_width=True,
                help=f"Ver detalle de {nombre_corto}"):
                nav_go(3, unidad=unidad_sel, zonas=[zona], regs=[reg], dms=[dm_name])

    # Graficos resumen
    g1,g2 = st.columns(2)
    with g1:
        st.markdown('<div class="card"><div class="card-title">% quiebra por zona — real vs objetivo vs best practice</div>', unsafe_allow_html=True)
        zd = agg(f,['Zona'])
        zona_obj = f.groupby('Zona').apply(lambda x: pd.Series({
            'Obj': obj_reg.loc[obj_reg['Cod. Region'].isin(x['Region'].unique()),'Objetivo Quiebra %'].mean(),
            'BP':  obj_reg.loc[obj_reg['Cod. Region'].isin(x['Region'].unique()),'Best Practice %'].mean(),
        })).reset_index()
        zd = zd.merge(zona_obj, on='Zona', how='left')
        zd = zd.sort_values('Pct')
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real', x=zd['Zona'], y=zd['Pct']*100,
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(zd['Pct'],zd['Obj'])],
            text=[f"{v:.2f}%" for v in zd['Pct']*100], textposition='outside', textfont=dict(size=10)))
        fig.add_trace(go.Bar(name='Objetivo', x=zd['Zona'], y=zd['Obj']*100, marker_color=C['obj']))
        fig.add_trace(go.Scatter(name='Best Practice', x=zd['Zona'], y=zd['BP']*100,
            mode='markers+lines', line=dict(color=C['bp'],dash='dot',width=1.5), marker=dict(size=6,color=C['bp'])))
        fig.update_layout(**pb(), barmode='group', height=220, yaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.markdown('<div class="card"><div class="card-title">top 7 divisiones — % real vs objetivo</div>', unsafe_allow_html=True)
        top7 = divs_agg.nsmallest(7,'Pct')
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Real', y=top7['Div'], x=top7['Pct']*100, orientation='h',
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(top7['Pct'],top7['obj'])]))
        fig2.add_trace(go.Bar(name='Objetivo', y=top7['Div'], x=top7['obj']*100, orientation='h', marker_color=C['obj']))
        bp_col = 'Best Practice %' if 'Best Practice %' in top7.columns else 'obj'
        fig2.add_trace(go.Scatter(name='BP', y=top7['Div'], x=top7[bp_col]*100,
            mode='markers', marker=dict(color=C['bp'],size=8,symbol='diamond')))
        fig2.update_layout(**pb(), barmode='group', height=220, xaxis_ticksuffix='%', yaxis_autorange='reversed')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 2: DIVISIONES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    divs = agg(f,['Div']).merge(
        obj_div[['Desc. Division','Objetivo Quiebra %','Best Practice %','Quiebra Objetivo $']],
        left_on='Div', right_on='Desc. Division', how='left')
    divs['obj'] = divs['Objetivo Quiebra %']
    divs['bp']  = divs['Best Practice %']
    divs['Brecha'] = divs['Pct'] - divs['obj']
    divs_s = divs.nsmallest(10,'Pct')

    d1,d2 = st.columns(2)
    with d1:
        st.markdown('<div class="card"><div class="card-title">Quiebra $ — top 10</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(y=divs_s['Div'], x=divs_s['Q']/1e6, orientation='h',
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(divs_s['Pct'],divs_s['obj'])],
            text=[f"-${abs(v):,.0f}M" for v in divs_s['Q']/1e6], textposition='outside', textfont=dict(size=10)))
        fig.update_layout(**pb(), height=250, showlegend=False, yaxis_autorange='reversed')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with d2:
        st.markdown('<div class="card"><div class="card-title">% real vs objetivo vs best practice</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Real', y=divs_s['Div'], x=divs_s['Pct']*100, orientation='h',
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(divs_s['Pct'],divs_s['obj'])]))
        fig2.add_trace(go.Bar(name='Objetivo', y=divs_s['Div'], x=divs_s['obj']*100, orientation='h', marker_color=C['obj']))
        fig2.add_trace(go.Scatter(name='BP', y=divs_s['Div'], x=divs_s['bp']*100,
            mode='markers', marker=dict(color=C['bp'],size=8,symbol='diamond')))
        fig2.update_layout(**pb(), barmode='group', height=250, xaxis_ticksuffix='%', yaxis_autorange='reversed')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    d3,d4 = st.columns(2)
    with d3:
        st.markdown('<div class="card"><div class="card-title">Brecha PP vs objetivo</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(x=divs_s['Div'], y=divs_s['Brecha']*100,
            marker_color=[C['red'] if v<0 else C['green'] for v in divs_s['Brecha']],
            text=[f"{v:+.2f}" for v in divs_s['Brecha']*100], textposition='outside', textfont=dict(size=10)))
        fig3.add_hline(y=0, line_color='#E2E5EC', line_width=1)
        fig3.update_layout(**pb(), height=190, showlegend=False, yaxis_ticksuffix=' pp')
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with d4:
        st.markdown('<div class="card"><div class="card-title">Real vs historico top 6</div>', unsafe_allow_html=True)
        t6 = divs_s.head(6)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name='Real', x=t6['Div'], y=t6['Pct']*100, marker_color=C['red']))
        fig4.add_trace(go.Bar(name='Historico', x=t6['Div'], y=t6['PctH']*100, marker_color='rgba(26,37,64,.2)'))
        fig4.add_trace(go.Bar(name='Objetivo', x=t6['Div'], y=t6['obj']*100, marker_color=C['obj']))
        fig4.update_layout(**pb(), barmode='group', height=190, yaxis_ticksuffix='%')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla + drill-down a regiones
    st.markdown('<div class="card"><div class="card-title">Detalle — clic en una division para ver por region</div>', unsafe_allow_html=True)
    ef = st.selectbox("Estado", ['Todas','Critico','OK'], key='def2')
    dt = divs.copy()
    dt['Estado'] = dt.apply(lambda r: 'Critico' if r['Pct']<r['obj'] else 'OK', axis=1)
    if ef != 'Todas': dt = dt[dt['Estado']==ef]
    dt = dt.sort_values('Pct')

    for _,r in dt.iterrows():
        col_n, col_v, col_o, col_b, col_br = st.columns([4,2,2,2,2])
        if col_n.button(f"{dot_txt(r['Pct'],r['obj'])} {r['Div']} →", key=f"div_reg_{r['Div']}",
            use_container_width=True, help="Ver por region"):
            nav_go(2, unidad=unidad_sel, divs=[r['Div']])
        col_v.markdown(f"{fmm(r['Q'])}")
        col_o.markdown(f"{fmp(r['Pct'])} / {fmp(r['obj'])}")
        col_b.markdown(f"BP: {fmp(r['bp'])}")
        col_br.markdown(f"{r['Brecha']*100:+.2f} pp")
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
    regs['Brecha'] = regs['Pct'] - regs['obj']
    regs_s = regs.sort_values('Pct')

    r1,r2 = st.columns(2)
    with r1:
        st.markdown('<div class="card"><div class="card-title">% real vs objetivo vs best practice</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real', x='R'+regs_s['Region'], y=regs_s['Pct']*100,
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(regs_s['Pct'],regs_s['obj'])],
            text=[f"{v:.2f}%" for v in regs_s['Pct']*100], textposition='outside', textfont=dict(size=10)))
        fig.add_trace(go.Bar(name='Objetivo', x='R'+regs_s['Region'], y=regs_s['obj']*100, marker_color=C['obj']))
        fig.add_trace(go.Scatter(name='BP', x='R'+regs_s['Region'], y=regs_s['bp']*100,
            mode='markers+lines', line=dict(color=C['bp'],dash='dot',width=1.5), marker=dict(size=6,color=C['bp'])))
        fig.update_layout(**pb(), barmode='group', height=230, yaxis_ticksuffix='%')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2:
        st.markdown('<div class="card"><div class="card-title">Quiebra $ por region</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Bar(x='R'+regs_s['Region'], y=regs_s['Q']/1e6,
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(regs_s['Pct'],regs_s['obj'])],
            text=[f"-${abs(v):,.0f}M" for v in regs_s['Q']/1e6], textposition='outside', textfont=dict(size=10)))
        fig2.update_layout(**pb(), height=230, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r3,r4 = st.columns(2)
    with r3:
        st.markdown('<div class="card"><div class="card-title">Brecha PP vs objetivo</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(x='R'+regs_s['Region'], y=regs_s['Brecha']*100,
            marker_color=[C['red'] if v<0 else C['green'] for v in regs_s['Brecha']],
            text=[f"{v:+.2f}" for v in regs_s['Brecha']*100], textposition='outside', textfont=dict(size=10)))
        fig3.add_hline(y=0, line_color='#E2E5EC', line_width=1)
        fig3.update_layout(**pb(), height=190, showlegend=False, yaxis_ticksuffix=' pp')
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r4:
        st.markdown('<div class="card"><div class="card-title">Ventas por region</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Bar(x='R'+regs_s['Region'], y=regs_s['V']/1e9,
            marker_color=C['navy'], text=[f"${v:.1f}MM" for v in regs_s['V']/1e9],
            textposition='outside', textfont=dict(size=10)))
        fig4.update_layout(**pb(), height=190, showlegend=False, yaxis_ticksuffix='MM')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla con drill-down a DM
    st.markdown('<div class="card"><div class="card-title">Detalle — clic en una region para ver sus DMs</div>', unsafe_allow_html=True)
    for _,r in regs_s.iterrows():
        c1,c2,c3,c4,c5 = st.columns([3,2,2,2,2])
        if c1.button(f"{dot_txt(r['Pct'],r['obj'])} Reg. {r['Region']} {r['Zona']} →",
            key=f"reg_dm_{r['Region']}", use_container_width=True, help="Ver DMs de esta region"):
            nav_go(3, unidad=unidad_sel, zonas=[r['Zona']], regs=[r['Region']])
        c2.markdown(fmm(r['Q']))
        c3.markdown(f"{fmp(r['Pct'])} / {fmp(r['obj'])}")
        c4.markdown(f"BP: {fmp(r['bp'])}")
        c5.markdown(f"{r['Brecha']*100:+.2f} pp")
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 4: DM Y TIENDAS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    dms = agg(f,['Zona','Region','DM']).merge(
        obj_dm[['District Manager','Objetivo Quiebra %','Best Practice %','Quiebra Objetivo $']],
        left_on='DM', right_on='District Manager', how='left')
    dms['obj'] = dms['Objetivo Quiebra %']
    dms['bp']  = dms['Best Practice %']
    dms['Brecha'] = dms['Pct'] - dms['obj']
    dms_s = dms.sort_values('Pct')

    dm1,dm2 = st.columns(2)
    with dm1:
        st.markdown('<div class="card"><div class="card-title">% quiebra por DM — real vs objetivo</div>', unsafe_allow_html=True)
        top10 = dms_s.head(10)
        nombres = top10['DM'].apply(lambda x: x.split()[0]+' '+x.split()[-1])
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Real', y=nombres, x=top10['Pct']*100, orientation='h',
            marker_color=[C['red'] if r<o else C['green'] for r,o in zip(top10['Pct'],top10['obj'].fillna(0))]))
        fig.add_trace(go.Bar(name='Objetivo', y=nombres, x=top10['obj'].fillna(0)*100, orientation='h', marker_color=C['obj']))
        fig.add_trace(go.Scatter(name='BP', y=nombres, x=top10['bp'].fillna(0)*100,
            mode='markers', marker=dict(color=C['bp'],size=8,symbol='diamond')))
        fig.update_layout(**pb(), barmode='group', height=280, xaxis_ticksuffix='%', yaxis_autorange='reversed')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with dm2:
        st.markdown('<div class="card"><div class="card-title">Progreso vs objetivo</div>', unsafe_allow_html=True)
        for _,r in dms_s.head(8).iterrows():
            ratio = min(abs(r['Pct'])/abs(r['obj'])*50,100) if pd.notna(r['obj']) and r['obj'] != 0 else 50
            color = C['red'] if r['Pct'] < (r['obj'] or 0) else C['green']
            nombre = r['DM'].split()[0]+' '+r['DM'].split()[-1]
            obj_txt = fmp(r['obj']) if pd.notna(r['obj']) else 'S/O'
            st.markdown(f"""<div style="margin-bottom:8px">
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
                    <span style="color:#1A2540;font-weight:500">{nombre}</span>
                    <span style="color:{color};font-weight:500">{fmp(r['Pct'])}
                    <span style="color:#7B8FAE;font-weight:400"> obj {obj_txt}</span></span>
                </div>
                <div style="background:#F4F5F7;border-radius:3px;height:4px">
                    <div style="width:{ratio}%;background:{color};height:4px;border-radius:3px"></div>
                </div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    dm3,dm4 = st.columns(2)
    with dm3:
        st.markdown('<div class="card"><div class="card-title">Distribucion quiebra $ por zona</div>', unsafe_allow_html=True)
        zq = f.groupby('Zona')['Quiebra'].sum().reset_index()
        zq['Quiebra'] = zq['Quiebra'].abs()
        zq = zq.sort_values('Quiebra', ascending=False)
        fig3 = go.Figure(go.Pie(labels=zq['Zona'], values=zq['Quiebra'],
            hole=.5, marker_colors=[C['red'],'#8B4513',C['navy'],C['green']], textfont=dict(size=11)))
        fig3.update_layout(**pb(), height=190)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with dm4:
        st.markdown('<div class="card"><div class="card-title">Top 8 tiendas por quiebra $</div>', unsafe_allow_html=True)
        tt = f.groupby(['Tienda','DM','Region'],as_index=False).agg(Q=('Quiebra','sum'),V=('Ventas','sum')).nsmallest(8,'Q')
        fig4 = go.Figure(go.Bar(y=tt['Tienda'].apply(lambda x: x[:22]),x=tt['Q']/1e6, orientation='h',
            marker_color=C['red'], text=[f"-${abs(v):,.0f}M" for v in tt['Q']/1e6],
            textposition='outside', textfont=dict(size=10)))
        fig4.update_layout(**pb(), height=190, showlegend=False, yaxis_autorange='reversed')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tablas DM y tiendas con drill-down
    t1,t2 = st.columns(2)
    with t1:
        st.markdown('<div class="card"><div class="card-title">District Managers — clic para ver tiendas</div>', unsafe_allow_html=True)
        for _,r in dms_s.iterrows():
            c1,c2,c3,c4,c5 = st.columns([3,2,2,2,2])
            nombre = r['DM'].split()[0]+' '+r['DM'].split()[-1]
            c1.markdown(f"{dot(r['Pct'],r['obj'] or 0)} **{nombre}**", unsafe_allow_html=True)
            c2.markdown(fmm(r['Q']))
            obj_txt = fmp(r['obj']) if pd.notna(r['obj']) else 'S/O'
            c3.markdown(f"{fmp(r['Pct'])} / {obj_txt}")
            c4.markdown(f"{r['Brecha']*100:+.2f} pp" if pd.notna(r['Brecha']) else 'S/O')
            if c5.button("Ver", key=f"dm_ver_{r['DM']}_{r['Region']}_{r['Zona']}"):
                nav_go(3, unidad=unidad_sel, zonas=[r['Zona']], regs=[r['Region']], dms=[r['DM']])
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="card"><div class="card-title">Top 15 tiendas peores</div>', unsafe_allow_html=True)
        top15 = f.groupby(['Tienda','DM','AM','Region'],as_index=False).agg(
            V=('Ventas','sum'), Q=('Quiebra','sum'), QH=('QuiebraH','sum')
        ).nsmallest(15,'Q')
        top15['Pct']  = top15['Q'] / top15['V']
        top15['PctH'] = top15['QH'] / top15['V']
        ts = top15[['Tienda','DM','AM','Region','V','Q','Pct','PctH']].copy()
        ts.columns = ['Tienda','DM','AM','Reg','Ventas $','Quiebra $','% Real','% Hist']
        ts['Tienda']    = ts['Tienda'].apply(lambda x: x[:24])
        ts['DM']        = ts['DM'].apply(lambda x: x.split()[0]+' '+x.split()[-1])
        ts['Ventas $']  = ts['Ventas $'].apply(lambda x: f"${x/1e6:,.0f}M")
        ts['Quiebra $'] = ts['Quiebra $'].apply(lambda x: f"-${abs(x)/1e6:,.1f}M")
        ts['% Real']    = ts['% Real'].apply(lambda x: f"{x*100:.2f}%")
        ts['% Hist']    = ts['% Hist'].apply(lambda x: f"{x*100:.2f}%")
        st.dataframe(ts, use_container_width=True, hide_index=True, height=300)
        st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# FIN
# =============================================================================
