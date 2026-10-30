import os
import time
import sqlite3
import requests
from dotenv import load_dotenv
from config import BUSQUEDAS

load_dotenv()

# ==================== BASE DE DATOS ====================
def init_db():
    conn = sqlite3.connect('ofertas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            precio REAL,
            envio_gratis INTEGER,
            link TEXT,
            imagen TEXT,
            categoria TEXT,
            tienda TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos lista")

def guardar_producto(producto):
    conn = sqlite3.connect('ofertas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (titulo, precio, envio_gratis, link, imagen, categoria, tienda)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (producto['titulo'], producto['precio'], producto['envio_gratis'], producto['link'], producto['imagen'], producto['categoria'], producto['tienda']))
    conn.commit()
    conn.close()

# ==================== API DE MERCADOLIBRE ====================
def buscar_en_api(query, categoria):
    """Busca productos usando la API pública de MercadoLibre."""
    print(f"🔍 Buscando '{query}' en la API de MercadoLibre...")
    
    # Endpoint público de búsqueda para Argentina (MLA)
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={query}&limit=5"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"   ❌ Error HTTP: {response.status_code}")
            return []
        
        data = response.json()
        resultados = data.get('results', [])
        
        if not resultados:
            print("   ⚠️ No se encontraron resultados.")
            return []
        
        print(f"   ✅ {len(resultados)} productos encontrados.")
        return resultados
        
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return []

# ==================== MAIN ====================
def run():
    print("🚀 Iniciando bot de ofertas (API oficial)...")
    init_db()
    
    total_guardados = 0
    
    for busqueda in BUSQUEDAS:
        print(f"\n🔍 Procesando: {busqueda['categoria'].upper()}...")
        
        # Usamos el query de la config
        query = busqueda['query']
        resultados = buscar_en_api(query, busqueda['categoria'])
        
        for item in resultados:
            try:
                # Extraer datos del JSON de la API
                titulo = item.get('title', 'Sin título')
                precio = float(item.get('price', 0))
                
                # Envío gratis: el campo puede ser 'shipping.free_shipping' o 'shipping.free_methods'
                envio_gratis = 0
                shipping = item.get('shipping', {})
                if shipping.get('free_shipping') or shipping.get('free_methods'):
                    envio_gratis = 1
                
                # Link directo al producto
                link = item.get('permalink', '')
                
                # Imagen: usamos 'thumbnail' o 'secure_thumbnail' (mejor calidad)
                imagen = item.get('thumbnail', '')
                if not imagen:
                    imagen = item.get('secure_thumbnail', '')
                
                # Guardar en la base
                guardar_producto({
                    'titulo': titulo,
                    'precio': precio,
                    'envio_gratis': envio_gratis,
                    'link': link,
                    'imagen': imagen,
                    'categoria': busqueda['categoria'],
                    'tienda': 'MercadoLibre'
                })
                total_guardados += 1
                print(f"   💾 Guardado: {titulo[:50]}... | ${precio}")
                
            except Exception as e:
                print(f"   ❌ Error guardando: {e}")
        
        # Pequeña pausa para no saturar la API
        time.sleep(1)
    
    print(f"\n🏁 Bot finalizado. TOTAL GUARDADOS: {total_guardados} productos.")

if __name__ == "__main__":
    run()