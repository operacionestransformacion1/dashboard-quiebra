"""Helpers de formato, agregación y estilo de gráficos."""

import pandas as pd

C = {'red': '#C5372C', 'green': '#2D7A4F', 'navy': '#1A2540', 'obj': 'rgba(26,37,64,.15)', 'bp': '#E67700'}


def fmm(v):
    if v is None or pd.isna(v):
        return 'N/A'
    return f"-${abs(v)/1e6:,.1f} M" if v < 0 else f"${v/1e6:,.1f} M"


def fmp(v):
    if v is None or pd.isna(v):
        return 'N/A'
    return f"{v*100:.2f}%"


def pill(zona):
    cls = {'NORTE': 'pn', 'CENTRO': 'pc', 'OCCIDENTE': 'po', 'ANTIOQUIA': 'pa'}.get(str(zona).upper(), 'pn')
    return f'<span class="pill {cls}">{zona}</span>'


def dot(real, obj):
    if real is None or obj is None:
        return ''
    return '<span class="ib"></span>' if real < obj else '<span class="ig"></span>'


def agg(df, keys):
    g = df.groupby(keys, as_index=False).agg(V=('Ventas', 'sum'), VH=('VentasH', 'sum'), Q=('Quiebra', 'sum'), QH=('QuiebraH', 'sum'))
    g['Pct'] = (g['Q'] / g['V']).where(g['V'] != 0)
    g['PctH'] = (g['QH'] / g['VH']).where(g['VH'] != 0)
    return g


def pb():
    return dict(font=dict(family='Inter', size=11, color='#4A5568'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=6, r=6, t=20, b=6),
        xaxis=dict(gridcolor='#F0F1F4', linecolor='#E2E5EC', tickfont=dict(size=10)),
        yaxis=dict(gridcolor='#F0F1F4', linecolor='#E2E5EC', tickfont=dict(size=10)),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)))
