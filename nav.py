"""Historial de navegación tipo browser — guarda una pila de estados
{pestaña, filtros} para los botones atrás/adelante."""

from copy import deepcopy

import streamlit as st


def nav_init():
    """Inicializa el historial si no existe."""
    if 'hist' not in st.session_state:
        st.session_state.hist = [{'tab': 0, 'unidad': 'Ara', 'zona': 'Todas', 'regs': [], 'dms': [], 'divs': []}]
        st.session_state.pos = 0


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


def nav_go(tab, unidad='Ara', zona='Todas', regs=None, dms=None, divs=None):
    """Navega a una nueva vista y agrega al historial."""
    nav_push({'tab': tab, 'unidad': unidad, 'zona': zona,
              'regs': regs or [], 'dms': dms or [], 'divs': divs or []})
    st.rerun()
