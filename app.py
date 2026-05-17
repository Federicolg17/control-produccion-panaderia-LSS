"""
╔══════════════════════════════════════════════════════════════════╗
║   SISTEMA DE REGISTRO DE PRODUCCIÓN - PANADERÍA                  ║
║   Stack: Streamlit + gspread + Google Sheets                     ║
║   Propósito: Base de datos histórica para Lean Six Sigma         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, datetime
import time

# ─────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL (MODIFICA AQUÍ)
# ─────────────────────────────────────────────

NOMBRE_HOJA = "Registro_Panaderia"      # Nombre de la pestaña en Google Sheets
NOMBRE_SPREADSHEET = "LSS_Panaderia"   # Nombre del archivo de Google Sheets

PRODUCTOS = [
    "Pan de Bono",
    "Pan Resbado",
    "Pan Rollo",
    "Pastel",
    "Pandebono Mini",
    "Croissant",
    "Almojábana",
    "Mogolla",
    "Buñuelo",
    "Otro",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CABECERAS = [
    "Fecha",
    "Producto",
    "Cantidad_Producida",
    "Cantidad_Vendida",
    "Merma",
    "Porcentaje_Merma",
    "Observaciones",
    "Timestamp_Registro",
]

# ─────────────────────────────────────────────
#  ESTILOS CSS PERSONALIZADOS
# ─────────────────────────────────────────────

CSS = """
<style>
  /* Importar fuentes */
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500;600&display=swap');

  /* Variables de color */
  :root {
    --cafe-oscuro:  #2C1A0E;
    --cafe-medio:   #6B3F1F;
    --cafe-claro:   #C8893C;
    --crema:        #FDF6EC;
    --blanco:       #FFFFFF;
    --verde-exito:  #2D7A4F;
    --rojo-error:   #C0392B;
    --gris-texto:   #4A4A4A;
    --borde:        #E8D5B7;
  }

  /* Reset de fondo */
  .stApp {
    background-color: var(--crema) !important;
    font-family: 'DM Sans', sans-serif;
  }

  /* Header superior */
  header[data-testid="stHeader"] {
    background-color: var(--cafe-oscuro) !important;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: var(--cafe-oscuro) !important;
    border-right: 3px solid var(--cafe-claro);
  }
  section[data-testid="stSidebar"] * {
    color: var(--crema) !important;
  }

  /* Título principal */
  h1 {
    font-family: 'Playfair Display', serif !important;
    color: var(--cafe-oscuro) !important;
    letter-spacing: -0.5px;
  }

  h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--cafe-medio) !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: var(--cafe-oscuro);
    border-radius: 12px;
    padding: 6px;
  }
  .stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: var(--crema) !important;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    border-radius: 8px;
    padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background-color: var(--cafe-claro) !important;
    color: var(--cafe-oscuro) !important;
    font-weight: 600;
  }

  /* Inputs y Selectbox */
  .stSelectbox > div > div,
  .stNumberInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stDateInput > div > div > input {
    background-color: var(--blanco) !important;
    border: 1.5px solid var(--borde) !important;
    border-radius: 10px !important;
    color: var(--cafe-oscuro) !important;
    font-family: 'DM Sans', sans-serif !important;
  }
  .stSelectbox > div > div:focus-within,
  .stNumberInput > div > div:focus-within,
  .stTextArea > div > div:focus-within {
    border-color: var(--cafe-claro) !important;
    box-shadow: 0 0 0 2px rgba(200,137,60,0.2) !important;
  }

  /* Labels */
  label[data-testid="stWidgetLabel"] p {
    color: var(--cafe-oscuro) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Botón primario */
  .stButton > button[kind="primary"],
  .stButton > button {
    background-color: var(--cafe-oscuro) !important;
    color: var(--crema) !important;
    border: 2px solid var(--cafe-claro) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.6rem 2rem !important;
    width: 100%;
    letter-spacing: 0.5px;
    transition: all 0.25s ease;
  }
  .stButton > button:hover {
    background-color: var(--cafe-claro) !important;
    color: var(--cafe-oscuro) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(200,137,60,0.3) !important;
  }

  /* Card de métricas */
  div[data-testid="stMetric"] {
    background-color: var(--blanco);
    border: 1.5px solid var(--borde);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(44,26,14,0.06);
  }
  div[data-testid="stMetric"] label {
    color: var(--cafe-medio) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--cafe-oscuro) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
  }

  /* Merma calculada */
  .merma-box {
    background: linear-gradient(135deg, var(--cafe-oscuro), #4A2C12);
    color: var(--crema);
    border-radius: 14px;
    padding: 18px 22px;
    margin: 8px 0;
    border: 1.5px solid var(--cafe-claro);
    box-shadow: 0 4px 15px rgba(44,26,14,0.15);
  }
  .merma-box .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--cafe-claro);
    font-weight: 600;
    margin-bottom: 4px;
  }
  .merma-box .value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
  }
  .merma-box .pct {
    font-size: 0.85rem;
    color: rgba(253,246,236,0.7);
    margin-top: 2px;
  }

  /* Divisor decorativo */
  .divider {
    border: none;
    border-top: 2px solid var(--borde);
    margin: 20px 0;
  }

  /* Alertas */
  .stAlert {
    border-radius: 12px !important;
  }

  /* Dataframe */
  .stDataFrame {
    border: 1.5px solid var(--borde) !important;
    border-radius: 12px !important;
    overflow: hidden;
  }

  /* Ajuste móvil */
  @media (max-width: 640px) {
    h1 { font-size: 1.6rem !important; }
    .merma-box .value { font-size: 1.5rem; }
  }
