from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# Permitir que el frontend (Next.js) se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, cambiá "*" por la URL de tu frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def inicio():
    return {"mensaje": "¡API del Bot de Ofertas funcionando!"}

@app.get("/ofertas")
def obtener_ofertas():
    conn = sqlite3.connect('ofertas.db')
    conn.row_factory = sqlite3.Row  # Para que devuelva diccionarios
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY fecha DESC LIMIT 50")
    filas = cursor.fetchall()
    conn.close()
    
    # Convertir a lista de diccionarios
    ofertas = [dict(fila) for fila in filas]
    return {"total": len(ofertas), "ofertas": ofertas}