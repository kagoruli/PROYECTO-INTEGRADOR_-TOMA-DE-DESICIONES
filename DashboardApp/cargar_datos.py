import sqlite3
import pandas as pd

def cargar_datos():
    conn = sqlite3.connect("SistemaEscolar.db")

    archivo = r"C:/Users/Wilver/OneDrive/Documentos/A_ITO-ISC/SEMESTRE VIII/D. S. Toma de Desciciones/ProyectoEQ/DashboardApp/base_datos_normalizada.xlsx"
    xls = pd.ExcelFile(archivo)

    # --- Carreras ---
    df_carreras = pd.read_excel(xls, "Carreras")
    df_carreras.columns = ["id_carrera", "carrera"]
    df_carreras.drop_duplicates(subset=["id_carrera"], inplace=True)
    df_carreras.to_sql("Carreras", conn, if_exists="append", index=False)

    # --- Materias ---
    df_materias = pd.read_excel(xls, "Materias")
    df_materias.columns = ["id_materia", "materia"]
    df_materias.drop_duplicates(subset=["id_materia"], inplace=True)
    df_materias.to_sql("Materias", conn, if_exists="append", index=False)

    # --- Estudiantes ---
    df_estudiantes = pd.read_excel(xls, "Estudiantes")
    df_estudiantes.columns = ["matricula", "nombre", "apellido", "id_carrera"]
    df_estudiantes.drop_duplicates(subset=["matricula"], inplace=True)
    df_estudiantes.to_sql("Estudiantes", conn, if_exists="append", index=False)

    # --- Cursos ---
    df_cursos = pd.read_excel(xls, "Cursos")
    df_cursos.columns = ["id_curso", "id_materia", "periodo", "grupo"]
    df_cursos.drop_duplicates(subset=["id_curso"], inplace=True)
    df_cursos.to_sql("Cursos", conn, if_exists="append", index=False)

    # --- Calificaciones ---
    df_calificaciones = pd.read_excel(xls, "Calificaciones")
    df_calificaciones.columns = ["matricula", "id_curso", "calificacion"]
    df_calificaciones.drop_duplicates(subset=["matricula","id_curso"], inplace=True)
    df_calificaciones.to_sql("Calificaciones", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()
    print("✅ Datos cargados correctamente desde base_datos_normalizada.xlsx")

if __name__ == "__main__":
    cargar_datos()
