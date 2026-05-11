import sqlite3

def crear_bd():
    conn = sqlite3.connect("SistemaEscolar.db")
    cursor = conn.cursor()

    # Tabla Carreras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Carreras (
        id_carrera INTEGER PRIMARY KEY,
        carrera TEXT NOT NULL
    );
    """)

    # Tabla Materias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Materias (
        id_materia INTEGER PRIMARY KEY,
        materia TEXT NOT NULL
    );
    """)

    # Tabla Estudiantes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Estudiantes (
        matricula INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        id_carrera INTEGER NOT NULL,
        FOREIGN KEY (id_carrera) REFERENCES Carreras(id_carrera)
    );
    """)

    # Tabla Cursos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cursos (
        id_curso INTEGER PRIMARY KEY,
        id_materia INTEGER NOT NULL,
        periodo TEXT NOT NULL,
        grupo TEXT NOT NULL,
        FOREIGN KEY (id_materia) REFERENCES Materias(id_materia)
    );
    """)

    # Tabla Calificaciones
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
    print("Base de datos creada con éxito: SistemaEscolar.db")

if __name__ == "__main__":
    crear_bd()
