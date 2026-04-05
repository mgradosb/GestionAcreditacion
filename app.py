import streamlit as st
import pandas as pd
import io
import base64
from controller import TorneoController

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Wendy Chac Open 2026", layout="centered")

if 'torneo' not in st.session_state:
    st.session_state.torneo = TorneoController()

if 'dni_v' not in st.session_state:
    st.session_state.dni_v = ""
if 'w_key' not in st.session_state:
    st.session_state.w_key = 0

st.markdown("<h2 style='text-align: center;'>🏆 Wendy Chac Open 2026</h2>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Validación", "➕ Gestión y Carga", "📋 Reporte", "📊 Dashboard"])

# --- TAB 1: VALIDACIÓN ---
with tab1:
    dni = st.text_input("DNI:", value=st.session_state.dni_v, key=f"i_{st.session_state.w_key}")
    
    c_nav1, c_nav2 = st.columns(2)
    with c_nav1: 
        st.button("Validar Acceso", type="primary", width='stretch')
    with c_nav2: 
        if st.button("Limpiar Pantalla", width='stretch'):
            st.session_state.dni_v = ""; st.session_state.w_key += 1; st.rerun()

    if dni:
        res = st.session_state.torneo.buscar_por_dni(dni)
        if not res.empty:
            p = res.iloc[0]
            bg, txt = st.session_state.torneo.obtener_color_perfil(p['cargo'])
            qr_b64 = base64.b64encode(st.session_state.torneo.generar_qr(p['dni'])).decode()
            
            # --- GAFETE CON ETIQUETAS Y QR ---
            st.markdown(f"""
                <div style="display: flex; gap: 10px; margin-top: 10px; align-items: stretch;">
                    <div style="flex: 1.2; background-color: {bg}; padding: 15px; border-radius: 12px; border-left: 8px solid {txt}; display: flex; flex-direction: column; justify-content: center; min-height: 170px;">
                        <small style="color: {txt}; font-weight: bold; text-transform: uppercase; font-size: 0.7em;">Nombres</small>
                        <h3 style="margin:0; line-height: 0.9; font-size: 1.4em; color: #1e1e1e;">{p['nombre']}</h3>
                        <div style="margin-top: 5px;"></div>
                        <small style="color: {txt}; font-weight: bold; text-transform: uppercase; font-size: 0.7em;">Apellidos</small>
                        <h3 style="margin:0; line-height: 0.9; font-size: 1.4em; color: #1e1e1e;">{p['apellido']}</h3>
                        <div style="margin-top: 10px; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 5px;">
                            <b style="color: black;">DNI: {p['dni']}</b> | <b style="color: {txt}; text-transform: uppercase;">{p['cargo']}</b>
                        </div>
                    </div>
                    <div style="flex: 0.8; background-color: white; border: 1px solid #eee; border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 170px;">
                        <img src="data:image/png;base64,{qr_b64}" style="width: 125px;">
                        <p style="margin-top: -5px; font-weight: bold; color: #444; font-size: 0.7em; text-align: center;">Escanee para validar ID</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # --- FILA DE TIEMPOS ---
            st.write("")
            es_p = "Pre" in str(p['fecha_ingreso']) or not p['fecha_ingreso']
            ya_s = bool(p['fecha_salida'])
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                if not es_p: st.success(f"📥 Entró: {p['fecha_ingreso']}")
                else: st.info("⏳ Pendiente de Ingreso")
            with col_t2:
                if ya_s: st.error(f"📤 Salió: {p['fecha_salida']}")
                else: st.warning("🏃 En Recinto")

            # --- BOTONES DE ACCIÓN ---
            st.write("")
            b1, b2 = st.columns(2)
            with b1: 
                if st.button("✅ REGISTRAR INGRESO", width='stretch', disabled=not es_p or ya_s):
                    st.session_state.torneo.actualizar_ingreso(p['dni']); st.rerun()
            with b2:
                if st.button("🚪 REGISTRAR SALIDA", width='stretch', disabled=es_p or ya_s):
                    st.session_state.torneo.registrar_salida(p['dni']); st.rerun()
        else:
            # --- BÚSQUEDA POR NOMBRE / APELLIDO (RESTAURADA) ---
            st.error("DNI no encontrado.")
            st.write("---")
            st.subheader("🔍 Buscar por Nombre / Apellido")
            ape_search = st.text_input("Escriba el apellido:")
            if ape_search:
                sug = st.session_state.torneo.buscar_por_apellido(ape_search)
                if not sug.empty:
                    st.info("Seleccione una opción:")
                    for _, row in sug.iterrows():
                        if st.button(f"👤 {row['nombre']} {row['apellido']} (DNI: {row['dni']})", width='stretch', key=f"s_{row['dni']}"):
                            st.session_state.dni_v = str(row['dni'])
                            st.session_state.w_key += 1
                            st.rerun()
                else:
                    st.warning("No se encontraron coincidencias.")

# --- TABS GESTIÓN, REPORTE Y DASHBOARD ---
with tab2:
    accion = st.radio("Acción:", ["Nuevo Registro", "Actualizar Datos", "Carga Masiva Excel"], horizontal=True)
    if accion == "Nuevo Registro":
        with st.form("f_new"):
            d, n, a = st.text_input("DNI:"), st.text_input("Nombres:"), st.text_input("Apellidos:")
            c = st.selectbox("Perfil:", ["Atleta", "Familiar", "Staff", "Juez"])
            if st.form_submit_button("Guardar", width='stretch'):
                ok, msg = st.session_state.torneo.registrar_persona(d, n, a, c)
                st.success(msg) if ok else st.error(msg)
    elif accion == "Actualizar Datos":
        d_edit = st.text_input("DNI a buscar para editar:")
        if d_edit:
            res_e = st.session_state.torneo.buscar_por_dni(d_edit)
            if not res_e.empty:
                pe = res_e.iloc[0]
                with st.form("f_upd"):
                    nn, na = st.text_input("Nombres:", value=pe['nombre']), st.text_input("Apellidos:", value=pe['apellido'])
                    nc = st.selectbox("Perfil:", ["Atleta", "Familiar", "Staff", "Juez"], index=["Atleta", "Familiar", "Staff", "Juez"].index(pe['cargo']))
                    if st.form_submit_button("Actualizar", width='stretch'):
                        ok, msg = st.session_state.torneo.actualizar_persona(d_edit, nn, na, nc)
                        st.success(msg) if ok else st.error(msg)
    elif accion == "Carga Masiva Excel":
        f_up = st.file_uploader("Subir .xlsx", type=['xlsx'])
        if f_up and st.button("Procesar Lista", width='stretch'):
            ok, msg = st.session_state.torneo.cargar_masivo(pd.read_excel(f_up))
            st.success(msg) if ok else st.error(msg)

with tab3:
    df_full = st.session_state.torneo.obtener_datos()
    st.dataframe(df_full, width='stretch', hide_index=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as w: df_full.to_excel(w, index=False)
    st.download_button("📥 Descargar Reporte", data=buf.getvalue(), file_name="Reporte.xlsx", width='stretch')

with tab4:
    m = st.session_state.torneo.obtener_metricas()
    if m:
        c1, c2, c3 = st.columns(3)
        c1.metric("Padrón", m['padrón']); c2.metric("En Recinto", m['en_recinto']); c3.metric("Salidas", m['ya_salieron'])
        st.bar_chart(data=m['por_cargo'], x="Cargo", y="Cantidad", color="Cargo", width='stretch')