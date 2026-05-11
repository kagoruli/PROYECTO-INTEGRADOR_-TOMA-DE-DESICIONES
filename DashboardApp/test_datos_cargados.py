import sqlite3

conn = sqlite3.connect("SistemaEscolar.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM Estudiantes;")
print("Total de registros:", cursor.fetchone()[0])

conn.close()
