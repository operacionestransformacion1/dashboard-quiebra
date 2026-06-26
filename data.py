"""Carga de datos desde Google Drive: CSV de tiendas y Excel de objetivos."""

import gdown
import pandas as pd
import streamlit as st

TIENDAS_PATH = '/tmp/tiendas.csv'
OBJ_PATH = '/tmp/obj.xlsx'

COLUMNS = ['Unidad', 'Zona', 'Region', 'DM', 'AM', 'CodT', 'Tienda',
           'CodDiv', 'Div', 'VR', 'VH', 'QR', 'QPR', 'QH', 'QPH', 'DP', 'DQ']


def _to_number(v):
    try:
        return float(str(v).replace(',', '').strip())
    except (ValueError, TypeError):
        return None


def _to_pct(v):
    try:
        return float(str(v).replace('%', '').replace(',', '').strip()) / 100
    except (ValueError, TypeError):
        return None


@st.cache_data(ttl=3600)
def load_data():
    url_t = f"https://drive.google.com/uc?id={st.secrets['ID_TIENDAS']}"
    url_o = f"https://drive.google.com/uc?id={st.secrets['ID_OBJ']}"
    gdown.download(url_t, TIENDAS_PATH, quiet=True)
    gdown.download(url_o, OBJ_PATH, quiet=True)

    raw = pd.read_csv(TIENDAS_PATH, encoding='latin-1', dtype=str)
    raw.columns = COLUMNS
    raw = raw[raw['Unidad'].isin(['Ara', 'BdC', 'Ara Franquicia'])]
    raw = raw[~raw['Zona'].isin(['NO ASIGNADA', 'Total Ara sin BDC', 'Total Ara sin BDC y FRA'])]
    raw = raw[raw['Tienda'].notna() & raw['Div'].notna()]
    # Excluir CEDIs y centros de distribución
    raw = raw[~raw['Tienda'].str.contains('CEDI|CENTRO DISTRIBU|C. DISTRIBUCION', case=False, na=False)]

    for c in ['VR', 'VH', 'QR', 'QH', 'DP', 'DQ']:
        raw[c] = raw[c].apply(_to_number)
    raw['QPR'] = raw['QPR'].apply(_to_pct)
    raw['QPH'] = raw['QPH'].apply(_to_pct)
    raw['Region'] = raw['Region'].apply(lambda x: str(x).zfill(2) if pd.notna(x) and str(x).strip().isdigit() else x)
    raw = raw.rename(columns={'VR': 'Ventas', 'VH': 'VentasH', 'QR': 'Quiebra', 'QH': 'QuiebraH'})

    obj_div = pd.read_excel(OBJ_PATH, sheet_name='Obj_Divisiones')
    obj_reg = pd.read_excel(OBJ_PATH, sheet_name='Obj_Regiones')
    obj_dm = pd.read_excel(OBJ_PATH, sheet_name='Obj_DM')
    obj_reg['Cod. Region'] = obj_reg['Cod. Region'].astype(str).str.zfill(2)

    return raw, obj_div, obj_reg, obj_dm