</style>
"""

# ─────────────────────────────────────────────
#  CONEXIÓN A GOOGLE SHEETS
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner="Conectando con Google Sheets…")
def conectar_gsheets():
    """
    Establece y cachea la conexión con Google Sheets.
    Lee las credenciales desde st.secrets (secrets.toml).
    Retorna el objeto worksheet listo para leer/escribir.
    """
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    cliente = gspread.authorize(creds)

    # Abrir (o crear) el spreadsheet
    try:
        spreadsheet = cliente.open(NOMBRE_SPREADSHEET)
    except gspread.SpreadsheetNotFound:
        st.error(
            f"❌ No se encontró el archivo **'{NOMBRE_SPREADSHEET}'** en Google Drive. "
            "Verifica el nombre exacto y que la cuenta de servicio tenga acceso."
        )
        st.stop()

    # Abrir (o crear) la hoja
    try:
        hoja = spreadsheet.worksheet(NOMBRE_HOJA)
    except gspread.WorksheetNotFound:
        hoja = spreadsheet.add_worksheet(title=NOMBRE_HOJA, rows=2000, cols=10)
        hoja.append_row(CABECERAS)   # Crear cabeceras automáticamente
        st.info(f"✅ Hoja '{NOMBRE_HOJA}' creada con cabeceras automáticamente.")

    # Si la hoja existe pero está vacía, agregar cabeceras
    if hoja.row_count == 0 or hoja.cell(1, 1).value is None:
        hoja.append_row(CABECERAS)

    return hoja


def leer_ultimos_registros(hoja, n: int = 10) -> pd.DataFrame:
    """Lee todos los registros y retorna los últimos N como DataFrame."""
    datos = hoja.get_all_records()
    if not datos:
        return pd.DataFrame(columns=CABECERAS)
    df = pd.DataFrame(datos)
    return df.tail(n).reset_index(drop=True)


def escribir_registro(hoja, fila: list) -> None:
    """Agrega una nueva fila al final del Google Sheet."""
    hoja.append_row(fila, value_input_option="USER_ENTERED")


# ─────────────────────────────────────────────
#  HELPERS DE UI
# ─────────────────────────────────────────────

def mostrar_merma(producida: int, vendida: int):
    """Muestra un card visual con el cálculo de merma."""
    merma = producida - vendida
    pct = (merma / producida * 100) if producida > 0 else 0
    color_pct = "#F39C12" if pct > 20 else "#2ECC71"
    html = f"""
    <div class="merma-box">
      <div class="label">📊 Merma / Desperdicio (Calculado)</div>
      <div class="value">{merma} unidades</div>
      <div class="pct" style="color:{color_pct};">
        {pct:.1f}% del total producido
        {'⚠️ Alta merma' if pct > 20 else '✅ Dentro del rango'}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    return merma, pct


def reset_formulario():
    """Limpia los valores del formulario usando session_state."""
    st.session_state["producto_idx"] = 0
    st.session_state["producida"] = 1
    st.session_state["vendida"] = 0
    st.session_state["obs"] = ""


# ─────────────────────────────────────────────
#  PÁGINA PRINCIPAL
# ─────────────────────────────────────────────

