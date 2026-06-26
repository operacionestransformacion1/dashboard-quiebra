"""Historial de navegación tipo browser — guarda una pila de estados
{pestaña, filtros} para los botones atrás/adelante."""

from copy import deepcopy

import streamlit as st


DEFAULT_STATE = {'tab': 0, 'unidad': 'Ara', 'zonas': [], 'regs': [], 'dms': [], 'divs': []}


def nav_init():
    """Inicializa el historial si no existe."""
    if 'hist' not in st.session_state:
        st.session_state.hist = [deepcopy(DEFAULT_STATE)]
        st.session_state.pos = 0


def nav_reset():
    """Borra todo el historial y filtros, vuelve a la vista inicial."""
    st.session_state.hist = [deepcopy(DEFAULT_STATE)]
    st.session_state.pos = 0
    st.rerun()


def nav_push(state):
    """Agrega un estado al historial, descartando el futuro si existía."""
    st.session_state.hist = st.session_state.hist[:st.session_state.pos + 1]
    st.session_state.hist.append(deepcopy(state))
    st.session_state.pos = len(st.session_state.hist) - 1


def nav_back():
    if st.session_state.pos > 0:
        st.session_state.pos -= 1
        st.rerun()


def nav_fwd():
    if st.session_state.pos < len(st.session_state.hist) - 1:
        st.session_state.pos += 1
        st.rerun()


def nav_go(tab, unidad='Ara', zonas=None, regs=None, dms=None, divs=None):
    """Navega a una nueva vista y agrega al historial."""
    nav_push({'tab': tab, 'unidad': unidad, 'zonas': zonas or [],
              'regs': regs or [], 'dms': dms or [], 'divs': divs or []})
    st.rerun()
