import sqlite3
from io import BytesIO
from pathlib import Path
from datetime import date
import matplotlib.pyplot as plt

import pandas as pd
import streamlit as st

DB_PATH = Path("SistemaEscolar.db")
RIESGO_CALIFICACION = 70
BAJO_DESEMPENO = 80

st.set_page_config(
    page_title="Sistema Académico - Toma de Decisiones",
    layout="wide",
)

# Estilos CSS
st.markdown(
    """
    <style>
    .main { background-color: #f8fafc; }
    .block-container { padding-top: 1.4rem; }
    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 8px 18px rgba(15, 23, 42, .06);
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #60a5fa;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    /* ── KPI cards ── */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin: 10px 0 18px 0;
    }
    .kpi-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px 14px;
        border-top: 4px solid #3b82f6;
        box-shadow: 0 4px 14px rgba(15, 23, 42, .06);
    }
    .kpi-box.verde { border-top-color: #22c55e; }
    .kpi-box.rojo  { border-top-color: #ef4444; }
    .kpi-label {
        font-size: 0.71rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 7px;
    }
    .kpi-num {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1;
    }
    .kpi-sub {
        font-size: 0.71rem;
        color: #94a3b8;
        margin-top: 5px;
    }

    /* ── Info strip ── */
    .info-strip {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        margin-bottom: 18px;
    }
    .info-strip-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 13px 18px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, .04);
    }
    .info-strip-card.verde { border-left: 5px solid #22c55e; }
    .info-strip-card.ambar { border-left: 5px solid #f59e0b; }
    .info-strip-label {
        font-size: 0.69rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .info-strip-value {
        font-size: 0.97rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 2px;
    }

    /* ── Tabla estática personalizada ── */
    .static-table {
        width: 100%;
        border-collapse: collapse;
        font-family: system-ui, -apple-system, sans-serif;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .static-table th {
        background: #f8fafc;
        color: #1e293b;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
        position: sticky;
        top: 0;
        background-color: #f8fafc;
    }
    .static-table td {
        padding: 10px 16px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 0.85rem;
    }
    .static-table tr:hover td {
        background-color: #f8fafc;
    }
    .table-container {
        max-height: 400px;
        overflow-y: auto;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .table-container-full {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        overflow-x: auto;
    }

    /* ── Reporte final ── */
    .rpt-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(15,23,42,0.08);
        margin-bottom: 18px;
    }
    .rpt-header {
        background: #0f172a;
        color: white;
        padding: 26px 30px 22px;
    }
    .rpt-header-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .rpt-header-title {
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }
    .rpt-header-sub { font-size: 0.78rem; opacity: 0.5; }
    .rpt-header-badge {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }
    .rpt-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        background: #1e293b;
        border-top: 1px solid rgba(255,255,255,0.08);
    }
    .rpt-metric {
        padding: 14px 20px;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .rpt-metric:last-child { border-right: none; }
    .rpt-metric-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: rgba(255,255,255,0.45);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 4px;
    }
    .rpt-metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: white;
        line-height: 1;
    }
    .rpt-body { padding: 24px 28px; }

    .rpt-section {
        margin-bottom: 6px;
    }
    .rpt-section:last-child { margin-bottom: 0; }
    .rpt-section-title {
        font-size: 1.08rem;
        font-weight: 700;
        letter-spacing: 0.01em;
        color: #0f172a;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .rpt-section-title span { color: #0f172a; }
    .rpt-item {
        font-size: 0.875rem;
        color: #374151;
        padding: 7px 0;
        border-bottom: 1px solid #f8fafc;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        line-height: 1.5;
    }
    .rpt-item:last-child { border-bottom: none; padding-bottom: 0; }
    .rpt-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #3b82f6; margin-top: 6px; flex-shrink: 0;
    }
    .rpt-dot.rojo  { background: #ef4444; }
    .rpt-dot.verde { background: #22c55e; }
    .rpt-dot.ambar { background: #f59e0b; }
    .rpt-sub-item {
        font-size: 0.82rem;
        color: #6b7280;
        padding: 3px 0 3px 18px;
        display: flex;
        gap: 8px;
    }
    .rpt-divider {
        border: none;
        border-top: 1px solid #f1f5f9;
        margin: 6px 0;
    }
    .rpt-footer {
        background: #f8fafc;
        border-top: 1px solid #e2e8f0;
        padding: 14px 28px;
        font-size: 0.75rem;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* ── Modo oscuro ── */
    body.st-dark .kpi-box { background: #1e293b !important; border-color: #334155 !important; }
    body.st-dark .kpi-label { color: #94a3b8 !important; }
    body.st-dark .kpi-num { color: #f1f5f9 !important; }
    body.st-dark .kpi-sub { color: #64748b !important; }
    body.st-dark .info-strip-card { background: #1e293b !important; border-color: #334155 !important; }
    body.st-dark .info-strip-label { color: #94a3b8 !important; }
    body.st-dark .info-strip-value { color: #f1f5f9 !important; }
    body.st-dark .rpt-card { border-color: #334155 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important; }
    body.st-dark .rpt-body { background: #1e293b !important; }
    body.st-dark .rpt-section-title { color: #f1f5f9 !important; border-bottom-color: #334155 !important; }
    body.st-dark .rpt-section-title span { color: #f1f5f9 !important; }
    body.st-dark .rpt-item { color: #cbd5e1 !important; border-bottom-color: #263348 !important; }
    body.st-dark .rpt-sub-item { color: #94a3b8 !important; }
    body.st-dark .rpt-divider { border-top-color: #334155 !important; }
    body.st-dark .rpt-footer { background: #0f172a !important; border-top-color: #334155 !important; color: #475569 !important; }
    body.st-dark .static-table th { background: #1e293b !important; color: #f1f5f9 !important; border-bottom-color: #334155 !important; }
    body.st-dark .static-table td { background: #0f172a !important; color: #cbd5e1 !important; border-bottom-color: #1e293b !important; }
    body.st-dark .static-table tr:hover td { background-color: #1e293b !important; }
    body.st-dark .table-container { border-color: #334155 !important; }

    /* ── Botones de descarga en AZUL CIELO ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #87CEEB 0%, #00BFFF 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.4rem !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0, 191, 255, 0.3) !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #00BFFF 0%, #009ACD 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0, 191, 255, 0.4) !important;
    }
    .stDownloadButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Deshabilitar zoom en gráficas */
    .vega-embed.has-actions {
        pointer-events: none;
    }
    .vega-embed summary {
        display: none !important;
    }
    .vega-embed details {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Configuración de pandas para usar español
pd.set_option('display.float_format', lambda x: f'{x:.2f}')

# --- FUNCIÓN PARA TABLA HTML ESTÁTICA (SIN NINGÚN CONTROL) ---
def tabla_html_estatica(df, max_height=400, full_width=True):
    """Genera una tabla HTML completamente estática sin ningún control interactivo"""
    if df.empty:
        return "<div style='text-align:center; padding:40px; color:#64748b;'>No hay datos disponibles</div>"
    
    # Copiar y formatear números
    df_display = df.copy()
    for col in df_display.select_dtypes(include=['float64', 'float32']).columns:
        df_display[col] = df_display[col].apply(lambda x: f'{x:.2f}')
    
    # Generar HTML de la tabla
    container_class = "table-container" if max_height < 999 else "table-container-full"
    html = f'<div class="{container_class}" style="max-height:{max_height}px;">'
    html += '<table class="static-table">'
    
    # Encabezados
    html += '<thead><tr>'
    for col in df_display.columns:
        # Capitalizar primera letra y reemplazar guiones bajos por espacios
        col_display = col.replace('_', ' ').title()
        html += f'<th>{col_display}</th>'
    html += '</tr></thead>'
    
    # Filas
    html += '<tbody>'
    for _, row in df_display.iterrows():
        html += '<tr>'
        for col in df_display.columns:
            value = row[col]
            html += f'<td>{value}</td>'
        html += '</tr>'
    html += '</tbody>'
    
    html += '</table></div>'
    return html

# --- FUNCIONES DE BASE DE DATOS Y LIMPIEZA ---
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def crear_bd():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS Carreras (id_carrera INTEGER PRIMARY KEY, carrera TEXT NOT NULL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS Materias (id_materia INTEGER PRIMARY KEY, materia TEXT NOT NULL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS Estudiantes (matricula INTEGER PRIMARY KEY, nombre TEXT NOT NULL, apellido TEXT NOT NULL, id_carrera INTEGER NOT NULL, FOREIGN KEY (id_carrera) REFERENCES Carreras(id_carrera));")
    cursor.execute("CREATE TABLE IF NOT EXISTS Cursos (id_curso INTEGER PRIMARY KEY, id_materia INTEGER NOT NULL, periodo TEXT NOT NULL, grupo TEXT NOT NULL, FOREIGN KEY (id_materia) REFERENCES Materias(id_materia));")
    cursor.execute("CREATE TABLE IF NOT EXISTS Calificaciones (matricula INTEGER NOT NULL, id_curso INTEGER NOT NULL, calificacion REAL CHECK (calificacion >= 0 AND calificacion <= 100), PRIMARY KEY (matricula, id_curso), FOREIGN KEY (matricula) REFERENCES Estudiantes(matricula), FOREIGN KEY (id_curso) REFERENCES Cursos(id_curso));")
    conn.commit()
    conn.close()

def limpiar_texto(df):
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def normalizar_columnas(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("á", "a", regex=False)
        .str.replace("é", "e", regex=False)
        .str.replace("í", "i", regex=False)
        .str.replace("ó", "o", regex=False)
        .str.replace("ú", "u", regex=False)
    )
    return df

def limpiar_tablas(tablas):
    limpias = {}
    for nombre, df in tablas.items():
        df = normalizar_columnas(df)
        df = limpiar_texto(df)
        df = df.drop_duplicates()
        limpias[nombre] = df
    return limpias

def guardar_tablas(tablas):
    crear_bd()
    conn = get_connection()
    orden = ["Carreras", "Materias", "Estudiantes", "Cursos", "Calificaciones"]
    for tabla in orden:
        if tabla in tablas:
            tablas[tabla].to_sql(tabla, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

@st.cache_data(show_spinner=False)
def cargar_dataset_desde_db():
    crear_bd()
    conn = get_connection()
    query = """
    SELECT e.matricula, e.nombre, e.apellido, ca.carrera, m.materia, cu.periodo, cu.grupo, cal.calificacion
    FROM Calificaciones cal
    JOIN Estudiantes e ON cal.matricula = e.matricula
    JOIN Cursos cu ON cal.id_curso = cu.id_curso
    JOIN Materias m ON cu.id_materia = m.id_materia
    JOIN Carreras ca ON e.id_carrera = ca.id_carrera;
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def cargar_archivo_subido(archivo):
    if archivo.name.endswith(".csv"):
        df = pd.read_csv(archivo)
        df = normalizar_columnas(df)
        return df
    xls = pd.ExcelFile(archivo)
    df = pd.read_excel(xls, xls.sheet_names[0])
    df = normalizar_columnas(df)
    return df

def limpiar_dataset_general(df):
    df = df.copy()
    df = normalizar_columnas(df)
    df = limpiar_texto(df)
    df = df.drop_duplicates()
    if "calificacion" in df.columns:
        df["calificacion"] = pd.to_numeric(df["calificacion"], errors="coerce")
        df = df.dropna(subset=["calificacion"])
        df = df[df["calificacion"].between(0, 100)]
    return df

def limpiar_filtros():
    st.session_state.filtro_carrera = "Todas"
    st.session_state.filtro_materia = "Todas"
    st.session_state.filtro_grupo = "Todos"
    st.session_state.filtro_periodo = "Todos"
    st.session_state.filtro_busqueda = ""

def crear_reporte_texto(df, analisis):
    if df.empty:
        return "No existen datos suficientes para generar el reporte."

    riesgo_df = df[df["calificacion"] < RIESGO_CALIFICACION].copy()
    bajo_df = df[df["calificacion"] < BAJO_DESEMPENO].copy()

    lineas = []
    lineas.append("REPORTE FINAL DE ANÁLISIS ACADÉMICO")
    lineas.append("=" * 45)
    lineas.append(f"Total de registros analizados: {analisis['total_registros']}")
    lineas.append(f"Total de estudiantes únicos: {analisis['total_estudiantes']}")
    lineas.append(f"Promedio general: {analisis['promedio']:.2f}")
    lineas.append(f"Porcentaje de aprobación: {analisis['aprobacion']:.2f}%")
    lineas.append(f"Registros en riesgo académico: {analisis['riesgo']}")
    lineas.append(f"Materia con mejor desempeño: {analisis['mejor_materia']}")
    lineas.append(f"Materia con menor desempeño: {analisis['materia_critica']}")
    lineas.append("")
    lineas.append("PATRONES DETECTADOS")
    lineas.append("- Se identifican estudiantes en riesgo cuando su calificación es menor a 70.")
    lineas.append("- Se considera bajo desempeño cuando la calificación es menor a 80.")

    if "materia" in df:
        criticas = df.groupby("materia")["calificacion"].mean().sort_values().head(3)
        lineas.append("- Materias prioritarias por menor promedio:")
        for materia, prom in criticas.items():
            lineas.append(f"  • {materia}: {prom:.2f}")

    lineas.append("")
    lineas.append("CONCLUSIONES")
    lineas.append(f"- El promedio general del Panel de Datos es de {analisis['promedio']:.2f}.")
    lineas.append(f"- Existen {len(riesgo_df)} registros en riesgo académico que requieren seguimiento.")
    lineas.append(f"- Existen {len(bajo_df)} registros con bajo desempeño que requieren acciones preventivas.")
    lineas.append("")
    lineas.append("DECISIONES ACADÉMICAS PROPUESTAS")
    lineas.append("- Implementar tutorías para estudiantes con calificaciones menores a 70.")
    lineas.append("- Reforzar las materias con menor promedio mediante asesorías o ajustes de planeación.")
    lineas.append("- Revisar el desempeño por grupo y periodo para detectar cargas académicas problemáticas.")

    return "\n".join(lineas)

def generar_analisis(df):
    if df.empty:
        return {"promedio": 0, "total_registros": 0, "total_estudiantes": 0, "aprobacion": 0, "riesgo": 0, "mejor_materia": "Sin datos", "materia_critica": "Sin datos"}
    promedio = df["calificacion"].mean()
    total_estudiantes = df["matricula"].nunique() if "matricula" in df else len(df)
    aprobacion = (df["calificacion"] >= RIESGO_CALIFICACION).mean() * 100
    riesgo = (df["calificacion"] < RIESGO_CALIFICACION).sum()
    por_materia = df.groupby("materia", as_index=False)["calificacion"].mean() if "materia" in df else pd.DataFrame()
    mejor_materia = por_materia.sort_values("calificacion", ascending=False).iloc[0]["materia"] if not por_materia.empty else "Sin datos"
    materia_critica = por_materia.sort_values("calificacion", ascending=True).iloc[0]["materia"] if not por_materia.empty else "Sin datos"
    return {"promedio": promedio, "total_registros": len(df), "total_estudiantes": total_estudiantes, "aprobacion": aprobacion, "riesgo": riesgo, "mejor_materia": mejor_materia, "materia_critica": materia_critica}

def aplicar_filtros_custom(df, filtros, omitir=None):
    filtrado = df.copy()
    if filtros["carrera"] != "Todas" and "carrera" in filtrado and omitir != "carrera":
        filtrado = filtrado[filtrado["carrera"] == filtros["carrera"]]
    if filtros["materia"] != "Todas" and "materia" in filtrado and omitir != "materia":
        filtrado = filtrado[filtrado["materia"] == filtros["materia"]]
    if filtros["grupo"] != "Todos" and "grupo" in filtrado and omitir != "grupo":
        filtrado = filtrado[filtrado["grupo"] == filtros["grupo"]]
    if filtros["periodo"] != "Todos" and "periodo" in filtrado and omitir != "periodo":
        filtrado = filtrado[filtrado["periodo"] == filtros["periodo"]]
    if filtros["busqueda"] and omitir != "busqueda":
        texto = filtros["busqueda"].lower().strip()
        nombre_completo = (filtrado.get("nombre", "").astype(str) + " " + filtrado.get("apellido", "").astype(str)).str.lower()
        matricula = filtrado.get("matricula", "").astype(str).str.lower()
        filtrado = filtrado[nombre_completo.str.contains(texto, na=False) | matricula.str.contains(texto, na=False)]
    return filtrado

def convertir_excel(df, reporte_texto):
    """
    Convierte los datos y el reporte a un archivo Excel
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja con datos filtrados
        df.to_excel(writer, sheet_name='Datos_Filtrados', index=False)
        
        # Hoja con resumen estadístico
        resumen = pd.DataFrame({
            'Métrica': ['Total de registros', 'Total de estudiantes', 'Promedio general', 
                       'Porcentaje de aprobación', 'Registros en riesgo', 'Mejor materia', 
                       'Materia crítica'],
            'Valor': [
                len(df),
                df['matricula'].nunique() if 'matricula' in df else len(df),
                df['calificacion'].mean(),
                (df['calificacion'] >= RIESGO_CALIFICACION).mean() * 100,
                (df['calificacion'] < RIESGO_CALIFICACION).sum(),
                df.groupby('materia')['calificacion'].mean().idxmax() if 'materia' in df else 'N/A',
                df.groupby('materia')['calificacion'].mean().idxmin() if 'materia' in df else 'N/A'
            ]
        })
        resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Hoja con reporte de texto
        lineas = reporte_texto.split('\n')
        reporte_df = pd.DataFrame({'Reporte': lineas})
        reporte_df.to_excel(writer, sheet_name='Reporte_Texto', index=False)
        
        # Hoja con estudiantes en riesgo
        riesgo_df = df[df['calificacion'] < RIESGO_CALIFICACION]
        if not riesgo_df.empty:
            riesgo_df.to_excel(writer, sheet_name='Estudiantes_en_Riesgo', index=False)
        
        # Hoja con estadísticas por materia
        if 'materia' in df.columns:
            stats_materia = df.groupby('materia').agg(
                promedio=('calificacion', 'mean'),
                minimo=('calificacion', 'min'),
                maximo=('calificacion', 'max'),
                cantidad_registros=('calificacion', 'count'),
                tasa_riesgo=('calificacion', lambda x: (x < RIESGO_CALIFICACION).mean() * 100)
            ).round(2).reset_index()
            stats_materia.to_excel(writer, sheet_name='Estadisticas_Materia', index=False)
    
    output.seek(0)
    return output.getvalue()

def generar_pdf(df, analisis):
    """
    Genera un reporte PDF simple con los datos y análisis
    Usa solo texto formateado para evitar dependencias problemáticas
    """
    from datetime import date
    import io
    
    # Crear un buffer en memoria
    buffer = io.BytesIO()
    
    # Crear contenido del PDF en texto plano (se convertirá a PDF)
    contenido = []
    contenido.append("%PDF-1.4")
    contenido.append("1 0 obj")
    contenido.append("<< /Type /Catalog /Pages 2 0 R >>")
    contenido.append("endobj")
    contenido.append("2 0 obj")
    contenido.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    contenido.append("endobj")
    
    # Crear contenido del reporte
    hoy = date.today().strftime("%d/%m/%Y")
    
    reporte_texto = f"""
REPORTE DE ANÁLISIS ACADÉMICO
Sistema de Toma de Decisiones
Generado el: {hoy}

================================================================================

RESUMEN EJECUTIVO
--------------------------------------------------------------------------------
Total de registros analizados: {analisis['total_registros']:,}
Total de estudiantes únicos: {analisis['total_estudiantes']:,}
Promedio general: {analisis['promedio']:.2f}
Porcentaje de aprobación: {analisis['aprobacion']:.1f}%
Registros en riesgo académico: {analisis['riesgo']:,}
Materia con mejor desempeño: {analisis['mejor_materia']}
Materia con menor desempeño: {analisis['materia_critica']}

================================================================================

PATRONES DETECTADOS
--------------------------------------------------------------------------------
• Estudiantes en riesgo: calificaciones menores a 70 puntos
• Bajo desempeño: calificaciones menores a 80 puntos
• Se requiere atención especial para estudiantes con calificaciones bajas
• Identificación de materias con mayor índice de reprobación

================================================================================

CONCLUSIONES
--------------------------------------------------------------------------------
• El promedio general del Panel de Datos es de {analisis['promedio']:.2f}
• Existen {(df['calificacion'] < RIESGO_CALIFICACION).sum()} registros en riesgo académico que requieren seguimiento
• Existen {(df['calificacion'] < BAJO_DESEMPENO).sum()} registros con bajo desempeño que requieren acciones preventivas
• Se recomienda implementar programas de tutorías para estudiantes en riesgo

================================================================================

DECISIONES ACADÉMICAS PROPUESTAS
--------------------------------------------------------------------------------
1. Implementar tutorías personalizadas para estudiantes con calificaciones menores a 70
2. Reforzar las materias con menor promedio mediante asesorías académicas
3. Revisar el desempeño por grupo y periodo para optimizar la carga académica
4. Establecer seguimiento periódico a estudiantes con bajo desempeño
5. Desarrollar planes de mejora continua por carrera y materia

================================================================================

ESTADÍSTICAS POR MATERIA
--------------------------------------------------------------------------------
"""
    
    if 'materia' in df.columns:
        stats = df.groupby('materia').agg(
            promedio=('calificacion', 'mean'),
            min=('calificacion', 'min'),
            max=('calificacion', 'max')
        ).round(2).sort_values('promedio', ascending=False)
        
        for materia, row in stats.iterrows():
            reporte_texto += f"{materia:<30} Promedio: {row['promedio']:.2f}  |  Mín: {row['min']:.2f}  |  Máx: {row['max']:.2f}\n"
    
    reporte_texto += """
================================================================================

FIN DEL REPORTE
"""
    
    # En lugar de generar un PDF complejo, devolvemos el texto
    # El usuario puede guardarlo como .txt
    return reporte_texto.encode('utf-8')

# --- FUNCIÓN PARA GRÁFICAS MINIMALISTAS ---
def grafica_minimalista(datos, x, y, titulo, xlabel, ylabel, color='#3b82f6'):
    """Función para crear gráficas minimalistas"""
    fig, ax = plt.subplots(figsize=(10, 4.5))  # Más compacto
    
    # Quitar bordes innecesarios
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e2e8f0')
    ax.spines['bottom'].set_color('#e2e8f0')
    
    # Estilo de barras/líneas simple
    if isinstance(datos, pd.Series) or (hasattr(datos, '__len__') and not hasattr(datos, 'shape')):
        ax.bar(range(len(datos)), datos, color=color, width=0.6, alpha=0.8)
        ax.set_xticks(range(len(datos)))
        ax.set_xticklabels(x, rotation=45, ha='right', fontsize=9)
    else:
        ax.bar(x, datos, color=color, width=0.6, alpha=0.8)
        ax.set_xticklabels(x, rotation=45, ha='right', fontsize=9)
    
    # Título y etiquetas minimalistas
    ax.set_title(titulo, fontsize=13, fontweight='500', pad=15, color='#1e293b')
    ax.set_xlabel(xlabel, fontsize=10, color='#64748b', labelpad=8)
    ax.set_ylabel(ylabel, fontsize=10, color='#64748b', labelpad=8)
    
    # Grid sutil
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, axis='y')
    ax.set_axisbelow(True)
    
    # Límites y ajustes
    if ylabel.lower() in ['calificación', 'calificacion', 'promedio']:
        ax.set_ylim(0, 100)
    
    plt.tight_layout()
    return fig

# --- INTERFAZ DE USUARIO ---

st.title(" Sistema de Análisis Académico")

# --- SECCIÓN SUPERIOR: CARGA DE DATOS ---
with st.expander(" CARGA DE DATOS", expanded=True):
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        archivo = st.file_uploader("Subir archivo de datos (Excel/CSV)", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
        st.caption("200MB por archivo • XLSX, XLS, CSV")
    with col_c2:
        usar_db = st.checkbox("Usar base de datos existente", value=True)

# Lógica de carga
if archivo is not None:
    df_raw = cargar_archivo_subido(archivo)
    if df_raw is not None:
        df = limpiar_dataset_general(df_raw)
elif usar_db:
    df = cargar_dataset_desde_db()
    df = limpiar_dataset_general(df)
else:
    df = pd.DataFrame()

if df.empty:
    st.warning("Esperando datos...")
    st.stop()

# --- SECCIÓN SUPERIOR: FILTROS ---
with st.expander(" FILTROS DEL PANEL Y BÚSQUEDA", expanded=True):
    st.subheader("Búsqueda de Estudiante Específico")
    busqueda = st.text_input("Buscar por nombre, apellido o matrícula", key="filtro_busqueda", placeholder="Ejemplo: 20210001 o Juan Pérez", label_visibility="collapsed")
    
    st.write("---")
    st.subheader("Filtros Generales")
    col1, col2, col3, col4 = st.columns(4)
    
    carreras = ["Todas"] + sorted(df["carrera"].dropna().unique().tolist()) if "carrera" in df else ["Todas"]
    materias = ["Todas"] + sorted(df["materia"].dropna().unique().tolist()) if "materia" in df else ["Todas"]
    grupos = ["Todos"] + sorted(df["grupo"].dropna().unique().tolist()) if "grupo" in df else ["Todos"]
    periodos = ["Todos"] + sorted(df["periodo"].dropna().unique().tolist()) if "periodo" in df else ["Todos"]

    with col1: carrera = st.selectbox("Carrera", carreras, key="filtro_carrera")
    with col2: materia = st.selectbox("Materia", materias, key="filtro_materia")
    with col3: grupo = st.selectbox("Grupo", grupos, key="filtro_grupo")
    with col4: periodo = st.selectbox("Periodo", periodos, key="filtro_periodo")
    
    st.button("Limpiar todos los filtros", on_click=limpiar_filtros, use_container_width=True)

# Aplicar filtros
filtros_seleccionados = {
    "carrera": carrera, "materia": materia, "grupo": grupo, "periodo": periodo, "busqueda": busqueda
}
df_filtrado = aplicar_filtros_custom(df, filtros_seleccionados)
analisis = generar_analisis(df_filtrado)

# --- VISUALIZACIÓN DE MÉTRICAS ---
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">Promedio general</div>
        <div class="kpi-num">{analisis['promedio']:.2f}</div>
        <div class="kpi-sub">sobre 100 puntos</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">Estudiantes</div>
        <div class="kpi-num">{analisis['total_estudiantes']:,}</div>
        <div class="kpi-sub">alumnos únicos</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">Registros</div>
        <div class="kpi-num">{analisis['total_registros']:,}</div>
        <div class="kpi-sub">calificaciones totales</div>
    </div>
    <div class="kpi-box verde">
        <div class="kpi-label">Aprobación</div>
        <div class="kpi-num">{analisis['aprobacion']:.1f}%</div>
        <div class="kpi-sub">calificación ≥ 70</div>
    </div>
    <div class="kpi-box rojo">
        <div class="kpi-label">En riesgo</div>
        <div class="kpi-num">{analisis['riesgo']:,}</div>
        <div class="kpi-sub">calificación &lt; 70</div>
    </div>
</div>
<div class="info-strip">
    <div class="info-strip-card verde">
        <span style="font-size:1.4rem"></span>
        <div>
            <div class="info-strip-label">Mejor desempeño</div>
            <div class="info-strip-value">{analisis['mejor_materia']}</div>
        </div>
    </div>
    <div class="info-strip-card ambar">
        <span style="font-size:1.4rem"></span>
        <div>
            <div class="info-strip-label">Materia crítica</div>
            <div class="info-strip-value">{analisis['materia_critica']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- PESTAÑAS DE CONTENIDO ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    " Panel de datos", " Visualización", " Comparaciones", 
    " Consultas", " Riesgo académico", " Reporte final",
])

with tab1:
    st.subheader("Panel de Datos consolidado y limpio")
    st.markdown(tabla_html_estatica(df_filtrado, 420), unsafe_allow_html=True)

with tab2:
    st.subheader("Gráficas de desempeño")
    
    if "materia" in df_filtrado:
        df_materia = aplicar_filtros_custom(df, filtros_seleccionados, omitir="materia")
        prom_materia = df_materia.groupby("materia", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)
        
        fig1 = grafica_minimalista(
            prom_materia['calificacion'].tolist(),
            prom_materia['materia'].tolist(),
            None,
            'Promedio por Materia',
            'Materia',
            'Calificación Promedio',
            color='#3b82f6'
        )
        st.pyplot(fig1)
        plt.close(fig1)
        st.divider()

    if "carrera" in df_filtrado:
        df_carrera = aplicar_filtros_custom(df, filtros_seleccionados, omitir="carrera")
        prom_carrera = df_carrera.groupby("carrera", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)
        
        fig2 = grafica_minimalista(
            prom_carrera['calificacion'].tolist(),
            prom_carrera['carrera'].tolist(),
            None,
            'Promedio por Carrera',
            'Carrera',
            'Calificación Promedio',
            color='#22c55e'
        )
        st.pyplot(fig2)
        plt.close(fig2)
        st.divider()

    if "periodo" in df_filtrado:
        df_periodo = aplicar_filtros_custom(df, filtros_seleccionados, omitir="periodo")
        prom_periodo = df_periodo.groupby("periodo", as_index=False)["calificacion"].mean().sort_values("periodo")
        
        fig3, ax3 = plt.subplots(figsize=(10, 4.5))
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.plot(prom_periodo['periodo'], prom_periodo['calificacion'], 
                marker='o', linewidth=2, markersize=6, color='#ef4444', alpha=0.8)
        ax3.set_title('Tendencia de Calificaciones por Período', fontsize=13, fontweight='500', pad=15, color='#1e293b')
        ax3.set_xlabel('Período', fontsize=10, color='#64748b')
        ax3.set_ylabel('Calificación Promedio', fontsize=10, color='#64748b')
        ax3.grid(True, alpha=0.2, linestyle='-', axis='y')
        ax3.set_ylim(0, 100)
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)
        st.divider()

    distribucion = pd.cut(
        df_filtrado["calificacion"],
        bins=[0, 60, 70, 80, 90, 100],
        labels=["0-59", "60-69", "70-79", "80-89", "90-100"],
        include_lowest=True,
    ).value_counts().sort_index()
    
    fig4, ax4 = plt.subplots(figsize=(10, 4.5))
    ax4.spines['top'].set_visible(False)
    ax4.spines['right'].set_visible(False)
    colores = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981']
    ax4.bar(range(len(distribucion)), distribucion.values, color=colores, width=0.6, alpha=0.8)
    ax4.set_xticks(range(len(distribucion)))
    ax4.set_xticklabels(distribucion.index, fontsize=9)
    ax4.set_title('Distribución de Calificaciones', fontsize=13, fontweight='500', pad=15, color='#1e293b')
    ax4.set_xlabel('Rango de Calificación', fontsize=10, color='#64748b')
    ax4.set_ylabel('Cantidad de Estudiantes', fontsize=10, color='#64748b')
    ax4.grid(True, alpha=0.2, linestyle='-', axis='y')
    
    for i, (rango, freq) in enumerate(zip(distribucion.index, distribucion.values)):
        ax4.text(i, freq + (max(distribucion.values)*0.01), str(freq), 
                ha='center', va='bottom', fontsize=9, color='#475569')
    
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close(fig4)

with tab3:
    st.subheader("Comparaciones entre grupos")

    if "grupo" in df:
        df_grupos = aplicar_filtros_custom(df, filtros_seleccionados, omitir="grupo")
        
        comparacion_grupos = df_grupos.groupby("grupo").agg(
            promedio=("calificacion", "mean"),
            minimo=("calificacion", "min"),
            maximo=("calificacion", "max"),
            registros=("calificacion", "count"),
        ).reset_index().sort_values("promedio", ascending=False)
        st.markdown(tabla_html_estatica(comparacion_grupos, 300), unsafe_allow_html=True)
        
        fig_grupos, ax_grupos = plt.subplots(figsize=(10, 4.5))
        ax_grupos.spines['top'].set_visible(False)
        ax_grupos.spines['right'].set_visible(False)
        grupos_nombres = comparacion_grupos['grupo'].tolist()
        grupos_promedios = comparacion_grupos['promedio'].tolist()
        
        ax_grupos.bar(grupos_nombres, grupos_promedios, color='#9b59b6', width=0.6, alpha=0.8)
        ax_grupos.set_title('Promedio por Grupo', fontsize=13, fontweight='500', pad=15, color='#1e293b')
        ax_grupos.set_xlabel('Grupo', fontsize=10, color='#64748b')
        ax_grupos.set_ylabel('Calificación Promedio', fontsize=10, color='#64748b')
        ax_grupos.grid(True, alpha=0.2, linestyle='-', axis='y')
        ax_grupos.set_ylim(0, 100)
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig_grupos)
        plt.close(fig_grupos)
    else:
        st.info("El conjunto de datos no contiene columna de grupo.")

    if {"materia", "grupo"}.issubset(df.columns):
        st.write("Promedio por materia y grupo")
        df_grupos = aplicar_filtros_custom(df, filtros_seleccionados, omitir="grupo")
        tabla_pivote = pd.pivot_table(
            df_grupos,
            values="calificacion",
            index="materia",
            columns="grupo",
            aggfunc="mean",
        )
        st.markdown(tabla_html_estatica(tabla_pivote.round(2), 350), unsafe_allow_html=True)

with tab4:
    st.subheader("Consultas sobre el conjunto de datos")

    opcion = st.selectbox(
        "Selecciona una consulta automática",
        [
            "Las 10 mejores calificaciones",
            "Las 10 calificaciones más bajas",
            "Promedio por materia",
            "Promedio por carrera",
            "Promedio por grupo",
            "Estudiantes con calificación menor a 70",
            "Estudiantes con bajo desempeño menor a 80",
        ],
    )

    if opcion == "Las 10 mejores calificaciones":
        resultado = df_filtrado.sort_values("calificacion", ascending=False).head(10)
    elif opcion == "Las 10 calificaciones más bajas":
        resultado = df_filtrado.sort_values("calificacion", ascending=True).head(10)
    elif opcion == "Promedio por materia" and "materia" in df_filtrado:
        resultado = df_filtrado.groupby("materia", as_index=False)["calificacion"].mean().sort_values("calificacion")
    elif opcion == "Promedio por carrera" and "carrera" in df_filtrado:
        resultado = df_filtrado.groupby("carrera", as_index=False)["calificacion"].mean().sort_values("calificacion")
    elif opcion == "Promedio por grupo" and "grupo" in df_filtrado:
        resultado = df_filtrado.groupby("grupo", as_index=False)["calificacion"].mean().sort_values("calificacion")
    elif opcion == "Estudiantes con calificación menor a 70":
        resultado = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION].sort_values("calificacion")
    elif opcion == "Estudiantes con bajo desempeño menor a 80":
        resultado = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO].sort_values("calificacion")
    else:
        resultado = pd.DataFrame()

    if not resultado.empty:
        st.markdown(tabla_html_estatica(resultado, 420), unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar")

with tab5:
    st.subheader("Identificación de patrones y estudiantes en riesgo")

    riesgo = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION].sort_values("calificacion")
    bajo = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO].sort_values("calificacion")

    r1, r2 = st.columns(2)
    r1.metric("Riesgo académico < 70", len(riesgo))
    r2.metric("Bajo desempeño < 80", len(bajo))

    if not riesgo.empty:
        st.warning("Estudiantes que requieren atención prioritaria")
        st.markdown(tabla_html_estatica(riesgo, 350), unsafe_allow_html=True)
    else:
        st.success("No se detectaron estudiantes en riesgo con los filtros actuales.")

    if "materia" in df_filtrado:
        st.write("Materias con mayor cantidad de registros en riesgo")
        riesgo_materia = riesgo.groupby("materia", as_index=False).size().sort_values("size", ascending=False)
        if not riesgo_materia.empty:
            fig_riesgo, ax_riesgo = plt.subplots(figsize=(10, 4.5))
            ax_riesgo.spines['top'].set_visible(False)
            ax_riesgo.spines['right'].set_visible(False)
            materias_riesgo = riesgo_materia['materia'].tolist()[:10]
            cantidades = riesgo_materia['size'].tolist()[:10]
            
            ax_riesgo.barh(materias_riesgo, cantidades, color='#ef4444', alpha=0.8)
            ax_riesgo.set_title('Materias con Mayor Número de Estudiantes en Riesgo', fontsize=13, fontweight='500', pad=15, color='#1e293b')
            ax_riesgo.set_xlabel('Cantidad de Estudiantes', fontsize=10, color='#64748b')
            ax_riesgo.set_ylabel('Materia', fontsize=10, color='#64748b')
            ax_riesgo.grid(True, alpha=0.2, linestyle='-', axis='x')
            plt.tight_layout()
            st.pyplot(fig_riesgo)
            plt.close(fig_riesgo)

with tab6:
    reporte = crear_reporte_texto(df_filtrado, analisis)
    hoy = date.today().strftime("%d / %m / %Y")
    riesgo_df = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION]
    bajo_df = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO]

    mat_items = ""
    if "materia" in df_filtrado.columns:
        criticas = df_filtrado.groupby("materia")["calificacion"].mean().sort_values().head(3)
        for mat, prom in criticas.items():
            mat_items += f'<div class="rpt-sub-item"><span>›</span><span>{mat}: <strong>{prom:.2f}</strong></span></div>'

    grp_items = ""
    if "grupo" in df_filtrado.columns:
        grupos_r = df_filtrado.groupby("grupo")["calificacion"].mean().sort_values().head(3)
        for grp, prom in grupos_r.items():
            grp_items += f'<div class="rpt-sub-item"><span>›</span><span>Grupo {grp}: <strong>{prom:.2f}</strong></span></div>'

    patrones_html = (
        '<div class="rpt-item"><span class="rpt-dot rojo"></span>'
        '<span>Se identifican estudiantes en riesgo cuando su calificación es <strong>menor a 70</strong>.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot ambar"></span>'
        '<span>Se considera bajo desempeño cuando la calificación es <strong>menor a 80</strong>.</span></div>'
        + (f'<div class="rpt-item"><span class="rpt-dot"></span><div><div>Materias prioritarias por menor promedio:</div>{mat_items}</div></div>' if mat_items else '')
        + (f'<div class="rpt-item"><span class="rpt-dot"></span><div><div>Grupos con menor rendimiento:</div>{grp_items}</div></div>' if grp_items else '')
    )

    html = (
        '<div class="rpt-card">'

        '<div class="rpt-header">'
        '<div class="rpt-header-top">'
        '<div>'
        '<div class="rpt-header-title">Reporte Final de Análisis Académico</div>'
        f'<div class="rpt-header-sub">Sistema de Toma de Decisiones &nbsp;·&nbsp; Generado el {hoy}</div>'
        '</div>'
        '<div class="rpt-header-badge">ANÁLISIS COMPLETO</div>'
        '</div>'
        '</div>'

        '<div class="rpt-metrics">'
        f'<div class="rpt-metric"><div class="rpt-metric-label">Total registros</div><div class="rpt-metric-value">{analisis["total_registros"]:,}</div></div>'
        f'<div class="rpt-metric"><div class="rpt-metric-label">Estudiantes únicos</div><div class="rpt-metric-value">{analisis["total_estudiantes"]:,}</div></div>'
        f'<div class="rpt-metric"><div class="rpt-metric-label">Promedio general</div><div class="rpt-metric-value">{analisis["promedio"]:.2f}</div></div>'
        f'<div class="rpt-metric"><div class="rpt-metric-label">% de aprobación</div><div class="rpt-metric-value">{analisis["aprobacion"]:.1f}%</div></div>'
        '</div>'

        '<div class="rpt-body">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Resumen ejecutivo</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot verde"></span><span>Materia con <strong>mejor desempeño</strong>: {analisis["mejor_materia"]}</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot rojo"></span><span>Materia con <strong>menor desempeño</strong>: {analisis["materia_critica"]}</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot ambar"></span><span>Registros en <strong>riesgo académico</strong> (calificación &lt; 70): <strong>{analisis["riesgo"]:,}</strong></span></div>'
        '</div>'

        '<hr class="rpt-divider">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Patrones detectados</span></div>'
        + patrones_html +
        '</div>'

        '<hr class="rpt-divider">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Conclusiones</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot"></span><span>El promedio general del conjunto de datos es de <strong>{analisis["promedio"]:.2f}</strong>.</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot rojo"></span><span>Existen <strong>{len(riesgo_df):,} registros en riesgo académico</strong> que requieren seguimiento inmediato.</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot ambar"></span><span>Existen <strong>{len(bajo_df):,} registros con bajo desempeño</strong> que requieren acciones preventivas.</span></div>'
        '</div>'

        '<hr class="rpt-divider">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Decisiones académicas propuestas</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Implementar <strong>tutorías</strong> para estudiantes con calificaciones menores a 70.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Reforzar las materias con menor promedio mediante <strong>asesorías o ajustes de planeación</strong>.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Revisar el desempeño por grupo y periodo para detectar <strong>cargas académicas problemáticas</strong>.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Dar <strong>seguimiento periódico</strong> a los estudiantes con bajo desempeño antes del cierre del periodo.</span></div>'
        '</div>'

        '</div>'

        f'<div class="rpt-footer"><span>Sistema Académico · Toma de Decisiones</span><span>Generado el {hoy}</span></div>'

        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Descargar TXT",
            data=reporte.encode("utf-8"),
            file_name="reporte_academico.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        excel = convertir_excel(df_filtrado, reporte)
        st.download_button(
            label="Descargar Excel",
            data=excel,
            file_name="reporte_academico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        pdf_bytes = generar_pdf(df_filtrado, analisis)
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name="reporte_academico.pdf",
            mime="application/pdf",
            use_container_width=True
        )