def main():
    # ── Configuración de la página ──────────────────
    st.set_page_config(
        page_title="Panadería LSS · Registro Diario",
        page_icon="🥐",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    # ── Inicializar session_state ───────────────────
    defaults = {"producto_idx": 0, "producida": 1, "vendida": 0, "obs": ""}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Header ─────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
          <span style="font-size:3rem;">🥐</span>
          <h1 style="margin:0; padding:0;">Registro de Producción</h1>
          <p style="color:#6B3F1F; font-size:0.95rem; margin-top:4px;">
            Sistema de trazabilidad diaria · Lean Six Sigma
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Conexión ────────────────────────────────────
    with st.spinner("Iniciando conexión con Google Sheets…"):
        try:
            hoja = conectar_gsheets()
        except Exception as e:
            st.error(
                f"⚠️ **Error de conexión con Google Sheets.**\n\n"
                f"Verifica tu conexión a internet y las credenciales en `secrets.toml`.\n\n"
                f"Detalle técnico: `{e}`"
            )
            st.stop()

    # ── Tabs principales ────────────────────────────
    tab_registro, tab_visualizacion = st.tabs(
        ["📝  Nuevo Registro", "📋  Últimos Registros"]
    )

    # ═══════════════════════════════════════════════
    #  TAB 1 · FORMULARIO DE REGISTRO
    # ═══════════════════════════════════════════════
    with tab_registro:
        st.markdown("### Ingresa los datos del día")
        st.markdown(
            "<p style='color:#6B3F1F; font-size:0.88rem;'>"
            "Todos los campos marcados son obligatorios.</p>",
            unsafe_allow_html=True,
        )

        col_fecha, col_prod = st.columns([1, 2])

        with col_fecha:
            fecha = st.date_input(
                "📅 Fecha",
                value=date.today(),
                help="Por defecto es hoy. Puedes cambiarlo si registras datos de días anteriores.",
            )

        with col_prod:
            producto = st.selectbox(
                "🍞 Producto",
                options=PRODUCTOS,
                index=st.session_state["producto_idx"],
                key="producto_select",
                help="Selecciona el producto que vas a registrar.",
            )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown("#### Cantidades")

        col_producida, col_vendida = st.columns(2)

        with col_producida:
            cantidad_producida = st.number_input(
                "🏭 Cantidad Producida",
                min_value=1,
                max_value=10_000,
                value=st.session_state["producida"],
                step=1,
                key="input_producida",
                help="Número total de unidades que se hornearon hoy.",
            )

        with col_vendida:
            cantidad_vendida = st.number_input(
                "💰 Cantidad Vendida",
                min_value=0,
                max_value=10_000,
                value=st.session_state["vendida"],
                step=1,
                key="input_vendida",
                help="Número de unidades que se vendieron al cliente final.",
            )

        # ── Merma calculada en tiempo real ──────────
        merma, pct_merma = mostrar_merma(cantidad_producida, cantidad_vendida)

        # ── Alertas de validación visual ────────────
        if cantidad_vendida > cantidad_producida:
            st.warning(
                "⚠️ **Alerta de inconsistencia:** La cantidad vendida supera la producida. "
                "Verifica los datos antes de guardar."
            )

        if pct_merma > 30:
            st.warning(
                f"🔴 **Alta merma detectada ({pct_merma:.1f}%):** "
                "Considera documentar la causa en el campo de Observaciones."
            )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        observaciones = st.text_area(
            "📝 Observaciones (opcional)",
            value=st.session_state["obs"],
            placeholder="Ej: Día lluvioso, menos clientes. Horno falló 30 min. Feriado local…",
            max_chars=500,
            height=100,
            key="input_obs",
            help="Notas libres. Muy útil para el análisis de causas raíz en LSS.",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Botón de registro ────────────────────────
        if st.button("✅  Registrar Datos", use_container_width=True):

            # Validaciones de negocio
            errores = []
            if cantidad_producida < 1:
                errores.append("La cantidad producida debe ser mayor a 0.")
            if cantidad_vendida > cantidad_producida:
                errores.append(
                    f"La cantidad vendida ({cantidad_vendida}) "
                    f"no puede superar la producida ({cantidad_producida})."
                )
            if merma < 0:
                errores.append("La merma no puede ser negativa. Revisa los valores.")

            if errores:
                for err in errores:
                    st.error(f"❌ {err}")
            else:
                # Construir fila para Google Sheets
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fila = [
                    str(fecha),
                    producto,
                    cantidad_producida,
                    cantidad_vendida,
                    merma,
                    round(pct_merma, 2),
                    observaciones.strip() if observaciones else "",
                    timestamp,
                ]

                # Intentar escritura con manejo de errores de red
                try:
                    with st.spinner("Guardando en Google Sheets…"):
                        escribir_registro(hoja, fila)
                        time.sleep(0.5)  # Pequeña pausa para UX

                    st.success(
                        f"🎉 **¡Registro guardado exitosamente!**\n\n"
                        f"**{producto}** · {fecha.strftime('%d/%m/%Y')} · "
                        f"Producido: {cantidad_producida} · "
                        f"Vendido: {cantidad_vendida} · "
                        f"Merma: {merma} ({pct_merma:.1f}%)"
                    )

                    # Limpiar session_state para resetear formulario
                    st.session_state["producida"] = 1
                    st.session_state["vendida"] = 0
                    st.session_state["obs"] = ""
                    time.sleep(1.2)
                    st.rerun()

                except gspread.exceptions.APIError as api_err:
                    st.error(
                        f"❌ **Error de API de Google Sheets:**\n\n"
                        f"No se pudo guardar el registro. Detalles: `{api_err}`\n\n"
                        "Asegúrate de que la cuenta de servicio tiene permiso de **Editor** en el archivo."
                    )

                except Exception as err:
                    st.error(
                        f"❌ **Error inesperado al guardar:**\n\n`{err}`\n\n"
                        "Verifica tu conexión a internet e intenta de nuevo."
                    )

        # ── Resumen del día (sidebar rápido) ─────────
        with st.expander("ℹ️ ¿Qué se guardará?", expanded=False):
            st.markdown(
                f"""
                | Campo | Valor |
                |---|---|
                | **Fecha** | {fecha.strftime('%d/%m/%Y')} |
                | **Producto** | {producto} |
                | **Producida** | {cantidad_producida} uds |
                | **Vendida** | {cantidad_vendida} uds |
                | **Merma** | {merma} uds ({pct_merma:.1f}%) |
                | **Observaciones** | {observaciones[:60] + '…' if len(observaciones) > 60 else observaciones or '—'} |
                """
            )

    # ═══════════════════════════════════════════════
    #  TAB 2 · VISUALIZACIÓN DE ÚLTIMOS REGISTROS
    # ═══════════════════════════════════════════════
    with tab_visualizacion:
        st.markdown("### Últimos 10 registros")
        st.markdown(
            "<p style='color:#6B3F1F; font-size:0.88rem;'>"
            "Datos cargados directamente desde Google Sheets.</p>",
            unsafe_allow_html=True,
        )

        col_btn, _ = st.columns([1, 3])
        with col_btn:
            refrescar = st.button("🔄 Actualizar datos", key="btn_refresh")

        if refrescar:
            st.cache_resource.clear()

        try:
            with st.spinner("Cargando registros…"):
                df = leer_ultimos_registros(hoja, n=10)

            if df.empty:
                st.info("📭 Aún no hay registros guardados. ¡Sé el primero en registrar!")
            else:
                # Métricas resumen de los últimos registros visibles
                st.markdown("#### Resumen de los registros mostrados")
                m1, m2, m3 = st.columns(3)

                total_prod = df["Cantidad_Producida"].sum() if "Cantidad_Producida" in df else 0
                total_vend = df["Cantidad_Vendida"].sum() if "Cantidad_Vendida" in df else 0
                total_merma = df["Merma"].sum() if "Merma" in df else 0

                m1.metric("🏭 Total Producido", f"{total_prod:,}")
                m2.metric("💰 Total Vendido", f"{total_vend:,}")
                m3.metric(
                    "🗑️ Total Merma",
                    f"{total_merma:,}",
                    delta=f"{(total_merma/total_prod*100):.1f}%" if total_prod > 0 else "0%",
                    delta_color="inverse",
                )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### Tabla de registros")

                # Formatear columnas numéricas
                cols_num = ["Cantidad_Producida", "Cantidad_Vendida", "Merma"]
                df_display = df.copy()
                for col in cols_num:
                    if col in df_display.columns:
                        df_display[col] = pd.to_numeric(df_display[col], errors="coerce").fillna(0).astype(int)

                if "Porcentaje_Merma" in df_display.columns:
                    df_display["Porcentaje_Merma"] = (
                        pd.to_numeric(df_display["Porcentaje_Merma"], errors="coerce")
                        .fillna(0)
                        .round(1)
                        .astype(str) + "%"
                    )

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Fecha": st.column_config.TextColumn("📅 Fecha", width="small"),
                        "Producto": st.column_config.TextColumn("🍞 Producto", width="medium"),
                        "Cantidad_Producida": st.column_config.NumberColumn("🏭 Producida", format="%d"),
                        "Cantidad_Vendida": st.column_config.NumberColumn("💰 Vendida", format="%d"),
                        "Merma": st.column_config.NumberColumn("🗑️ Merma", format="%d"),
                        "Porcentaje_Merma": st.column_config.TextColumn("% Merma", width="small"),
                        "Observaciones": st.column_config.TextColumn("📝 Observaciones", width="large"),
                        "Timestamp_Registro": st.column_config.TextColumn("🕐 Registrado", width="medium"),
                    },
                )

                st.caption(f"Mostrando los últimos {len(df_display)} registros de {NOMBRE_HOJA}.")

        except Exception as err:
            st.error(
                f"❌ **No se pudieron cargar los registros.**\n\n"
                f"Error: `{err}`\n\nVerifica tu conexión y vuelve a intentarlo."
            )

    # ── Footer ──────────────────────────────────────
    st.markdown(
        """
        <hr class='divider'>
        <p style='text-align:center; color:#9B7B5B; font-size:0.78rem; padding-bottom:1rem;'>
          🥐 Sistema de Registro Panadería · Lean Six Sigma Data Collection
        </p>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
