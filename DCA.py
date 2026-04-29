import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import curve_fit

# -------------------------------------------------
# Configuración general
# -------------------------------------------------
st.set_page_config(page_title="Decline Curve Analysis", layout="wide")
st.title("Decline Curve Analysis (DCA)")

# -------------------------------------------------
# Carga de datos
# -------------------------------------------------
st.subheader("Carga de datos")

uploaded_file = st.file_uploader(
    "Cargar archivo Excel (primera columna = fecha)",
    type=["xlsx"]
)

# -------------------------------------------------
# Lectura genérica del Excel
# -------------------------------------------------
@st.cache_data(show_spinner=True)
def read_excel(file):
    df = pd.read_excel(file, engine="openpyxl")

    # Primera columna = fecha
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")

    df = df.dropna(subset=[date_col])
    df = df.sort_values(date_col)

    return df, date_col

# -------------------------------------------------
# Cargar archivo
# -------------------------------------------------
if uploaded_file is None:
    st.warning("Por favor cargue un archivo Excel para continuar.")
    st.stop()

try:
    df_all, date_col = read_excel(uploaded_file)
    st.success("Archivo cargado correctamente.")
except Exception as e:
    st.error(f"No se pudo leer el archivo: {e}")
    st.stop()

# -------------------------------------------------
# Detectar columnas candidatas (todas menos fecha)
# -------------------------------------------------
value_columns = [
    c for c in df_all.columns
    if c != date_col and pd.api.types.is_numeric_dtype(df_all[c])
]

if len(value_columns) == 0:
    st.error("El archivo no contiene columnas numéricas para realizar DCA.")
    st.stop()

# -------------------------------------------------
# Selección de curva para declino
# -------------------------------------------------
st.sidebar.subheader("Curva usada para el declino")

selected_curve = st.sidebar.selectbox(
    "Seleccionar columna para DCA",
    value_columns
)

# -------------------------------------------------
# Selección de curvas visibles
# -------------------------------------------------
st.sidebar.subheader("Curvas visibles en el gráfico")

visible_curves = st.sidebar.multiselect(
    "Seleccionar curvas a mostrar",
    value_columns,
    default=value_columns
)

# -------------------------------------------------
# DataFrame para ajuste
# -------------------------------------------------
df_fit_source = (
    df_all[[date_col, selected_curve]]
    .rename(columns={selected_curve: "Rate"})
    .dropna()
)

df_fit_source = df_fit_source[df_fit_source["Rate"] > 0]

if len(df_fit_source) < 10:
    st.error("Muy pocos datos válidos para realizar el DCA.")
    st.stop()

# -------------------------------------------------
# Selección del tramo temporal
# -------------------------------------------------
st.sidebar.subheader("Tramo usado para el ajuste")

start_idx, end_idx = st.sidebar.slider(
    "Rango de datos",
    min_value=0,
    max_value=len(df_fit_source) - 1,
    value=(0, len(df_fit_source) - 1),
    step=1
)

df_fit = df_fit_source.iloc[start_idx:end_idx + 1].copy()

# -------------------------------------------------
# Tiempo en días
# -------------------------------------------------
t0 = df_fit[date_col].iloc[0]
df_fit["t"] = (df_fit[date_col] - t0).dt.days

# -------------------------------------------------
# Modelo hiperbólico
# -------------------------------------------------
def hyperbolic(t, qi, Di, b):
    return qi / ((1 + b * Di * t) ** (1 / b))

# -------------------------------------------------
# Ajuste del DCA
# -------------------------------------------------
p0 = [df_fit["Rate"].iloc[0], 0.001, 0.5]

try:
    popt, _ = curve_fit(
        hyperbolic,
        df_fit["t"],
        df_fit["Rate"],
        p0=p0,
        bounds=(0, [np.inf, 1, 2])
    )
except Exception as e:
    st.error(f"No se pudo ajustar el declino: {e}")
    st.stop()

qi, Di, b = popt

# -------------------------------------------------
# Declino anual efectivo del forecast
# -------------------------------------------------
last_real_date = df_all[date_col].max()
last_real_t = (last_real_date - t0).days

q_t0 = hyperbolic(last_real_t, qi, Di, b)
q_t365 = hyperbolic(last_real_t + 365, qi, Di, b)

declino_anual_forecast = (q_t0 - q_t365) / q_t0 * 100

# -------------------------------------------------
# Pronóstico
# -------------------------------------------------
forecast_days = st.sidebar.number_input(
    "Días de pronóstico",
    min_value=30, max_value=5000, value=365, step=30
)

t_forecast = np.arange(
    0, (df_all[date_col].max() - t0).days + forecast_days
)

q_forecast = hyperbolic(t_forecast, qi, Di, b)
dates_forecast = t0 + pd.to_timedelta(t_forecast, unit="D")

# -------------------------------------------------
# Resultados
# -------------------------------------------------
st.info(
    f"Curva usada: {selected_curve}  |  "
    f"qi = {qi:.2f}  |  "
    f"Di = {Di:.5f} 1/d  |  "
    f"b = {b:.3f}  |  "
    f"Declino anual (forecast) = {declino_anual_forecast:.1f} %"
)

# -------------------------------------------------
# DataFrame para exportación
# -------------------------------------------------

# Partimos del DataFrame original
df_export = df_all[[date_col]].copy()

# Agregamos solo las curvas visibles
for col in visible_curves:
    df_export[col] = df_all[col]

# DataFrame del declino
df_decline = pd.DataFrame({
    date_col: dates_forecast,
    "Declino_ajustado": q_forecast
})

# Merge (outer para no perder fechas)
df_export = pd.merge(
    df_export,
    df_decline,
    on=date_col,
    how="outer"
)

# Orden final
df_export = df_export.sort_values(date_col)

# -------------------------------------------------
# Gráfico
# -------------------------------------------------
fig = go.Figure()

for col in visible_curves:
    fig.add_trace(go.Scatter(
        x=df_all[date_col],
        y=df_all[col],
        mode="markers",
        name=col,
        marker=dict(size=6),
    ))

fig.add_trace(go.Scatter(
    x=dates_forecast,
    y=q_forecast,
    mode="lines",
    name="Declino ajustado",
    line=dict(color="black", width=3),
))

fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Producción",
    template="plotly_white",
    hovermode="x unified",
    legend_title="Series"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# Descargar resultados
# -------------------------------------------------
import io


st.subheader("Descarga de resultados")


buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_export.to_excel(writer, index=False, sheet_name="DCA")

st.download_button(
    label="Descargar datos y declino (Excel)",
    data=buffer.getvalue(),
    file_name="DCA_resultados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)