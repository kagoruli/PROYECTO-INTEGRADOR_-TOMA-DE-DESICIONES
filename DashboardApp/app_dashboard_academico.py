import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st



DB_PATH = Path("SistemaEscolar.db")
RIESGO_CALIFICACION = 70
BAJO_DESEMPENO = 80

st.set_page_config(
    page_title="Sistema Académico - Toma de Decisiones",
    page_icon="📊",
    layout="wide",
)


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
        color: #272AF5;
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

    /* ── Info strip (mejor/peor materia) ── */
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

    /* ── Modo oscuro — activado por JS cuando Streamlit está en Dark/System dark ── */
    body.st-dark .kpi-box                { background: #1e293b !important; border-color: #334155 !important; }
    body.st-dark .kpi-label              { color: #94a3b8 !important; }
    body.st-dark .kpi-num                { color: #f1f5f9 !important; }
    body.st-dark .kpi-sub                { color: #64748b !important; }
    body.st-dark .info-strip-card        { background: #1e293b !important; border-color: #334155 !important; }
    body.st-dark .info-strip-label       { color: #94a3b8 !important; }
    body.st-dark .info-strip-value       { color: #f1f5f9 !important; }
    body.st-dark .rpt-card               { border-color: #334155 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important; }
    body.st-dark .rpt-body               { background: #1e293b !important; }
    body.st-dark .rpt-section-title      { color: #f1f5f9 !important; border-bottom-color: #334155 !important; }
    body.st-dark .rpt-section-title span { color: #f1f5f9 !important; }
    body.st-dark .rpt-item               { color: #cbd5e1 !important; border-bottom-color: #263348 !important; }
    body.st-dark .rpt-sub-item           { color: #94a3b8 !important; }
    body.st-dark .rpt-divider            { border-top-color: #334155 !important; }
    body.st-dark .rpt-footer             { background: #0f172a !important; border-top-color: #334155 !important; color: #475569 !important; }

    /* ── Botones de descarga ── */
    .stDownloadButton > button {
        background-color: #0f172a !important;
        color: white !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.4rem !important;
        width: 100% !important;
        transition: background-color 0.15s !important;
    }
    .stDownloadButton > button:hover {
        background-color: #1e3a5f !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def crear_bd():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Carreras (
        id_carrera INTEGER PRIMARY KEY,
        carrera TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Materias (
        id_materia INTEGER PRIMARY KEY,
        materia TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Estudiantes (
        matricula INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        id_carrera INTEGER NOT NULL,
        FOREIGN KEY (id_carrera) REFERENCES Carreras(id_carrera)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cursos (
        id_curso INTEGER PRIMARY KEY,
        id_materia INTEGER NOT NULL,
        periodo TEXT NOT NULL,
        grupo TEXT NOT NULL,
        FOREIGN KEY (id_materia) REFERENCES Materias(id_materia)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Calificaciones (
        matricula INTEGER NOT NULL,
        id_curso INTEGER NOT NULL,
        calificacion REAL CHECK (calificacion >= 0 AND calificacion <= 100),
        PRIMARY KEY (matricula, id_curso),
        FOREIGN KEY (matricula) REFERENCES Estudiantes(matricula),
        FOREIGN KEY (id_curso) REFERENCES Cursos(id_curso)
    );
    """)

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

    if "Carreras" in limpias:
        limpias["Carreras"] = limpias["Carreras"].rename(columns={"id_carrera": "id_carrera", "carrera": "carrera"})
        limpias["Carreras"] = limpias["Carreras"].drop_duplicates(subset=["id_carrera"])

    if "Materias" in limpias:
        limpias["Materias"] = limpias["Materias"].rename(columns={"id_materia": "id_materia", "materia": "materia"})
        limpias["Materias"] = limpias["Materias"].drop_duplicates(subset=["id_materia"])

    if "Estudiantes" in limpias:
        limpias["Estudiantes"] = limpias["Estudiantes"].rename(
            columns={"matricula": "matricula", "nombre": "nombre", "apellido": "apellido", "id_carrera": "id_carrera"}
        )
        limpias["Estudiantes"] = limpias["Estudiantes"].drop_duplicates(subset=["matricula"])

    if "Cursos" in limpias:
        limpias["Cursos"] = limpias["Cursos"].rename(
            columns={"id_curso": "id_curso", "id_materia": "id_materia", "periodo": "periodo", "grupo": "grupo"}
        )
        limpias["Cursos"] = limpias["Cursos"].drop_duplicates(subset=["id_curso"])

    if "Calificaciones" in limpias:
        limpias["Calificaciones"] = limpias["Calificaciones"].rename(
            columns={"matricula": "matricula", "id_curso": "id_curso", "calificacion": "calificacion"}
        )
        limpias["Calificaciones"]["calificacion"] = pd.to_numeric(
            limpias["Calificaciones"]["calificacion"], errors="coerce"
        )
        limpias["Calificaciones"] = limpias["Calificaciones"].dropna(subset=["calificacion"])
        limpias["Calificaciones"] = limpias["Calificaciones"][
            limpias["Calificaciones"]["calificacion"].between(0, 100)
        ]
        limpias["Calificaciones"] = limpias["Calificaciones"].drop_duplicates(subset=["matricula", "id_curso"])

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
    SELECT
        e.matricula,
        e.nombre,
        e.apellido,
        ca.carrera,
        m.materia,
        cu.periodo,
        cu.grupo,
        cal.calificacion
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
        requeridas = {"matricula", "nombre", "apellido", "carrera", "materia", "periodo", "grupo", "calificacion"}
        faltantes = requeridas - set(df.columns)
        if faltantes:
            st.error(f"El CSV debe contener estas columnas: {', '.join(sorted(requeridas))}")
            return None
        return df

    xls = pd.ExcelFile(archivo)
    hojas = set(xls.sheet_names)
    hojas_normalizadas = {h.lower(): h for h in xls.sheet_names}

    if {"carreras", "materias", "estudiantes", "cursos", "calificaciones"}.issubset(set(hojas_normalizadas.keys())):
        tablas = {
            "Carreras": pd.read_excel(xls, hojas_normalizadas["carreras"]),
            "Materias": pd.read_excel(xls, hojas_normalizadas["materias"]),
            "Estudiantes": pd.read_excel(xls, hojas_normalizadas["estudiantes"]),
            "Cursos": pd.read_excel(xls, hojas_normalizadas["cursos"]),
            "Calificaciones": pd.read_excel(xls, hojas_normalizadas["calificaciones"]),
        }
        tablas = limpiar_tablas(tablas)
        guardar_tablas(tablas)
        st.cache_data.clear()
        return cargar_dataset_desde_db()

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

    if "periodo" in df.columns:
        df["periodo"] = df["periodo"].astype(str)

    return df


def obtener_filtros(df):
    with st.sidebar:
        st.header("Filtros")

        carreras = ["Todas"] + sorted(df["carrera"].dropna().unique().tolist()) if "carrera" in df else ["Todas"]
        materias = ["Todas"] + sorted(df["materia"].dropna().unique().tolist()) if "materia" in df else ["Todas"]
        grupos = ["Todos"] + sorted(df["grupo"].dropna().unique().tolist()) if "grupo" in df else ["Todos"]
        periodos = ["Todos"] + sorted(df["periodo"].dropna().unique().tolist()) if "periodo" in df else ["Todos"]

        carrera = st.selectbox("Carrera", carreras)
        materia = st.selectbox("Materia", materias)
        grupo = st.selectbox("Grupo", grupos)
        periodo = st.selectbox("Periodo", periodos)
        busqueda = st.text_input("Buscar alumno o matrícula")

    return {
        "carrera": carrera,
        "materia": materia,
        "grupo": grupo,
        "periodo": periodo,
        "busqueda": busqueda
    }


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
        nombre_completo = (
            filtrado.get("nombre", "").astype(str) + " " + filtrado.get("apellido", "").astype(str)
        ).str.lower()
        matricula = filtrado.get("matricula", "").astype(str).str.lower()
        filtrado = filtrado[nombre_completo.str.contains(texto, na=False) | matricula.str.contains(texto, na=False)]

    return filtrado


def generar_analisis(df):
    if df.empty:
        return {
            "promedio": 0,
            "total_registros": 0,
            "total_estudiantes": 0,
            "aprobacion": 0,
            "riesgo": 0,
            "mejor_materia": "Sin datos",
            "materia_critica": "Sin datos",
        }

    promedio = df["calificacion"].mean()
    total_estudiantes = df["matricula"].nunique() if "matricula" in df else len(df)
    aprobacion = (df["calificacion"] >= RIESGO_CALIFICACION).mean() * 100
    riesgo = (df["calificacion"] < RIESGO_CALIFICACION).sum()

    por_materia = df.groupby("materia", as_index=False)["calificacion"].mean() if "materia" in df else pd.DataFrame()
    mejor_materia = por_materia.sort_values("calificacion", ascending=False).iloc[0]["materia"] if not por_materia.empty else "Sin datos"
    materia_critica = por_materia.sort_values("calificacion", ascending=True).iloc[0]["materia"] if not por_materia.empty else "Sin datos"

    return {
        "promedio": promedio,
        "total_registros": len(df),
        "total_estudiantes": total_estudiantes,
        "aprobacion": aprobacion,
        "riesgo": riesgo,
        "mejor_materia": mejor_materia,
        "materia_critica": materia_critica,
    }


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

    if "grupo" in df:
        grupos = df.groupby("grupo")["calificacion"].mean().sort_values().head(3)
        lineas.append("- Grupos con menor rendimiento promedio:")
        for grupo, prom in grupos.items():
            lineas.append(f"  • Grupo {grupo}: {prom:.2f}")

    lineas.append("")
    lineas.append("CONCLUSIONES")
    lineas.append(f"- El promedio general del dataset es de {analisis['promedio']:.2f}.")
    lineas.append(f"- Existen {len(riesgo_df)} registros en riesgo académico que requieren seguimiento.")
    lineas.append(f"- Existen {len(bajo_df)} registros con bajo desempeño que requieren acciones preventivas.")
    lineas.append("")
    lineas.append("DECISIONES ACADÉMICAS PROPUESTAS")
    lineas.append("- Implementar tutorías para estudiantes con calificaciones menores a 70.")
    lineas.append("- Reforzar las materias con menor promedio mediante asesorías o ajustes de planeación.")
    lineas.append("- Revisar el desempeño por grupo y periodo para detectar cargas académicas problemáticas.")
    lineas.append("- Dar seguimiento periódico a los estudiantes con bajo desempeño antes del cierre del periodo.")

    return "\n".join(lineas)


def generar_pdf(df, analisis):
    from fpdf import FPDF
    from datetime import date

    riesgo_df = df[df["calificacion"] < RIESGO_CALIFICACION]
    bajo_df   = df[df["calificacion"] < BAJO_DESEMPENO]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # ── Encabezado ──────────────────────────────────────
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(20, 10)
    pdf.cell(0, 8, "REPORTE FINAL DE ANALISIS ACADEMICO", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 190, 210)
    pdf.set_x(20)
    pdf.cell(0, 6, f"Generado el {date.today().strftime('%d/%m/%Y')}  |  Sistema de Toma de Decisiones", ln=True)
    pdf.ln(14)

    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    labels = ["REGISTROS", "ESTUDIANTES", "PROMEDIO", "APROBACION"]
    values = [
        f"{analisis['total_registros']:,}",
        f"{analisis['total_estudiantes']:,}",
        f"{analisis['promedio']:.2f}",
        f"{analisis['aprobacion']:.1f}%",
    ]
    col_w = 42.5
    for lbl, val in zip(labels, values):
        pdf.set_text_color(100, 116, 139)
        pdf.cell(col_w, 5, lbl)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    for val in values:
        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w, 8, val)
    pdf.ln(14)

    def section(title, items):
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 7, title, ln=True, fill=True, border="B")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(55, 65, 81)
        for item in items:
            pdf.set_x(20)
            pdf.cell(5, 6, chr(149))
            pdf.multi_cell(0, 6, item)
        pdf.ln(4)

    
    section("RESUMEN EJECUTIVO", [
        f"Materia con mejor desempeno: {analisis['mejor_materia']}",
        f"Materia con menor desempeno: {analisis['materia_critica']}",
        f"Registros en riesgo academico (< 70): {analisis['riesgo']:,}",
    ])

    
    patrones = [
        "Se identifican estudiantes en riesgo cuando su calificacion es menor a 70.",
        "Se considera bajo desempeno cuando la calificacion es menor a 80.",
    ]
    if "materia" in df.columns:
        criticas = df.groupby("materia")["calificacion"].mean().sort_values().head(3)
        for mat, prom in criticas.items():
            patrones.append(f"  Materia prioritaria: {mat} - promedio {prom:.2f}")
    if "grupo" in df.columns:
        grupos = df.groupby("grupo")["calificacion"].mean().sort_values().head(3)
        for grp, prom in grupos.items():
            patrones.append(f"  Grupo con menor rendimiento: Grupo {grp} - {prom:.2f}")
    section("PATRONES DETECTADOS", patrones)

    
    section("CONCLUSIONES", [
        f"El promedio general del dataset es de {analisis['promedio']:.2f}.",
        f"Existen {len(riesgo_df):,} registros en riesgo academico que requieren seguimiento.",
        f"Existen {len(bajo_df):,} registros con bajo desempeno que requieren acciones preventivas.",
    ])

    
    section("DECISIONES ACADEMICAS PROPUESTAS", [
        "Implementar tutorias para estudiantes con calificaciones menores a 70.",
        "Reforzar las materias con menor promedio mediante asesorias o ajustes de planeacion.",
        "Revisar el desempeno por grupo y periodo para detectar cargas academicas problematicas.",
        "Dar seguimiento periodico a los estudiantes con bajo desempeno antes del cierre del periodo.",
    ])

    
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, f"Sistema Academico - Toma de Decisiones  |  {date.today().strftime('%d/%m/%Y')}", align="C")

    return pdf.output(dest='S').encode('latin-1')


def convertir_excel(df, reporte):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dataset_Limpio")
        resumen = pd.DataFrame({"Reporte": reporte.split("\n")})
        resumen.to_excel(writer, index=False, sheet_name="Reporte")

        if not df.empty:
            if "materia" in df:
                df.groupby("materia", as_index=False)["calificacion"].mean().to_excel(writer, index=False, sheet_name="Promedio_Materia")
            if "grupo" in df:
                df.groupby("grupo", as_index=False)["calificacion"].mean().to_excel(writer, index=False, sheet_name="Promedio_Grupo")
            if "carrera" in df:
                df.groupby("carrera", as_index=False)["calificacion"].mean().to_excel(writer, index=False, sheet_name="Promedio_Carrera")
            df[df["calificacion"] < RIESGO_CALIFICACION].to_excel(writer, index=False, sheet_name="Riesgo_Academico")

    output.seek(0)
    return output



st.markdown("""
<script>
(function() {
    function applyTheme() {
        var app = document.querySelector('[data-testid="stApp"]');
        if (!app) return;
        var bg = window.getComputedStyle(app).backgroundColor;
        // rgb(14,17,23) = #0e1117 (Streamlit dark), rgb(38,39,48) = #262730
        var dark = bg && (
            bg.includes('14, 17, 23') || bg.includes('14,17,23') ||
            bg.includes('38, 39, 48') || bg.includes('38,39,48') ||
            bg.includes('26, 28, 36') || bg.includes('26,28,36')
        );
        document.body.classList.toggle('st-dark', dark);
    }
    applyTheme();
    var observer = new MutationObserver(applyTheme);
    observer.observe(document.documentElement, {
        attributes: true, childList: true, subtree: true,
        attributeFilter: ['style', 'class']
    });
    setInterval(applyTheme, 500);
})();
</script>
""", unsafe_allow_html=True)

st.title("📊 Sistema de Análisis Académico")
st.caption("Consolidación, limpieza, análisis, visualización y reporte para toma de decisiones académicas")

with st.sidebar:
    st.header("Carga de datos")
    archivo = st.file_uploader("Sube archivo Excel o CSV", type=["xlsx", "xls", "csv"])
    usar_db = st.checkbox("Usar base SQLite existente", value=True)

if archivo is not None:
    df = cargar_archivo_subido(archivo)
    if df is not None:
        df = limpiar_dataset_general(df)
        st.success("Archivo cargado y limpiado correctamente.")
elif usar_db:
    df = cargar_dataset_desde_db()
    df = limpiar_dataset_general(df)
else:
    df = pd.DataFrame()

if df.empty:
    st.warning("No hay datos disponibles. Sube un archivo Excel/CSV o verifica la base de datos SQLite.")
    st.stop()

# Validación mínima
columnas_necesarias = {"calificacion"}
if not columnas_necesarias.issubset(df.columns):
    st.error("El dataset debe incluir al menos la columna 'calificacion'.")
    st.stop()

filtros_seleccionados = obtener_filtros(df)
df_filtrado = aplicar_filtros_custom(df, filtros_seleccionados)
analisis = generar_analisis(df_filtrado)


st.markdown('<div class="section-title">Resumen general</div>', unsafe_allow_html=True)
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
        <span style="font-size:1.4rem">🏆</span>
        <div>
            <div class="info-strip-label">Mejor desempeño</div>
            <div class="info-strip-value">{analisis['mejor_materia']}</div>
        </div>
    </div>
    <div class="info-strip-card ambar">
        <span style="font-size:1.4rem">⚠️</span>
        <div>
            <div class="info-strip-label">Materia crítica</div>
            <div class="info-strip-value">{analisis['materia_critica']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Dataset",
    "📈 Visualización",
    "⚖️ Comparaciones",
    "🔎 Consultas",
    "⚠️ Riesgo académico",
    "📄 Reporte final",
])

with tab1:
    st.subheader("Dataset consolidado y limpio")
    st.dataframe(df_filtrado, use_container_width=True, height=420)
    st.write("Columnas disponibles:", list(df_filtrado.columns))

with tab2:
    st.subheader("Gráficas de desempeño")

    if "materia" in df_filtrado:
        # Ignorar filtro de materia
        df_materia = aplicar_filtros_custom(df, filtros_seleccionados, omitir="materia")
        prom_materia = df_materia.groupby("materia", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)
        st.write("Promedio por materia")
        st.bar_chart(prom_materia.set_index("materia"), use_container_width=True)
        st.divider()

    if "carrera" in df_filtrado:
        # Ignorar filtro de carrera
        df_carrera = aplicar_filtros_custom(df, filtros_seleccionados, omitir="carrera")
        prom_carrera = df_carrera.groupby("carrera", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)
        st.write("Promedio por carrera")
        st.bar_chart(prom_carrera.set_index("carrera"), use_container_width=True)
        st.divider()

    if "periodo" in df_filtrado:
        # Ignorar filtro de periodo para ver tendencia completa
        df_periodo = aplicar_filtros_custom(df, filtros_seleccionados, omitir="periodo")
        prom_periodo = df_periodo.groupby("periodo", as_index=False)["calificacion"].mean().sort_values("periodo")
        st.write("Tendencia por periodo")
        st.line_chart(prom_periodo.set_index("periodo"), use_container_width=True)
        st.divider()

    # Distribución sí obedece a todos los filtros
    distribucion = pd.cut(
        df_filtrado["calificacion"],
        bins=[0, 60, 70, 80, 90, 100],
        labels=["0-59", "60-69", "70-79", "80-89", "90-100"],
        include_lowest=True,
    ).value_counts().sort_index()
    st.write("Distribución de calificaciones")
    st.bar_chart(distribucion, use_container_width=True)

with tab3:
    st.subheader("Comparaciones entre grupos")

    if "grupo" in df:
        # Ignorar el filtro de grupo para poder comparar todos los grupos
        df_grupos = aplicar_filtros_custom(df, filtros_seleccionados, omitir="grupo")
        
        comparacion_grupos = df_grupos.groupby("grupo").agg(
            promedio=("calificacion", "mean"),
            minimo=("calificacion", "min"),
            maximo=("calificacion", "max"),
            registros=("calificacion", "count"),
        ).reset_index().sort_values("promedio", ascending=False)
        st.dataframe(comparacion_grupos, use_container_width=True)
        st.bar_chart(comparacion_grupos.set_index("grupo")[["promedio"]])
    else:
        st.info("El dataset no contiene columna de grupo.")

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
        st.dataframe(tabla_pivote.round(2), use_container_width=True)

with tab4:
    st.subheader("Consultas sobre el dataset")

    opcion = st.selectbox(
        "Selecciona una consulta automática",
        [
            "Top 10 mejores calificaciones",
            "Top 10 calificaciones más bajas",
            "Promedio por materia",
            "Promedio por carrera",
            "Promedio por grupo",
            "Estudiantes con calificación menor a 70",
            "Estudiantes con bajo desempeño menor a 80",
        ],
    )

    if opcion == "Top 10 mejores calificaciones":
        resultado = df_filtrado.sort_values("calificacion", ascending=False).head(10)
    elif opcion == "Top 10 calificaciones más bajas":
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

    st.dataframe(resultado, use_container_width=True, height=420)

with tab5:
    st.subheader("Identificación de patrones y estudiantes en riesgo")

    riesgo = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION].sort_values("calificacion")
    bajo = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO].sort_values("calificacion")

    r1, r2 = st.columns(2)
    r1.metric("Riesgo académico < 70", len(riesgo))
    r2.metric("Bajo desempeño < 80", len(bajo))

    if not riesgo.empty:
        st.warning("Estudiantes que requieren atención prioritaria")
        st.dataframe(riesgo, use_container_width=True, height=350)
    else:
        st.success("No se detectaron estudiantes en riesgo con los filtros actuales.")

    if "materia" in df_filtrado:
        st.write("Materias con mayor cantidad de registros en riesgo")
        riesgo_materia = riesgo.groupby("materia", as_index=False).size().sort_values("size", ascending=False)
        if not riesgo_materia.empty:
            st.bar_chart(riesgo_materia.set_index("materia"))

with tab6:
    from datetime import date as _date

    reporte  = crear_reporte_texto(df_filtrado, analisis)
    hoy      = _date.today().strftime("%d / %m / %Y")
    riesgo_df = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION]
    bajo_df   = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO]

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
        f'<div class="rpt-item"><span class="rpt-dot"></span><span>El promedio general del dataset es de <strong>{analisis["promedio"]:.2f}</strong>.</span></div>'
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

    
    st.download_button(
        label=" Descargar TXT",
        data=reporte.encode("utf-8"),
        file_name="reporte_academico.txt",
        mime="text/plain",
    )
    excel = convertir_excel(df_filtrado, reporte)
    st.download_button(
        label=" Descargar Excel",
        data=excel,
        file_name="reporte_academico.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    pdf_bytes = generar_pdf(df_filtrado, analisis)
    st.download_button(
        label=" Descargar PDF",
        data=pdf_bytes,
        file_name="reporte_academico.pdf",
        mime="application/pdf",
    )
