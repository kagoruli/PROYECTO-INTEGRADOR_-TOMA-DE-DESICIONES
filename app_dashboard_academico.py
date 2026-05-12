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
        color: #0f172a;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# BASE DE DATOS
# =============================
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


def aplicar_filtros(df):
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

    filtrado = df.copy()

    if carrera != "Todas" and "carrera" in filtrado:
        filtrado = filtrado[filtrado["carrera"] == carrera]
    if materia != "Todas" and "materia" in filtrado:
        filtrado = filtrado[filtrado["materia"] == materia]
    if grupo != "Todos" and "grupo" in filtrado:
        filtrado = filtrado[filtrado["grupo"] == grupo]
    if periodo != "Todos" and "periodo" in filtrado:
        filtrado = filtrado[filtrado["periodo"] == periodo]
    if busqueda:
        texto = busqueda.lower().strip()
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

df_filtrado = aplicar_filtros(df)
analisis = generar_analisis(df_filtrado)


st.markdown('<div class="section-title">Dashboard básico</div>', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Promedio general", f"{analisis['promedio']:.2f}")
col2.metric("Estudiantes", f"{analisis['total_estudiantes']}")
col3.metric("Registros", f"{analisis['total_registros']}")
col4.metric("Aprobación", f"{analisis['aprobacion']:.1f}%")
col5.metric("En riesgo", f"{analisis['riesgo']}")

col_a, col_b = st.columns(2)
col_a.info(f"✅ Mejor desempeño: **{analisis['mejor_materia']}**")
col_b.warning(f"⚠️ Materia crítica: **{analisis['materia_critica']}**")


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

    c1, c2 = st.columns(2)

    if "materia" in df_filtrado:
        prom_materia = df_filtrado.groupby("materia", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)
        c1.write("Promedio por materia")
        c1.bar_chart(prom_materia.set_index("materia"))

    if "carrera" in df_filtrado:
        prom_carrera = df_filtrado.groupby("carrera", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)
        c2.write("Promedio por carrera")
        c2.bar_chart(prom_carrera.set_index("carrera"))

    c3, c4 = st.columns(2)

    if "periodo" in df_filtrado:
        prom_periodo = df_filtrado.groupby("periodo", as_index=False)["calificacion"].mean().sort_values("periodo")
        c3.write("Tendencia por periodo")
        c3.line_chart(prom_periodo.set_index("periodo"))

    distribucion = pd.cut(
        df_filtrado["calificacion"],
        bins=[0, 60, 70, 80, 90, 100],
        labels=["0-59", "60-69", "70-79", "80-89", "90-100"],
        include_lowest=True,
    ).value_counts().sort_index()
    c4.write("Distribución de calificaciones")
    c4.bar_chart(distribucion)

with tab3:
    st.subheader("Comparaciones entre grupos")

    if "grupo" in df_filtrado:
        comparacion_grupos = df_filtrado.groupby("grupo").agg(
            promedio=("calificacion", "mean"),
            minimo=("calificacion", "min"),
            maximo=("calificacion", "max"),
            registros=("calificacion", "count"),
        ).reset_index().sort_values("promedio", ascending=False)
        st.dataframe(comparacion_grupos, use_container_width=True)
        st.bar_chart(comparacion_grupos.set_index("grupo")[["promedio"]])
    else:
        st.info("El dataset no contiene columna de grupo.")

    if {"materia", "grupo"}.issubset(df_filtrado.columns):
        st.write("Promedio por materia y grupo")
        tabla_pivote = pd.pivot_table(
            df_filtrado,
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
    st.subheader("Generación de reporte final")
    reporte = crear_reporte_texto(df_filtrado, analisis)
    st.text_area("Reporte generado automáticamente", reporte, height=420)

    st.download_button(
        label="Descargar reporte en TXT",
        data=reporte.encode("utf-8"),
        file_name="reporte_academico.txt",
        mime="text/plain",
    )

    excel = convertir_excel(df_filtrado, reporte)
    st.download_button(
        label="Descargar reporte en Excel",
        data=excel,
        file_name="reporte_academico.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
