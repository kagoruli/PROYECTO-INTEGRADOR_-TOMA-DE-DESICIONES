import sqlite3
import pandas as pd
import streamlit as st

#Ejecuta con: streamlit run app.py


# Conexión a la base de datos
conn = sqlite3.connect("SistemaEscolar.db")

# --- Cargar datos ---
df_estudiantes = pd.read_sql("SELECT * FROM Estudiantes", conn)
df_carreras = pd.read_sql("SELECT * FROM Carreras", conn)
df_materias = pd.read_sql("SELECT * FROM Materias", conn)
df_cursos = pd.read_sql("SELECT * FROM Cursos", conn)
df_calificaciones = pd.read_sql("SELECT * FROM Calificaciones", conn)

# --- Dashboard ---
st.title("📊 Dashboard Académico")
st.write("Sistema de análisis de rendimiento estudiantil")

# 🔹 Promedio de calificaciones por carrera
query_carrera = """
SELECT c.carrera, AVG(cal.calificacion) as promedio
FROM Calificaciones cal
JOIN Estudiantes e ON cal.matricula = e.matricula
JOIN Carreras c ON e.id_carrera = c.id_carrera
GROUP BY c.carrera;
"""
df_promedio_carrera = pd.read_sql(query_carrera, conn)
st.subheader("Promedio por carrera")
st.bar_chart(df_promedio_carrera.set_index("carrera"))

# 🔹 Promedio de calificaciones por materia
query_materia = """
SELECT m.materia, AVG(cal.calificacion) as promedio
FROM Calificaciones cal
JOIN Cursos cu ON cal.id_curso = cu.id_curso
JOIN Materias m ON cu.id_materia = m.id_materia
GROUP BY m.materia;
"""
df_promedio_materia = pd.read_sql(query_materia, conn)
st.subheader("Promedio por materia")
st.bar_chart(df_promedio_materia.set_index("materia"))

# 🔹 Estudiantes en riesgo (<60)
query_riesgo = """
SELECT e.matricula, e.nombre, e.apellido, c.carrera, cal.calificacion
FROM Calificaciones cal
JOIN Estudiantes e ON cal.matricula = e.matricula
JOIN Carreras c ON e.id_carrera = c.id_carrera
WHERE cal.calificacion < 70;
"""
df_riesgo = pd.read_sql(query_riesgo, conn)
st.subheader("⚠️ Estudiantes en riesgo académico")
st.dataframe(df_riesgo)

# 🔹 Filtros interactivos
st.subheader("Filtrar por carrera")
carrera_seleccionada = st.selectbox("Selecciona una carrera", df_carreras["carrera"].unique())
df_filtrado = df_riesgo[df_riesgo["carrera"] == carrera_seleccionada]
st.write(df_filtrado)

conn.close()
