import pandas as pd
import streamlit as st
import os
import qrcode
from io import BytesIO
from datetime import datetime
from thefuzz import fuzz, process

class TorneoController:
    def __init__(self, file_path="datos.xlsx"):
        self.file_path = file_path
        self.columns = ['dni', 'nombre', 'apellido', 'cargo', 'fecha_ingreso', 'fecha_salida']
        self._inicializar_db()

    def _inicializar_db(self):
        if not os.path.exists(self.file_path):
            pd.DataFrame(columns=self.columns).to_excel(self.file_path, index=False)
        else:
            df = pd.read_excel(self.file_path, dtype={'dni': str})
            for col in self.columns:
                if col not in df.columns: df[col] = ""
            df.to_excel(self.file_path, index=False)

    def obtener_datos(self):
        # Limpiamos caché para asegurar datos frescos
        return pd.read_excel(self.file_path, dtype={'dni': str}).fillna('')

    def obtener_color_perfil(self, perfil):
        p = str(perfil).lower()
        if "atleta" in p: return "#E3F2FD", "#1976D2"
        if "familiar" in p: return "#E8F5E9", "#2E7D32"
        if "staff" in p or "juez" in p: return "#FFFDE7", "#FBC02D"
        return "#F5F5F5", "#616161"

    def generar_qr(self, dni):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(str(dni))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def buscar_por_dni(self, dni):
        df = self.obtener_datos()
        return df[df['dni'].str.strip() == str(dni).strip()]

    # --- ESTE ES EL MÉTODO QUE FALTABA ---
    def buscar_por_apellido(self, apellido_buscado):
        df = self.obtener_datos()
        if df.empty: return pd.DataFrame()
        # Obtenemos lista de apellidos únicos para comparar
        lista_apellidos = df['apellido'].astype(str).unique().tolist()
        # Usamos fuzzy matching para encontrar parecidos (útil por errores de tildes o dedos)
        matches = process.extract(apellido_buscado, lista_apellidos, limit=5, scorer=fuzz.token_set_ratio)
        apellidos_validos = [m[0] for m in matches if m[1] > 60] # Umbral de similitud
        return df[df['apellido'].isin(apellidos_validos)]

    def actualizar_ingreso(self, dni):
        df = self.obtener_datos()
        dni_l = str(dni).strip()
        ahora = datetime.now().strftime("%H:%M")
        df.loc[df['dni'] == dni_l, 'fecha_ingreso'] = ahora
        df.to_excel(self.file_path, index=False)
        st.cache_data.clear()
        return True

    def registrar_salida(self, dni):
        df = self.obtener_datos()
        dni_l = str(dni).strip()
        ahora = datetime.now().strftime("%H:%M")
        df.loc[df['dni'] == dni_l, 'fecha_salida'] = ahora
        df.to_excel(self.file_path, index=False)
        st.cache_data.clear()
        return True

    def registrar_persona(self, dni, nombre, apellido, cargo):
        df = self.obtener_datos()
        dni_s = str(dni).strip()
        if dni_s in df['dni'].values:
            return False, "El DNI ya existe."
        nueva_fila = pd.DataFrame([[dni_s, nombre, apellido, cargo, "Pre-registrado", ""]], columns=self.columns)
        pd.concat([df, nueva_fila], ignore_index=True).to_excel(self.file_path, index=False)
        st.cache_data.clear()
        return True, "¡Registro guardado!"

    def actualizar_persona(self, dni_original, n, a, c):
        df = self.obtener_datos()
        dni_s = str(dni_original).strip()
        if dni_s in df['dni'].values:
            idx = df[df['dni'] == dni_s].index
            df.loc[idx, ['nombre', 'apellido', 'cargo']] = [n, a, c]
            df.to_excel(self.file_path, index=False)
            st.cache_data.clear()
            return True, "Datos actualizados."
        return False, "No encontrado."

    def cargar_masivo(self, df_subido):
        try:
            df_actual = self.obtener_datos()
            df_subido.columns = [c.lower().strip() for c in df_subido.columns]
            df_subido['dni'] = df_subido['dni'].astype(str).str.strip()
            df_subido['fecha_ingreso'] = "Pre-registrado"
            df_subido['fecha_salida'] = ""
            df_final = pd.concat([df_actual, df_subido]).drop_duplicates(subset=['dni'], keep='first')
            df_final.to_excel(self.file_path, index=False)
            st.cache_data.clear()
            return True, f"Se procesaron {len(df_subido)} registros."
        except Exception as e:
            return False, str(e)

    def obtener_metricas(self):
        df = self.obtener_datos()
        if df.empty: return None
        # Personas que ya marcaron ingreso
        han_entrado = df[~df['fecha_ingreso'].astype(str).str.contains("Pre|No registrado|^$", na=True)]
        # Personas que están adentro (entraron pero no tienen salida)
        dentro = han_entrado[han_entrado['fecha_salida'].astype(str).str.strip() == ""]
        fuera = han_entrado[han_entrado['fecha_salida'].astype(str).str.strip() != ""]
        conteo = dentro['cargo'].value_counts().reset_index()
        conteo.columns = ['Cargo', 'Cantidad']
        return {
            "padrón": len(df),
            "en_recinto": len(dentro),
            "ya_salieron": len(fuera),
            "por_cargo": conteo
        }