"""
AquaMind SWRO – Executive Operations Dashboard
Nivel empresarial | Control Room Style | Alertas visuales | KPIs avanzados
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from io import StringIO
from datetime import datetime
import time

st.set_page_config(
    page_title="AquaMind SWRO | Executive Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================== ESTILO ENTERPRISE ======================
st.markdown("""
<style>
    .stApp { background-color: #0a0e17; color: #e8eaed; }
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
    h1 { font-size: 2.1rem; font-weight: 700; color: #ffffff; margin-bottom: 0.2rem; }
    h2 { font-size: 1.4rem; color: #c9d1d9; border-bottom: 1px solid #30363d; padding-bottom: 0.4rem; }
    h3 { color: #8b949e; font-size: 1.05rem; }
    
    .kpi-card {
        background: linear-gradient(145deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 18px 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.45);
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-value { font-size: 2.6rem; font-weight: 800; line-height: 1.1; }
    .kpi-label { font-size: 0.85rem; color: #8b949e; margin-top: 6px; letter-spacing: 0.5px; }
    .kpi-sub { font-size: 0.75rem; color: #6e7681; }
    
    .status-green { color: #3fb950; }
    .status-yellow { color: #d29922; }
    .status-red { color: #f85149; }
    .status-blue { color: #58a6ff; }
    
    .alert-card {
        border-radius: 10px;
        padding: 14px 16px;
        margin: 8px 0;
        border-left: 5px solid;
        background: #161b22;
    }
    .alert-high { border-left-color: #f85149; background: #2d1214; }
    .alert-medium { border-left-color: #d29922; background: #2d2414; }
    .alert-low { border-left-color: #3fb950; background: #12261e; }
    .alert-info { border-left-color: #58a6ff; background: #121d2d; }
    
    .header-bar {
        background: linear-gradient(90deg, #0d1117 0%, #161b22 100%);
        padding: 12px 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ====================== CONFIG ======================
SHEET_URL = "https://docs.google.com/spreadsheets/d/14gRV6bJBCoe_aG16q8UeRjC5dqWMvzL34KZY76fSwR4/export?format=csv&gid=0"
OBJETIVO = 3326.0
LIMITE_COND = 1500.0

# ====================== CARGA ======================
@st.cache_data(ttl=55)
def load_data():
    try:
        r = requests.get(SHEET_URL, timeout=20)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text), skiprows=5, low_memory=False)
        df['fecha'] = pd.to_datetime(df['Día'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['fecha']).sort_values('fecha').reset_index(drop=True)

        col_map = {
            'caudal_auto': 4, 'turb_tk': 24, 'temp_tk': 27, 'cond_tk': 29, 'cloro_tk': 28,
            'prod_total': 121, 'cond_perm': 128, 'cn': 91, 'di': 112, 'dj': 113, 'dv': 125,
            'dp_a': 179, 'perm_a': 181, 'rech_a': 182,
            'dp_b': 186, 'perm_b': 188, 'rech_b': 189,
            'dp_c': 193, 'perm_c': 195, 'rech_c': 196,
            'dp_d': 200, 'perm_d': 202, 'rech_d': 203,
            'dp_e': 207, 'perm_e': 210, 'rech_e': 211,
            'turb_ufn': 75, 'tpm_ufn': 76, 'sdi3': 82,
            'tpm_ufi201': 54, 'tpm_ufi202': 55, 'tpm_ufi203': 56,
        }
        for name, idx in col_map.items():
            if idx < len(df.columns):
                df[name] = pd.to_numeric(df.iloc[:, idx], errors='coerce')

        df['produccion_real'] = df['cn'].fillna(0) + df['di'].fillna(0) + df['dj'].fillna(0)
        for t in ['a','b','c','d','e']:
            p = df[f'perm_{t}'].fillna(0)
            r = df[f'rech_{t}'].fillna(0)
            df[f'rec_{t}'] = np.where((p + r) > 0, 100 * p / (p + r), np.nan)
        return df
    except Exception as e:
        st.error(f"Error de conexión con Google Sheet: {e}")
        return pd.DataFrame()

def get_record_vigente(df):
    if df.empty:
        return None, "Sin datos"
    now = datetime.now()
    last = df.iloc[-1]
    if now.hour < 19:
        if len(df) > 1 and last['fecha'].date() == now.date():
            return df.iloc[-2], f"Cierre anterior · {df.iloc[-2]['fecha'].strftime('%d/%m/%Y')}"
        return last, f"Último cierre · {last['fecha'].strftime('%d/%m/%Y')}"
    return last, f"Cierre del día · {last['fecha'].strftime('%d/%m/%Y')} (≥19:00)"

# ====================== HEADER ======================
st.markdown('<div class="header-bar">', unsafe_allow_html=True)
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# 💧 AquaMind SWRO")
    st.markdown("**Executive Operations Dashboard** · Seawater Reverse Osmosis Plant")
with col_h2:
    st.markdown(f"<div style='text-align:right; color:#8b949e; font-size:0.9rem;'>Actualizado<br><b>{datetime.now().strftime('%d/%m/%Y %H:%M')}</b></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

df = load_data()
record, msg_status = get_record_vigente(df)

if record is None or df.empty:
    st.error("No hay datos disponibles. Verifica la conexión.")
    st.stop()

st.success(f"**Registro vigente:** {msg_status}")

# ====================== KPIs PRINCIPALES ======================
st.subheader("KPIs Críticos del Día")

prod = float(record.get('produccion_real', 0) or 0)
pct = (prod / OBJETIVO * 100) if OBJETIVO else 0
cond = float(record.get('cond_perm', 0) or record.get('dv', 0) or 0)
rec_a = float(record.get('rec_a', 0) or 0)
turb = float(record.get('turb_tk', 0) or 0)
temp = float(record.get('temp_tk', 0) or 0)
dp_a = float(record.get('dp_a', 0) or 0)

def status_class(value, good, warn):
    if value >= good: return "status-green"
    if value >= warn: return "status-yellow"
    return "status-red"

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value status-blue">{prod:,.0f}</div>
        <div class="kpi-label">PRODUCCIÓN REAL</div>
        <div class="kpi-sub">m³/d · CN+(DI+DJ)</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    sc = status_class(pct, 90, 70)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value {sc}">{pct:.1f}%</div>
        <div class="kpi-label">VS OBJETIVO</div>
        <div class="kpi-sub">{OBJETIVO:,.0f} m³/d</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    sc_c = "status-green" if cond < LIMITE_COND else "status-red"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value {sc_c}">{cond:,.0f}</div>
        <div class="kpi-label">COND. PERMEADO</div>
        <div class="kpi-sub">µS/cm · Límite {LIMITE_COND}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    sc_r = status_class(rec_a, 40, 32)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value {sc_r}">{rec_a:.1f}%</div>
        <div class="kpi-label">RECUPERACIÓN A</div>
        <div class="kpi-sub">Tren A</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    sc_t = "status-green" if turb < 5 else "status-yellow" if turb < 10 else "status-red"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value {sc_t}">{turb:.1f}</div>
        <div class="kpi-label">TURBIDEZ TK</div>
        <div class="kpi-sub">NTU · Captación</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value status-blue">{temp:.1f}</div>
        <div class="kpi-label">TEMPERATURA</div>
        <div class="kpi-sub">°C · Agua de mar</div>
    </div>
    """, unsafe_allow_html=True)

# ====================== ALERTAS VISUALES ======================
st.subheader("Sistema de Alertas Inteligentes")

alerts = []

if pct < 70:
    alerts.append(("high", "Producción crítica", f"Solo {pct:.1f}% del objetivo. Revisar disponibilidad de trenes y recuperación."))
elif pct < 90:
    alerts.append(("medium", "Producción por debajo del objetivo", f"{pct:.1f}% del objetivo de {OBJETIVO:,.0f} m³/d."))

if cond > LIMITE_COND:
    alerts.append(("high", "Conductividad fuera de especificación", f"{cond:,.0f} µS/cm (límite {LIMITE_COND})."))

if turb > 10:
    alerts.append(("high", "Turbidez elevada en captación", f"{turb:.1f} NTU. Riesgo de carga al pretratamiento."))
elif turb > 5:
    alerts.append(("medium", "Turbidez en zona de atención", f"{turb:.1f} NTU en tanque de concreto."))

if dp_a > 35:
    alerts.append(("medium", "ΔP Tren A elevado", f"{dp_a:.1f} PSI. Monitorear tendencia de fouling."))

if not alerts:
    alerts.append(("low", "Operación estable", "Todos los parámetros críticos dentro de rangos normales."))

for level, title, msg in alerts:
    st.markdown(f"""
    <div class="alert-card alert-{level}">
        <strong>{title}</strong><br>
        <span style="color:#c9d1d9;">{msg}</span>
    </div>
    """, unsafe_allow_html=True)

# ====================== GRÁFICAS ======================
st.subheader("Tendencias Operativas")

df_plot = df.tail(120).copy()
tab1, tab2, tab3 = st.tabs(["Captación", "SWRO – ΔP & Recuperación", "Producción"])

with tab1:
    fig = make_subplots(rows=2, cols=2, subplot_titles=("Caudal Autocebantes (l/s)", "Temperatura (°C)", "Conductividad (mS/cm)", "Turbidez TK (NTU)"))
    fig.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot.caudal_auto, line=dict(color="#58a6ff", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot.temp_tk, line=dict(color="#f85149", width=2)), row=1, col=2)
    fig.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot.cond_tk/1000, line=dict(color="#3fb950", width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot.turb_tk, line=dict(color="#d29922", width=2)), row=2, col=2)
    fig.update_layout(template="plotly_dark", height=620, showlegend=False, paper_bgcolor="#0a0e17", plot_bgcolor="#0d1117")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    colors = ["#58a6ff", "#f85149", "#3fb950", "#d29922", "#bc8cff"]
    for i, t in enumerate(['a','b','c','d','e']):
        fig2.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot[f'dp_{t}'], name=f"Tren {t.upper()}", line=dict(color=colors[i], width=2)))
    fig2.update_layout(template="plotly_dark", height=420, title="Diferencial de Presión (PSI)", paper_bgcolor="#0a0e17", plot_bgcolor="#0d1117")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = go.Figure()
    for i, t in enumerate(['a','b','c','d']):
        fig3.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot[f'rec_{t}'], name=f"Tren {t.upper()}", line=dict(color=colors[i], width=2)))
    fig3.update_layout(template="plotly_dark", height=380, title="Recuperación por Tren (%)", paper_bgcolor="#0a0e17", plot_bgcolor="#0d1117")
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df_plot.fecha, y=df_plot.produccion_real, name="Producción Real", line=dict(color="#58a6ff", width=3), fill="tozeroy", fillcolor="rgba(88,166,255,0.1)"))
    fig4.add_hline(y=OBJETIVO, line_dash="dash", line_color="#3fb950", annotation_text="Objetivo")
    fig4.update_layout(template="plotly_dark", height=450, paper_bgcolor="#0a0e17", plot_bgcolor="#0d1117")
    st.plotly_chart(fig4, use_container_width=True)

st.caption("AquaMind SWRO · Executive Dashboard · Cierre diario 19:00 · Actualización automática cada 60 segundos · Datos en tiempo real desde Google Sheets")

# Auto-refresh
time.sleep(60)
st.rerun()
