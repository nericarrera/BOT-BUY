import os
import json
import time
import sqlite3
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
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

# ==================== EXTRACCIÓN DE FRÁVEGA ====================
def extraer_productos_fravega(page, categoria):
    """Extrae productos usando el JSON-LD (datos estructurados) de Frávega."""
    productos = []
    
    try:
        # Frávega incluye un script con type="application/ld+json" con la lista de productos
        script_ld = page.locator('script[type="application/ld+json"]').first
        if script_ld.count() == 0:
            print("   ⚠️ No se encontró JSON-LD en la página.")
            return []
        
        json_text = script_ld.inner_text()
        data = json.loads(json_text)
        
        # La estructura puede variar. Buscamos el "ItemList" o "Product"
        items = []
        if isinstance(data, list):
            for item in data:
                if item.get("@type") == "ItemList":
                    items = item.get("itemListElement", [])
                    break
                elif item.get("@type") == "Product":
                    items.append(item)
        elif data.get("@type") == "ItemList":
            items = data.get("itemListElement", [])
        elif data.get("@type") == "Product":
            items = [data]
        
        for item in items:
            # Si el item es un "ListItem", el producto está en "item"
            prod = item.get("item", item) if item.get("@type") == "ListItem" else item
            
            titulo = prod.get("name", "Sin título")
            precio = prod.get("offers", {}).get("price", 0) if isinstance(prod.get("offers"), dict) else 0
            link = prod.get("url", "")
            imagen = prod.get("image", "")
            
            # Limpiamos el link (a veces viene con parámetros)
            if link:
                link = link.split("?")[0]
            
            if titulo and precio > 0:
                productos.append({
                    "titulo": titulo,
                    "precio": float(precio),
                    "link": link,
                    "imagen": imagen,
                    "envio_gratis": 0,  # Frávega no siempre lo muestra en el listado
                })
        
        print(f"   ✅ {len(productos)} productos extraídos del JSON-LD.")
        return productos
        
    except Exception as e:
        print(f"   ❌ Error extrayendo JSON-LD: {e}")
        return []

# ==================== MAIN ====================
def run():
    print("🚀 Iniciando bot de ofertas (Frávega)...")
    init_db()
    
    total_guardados = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        Stealth().apply_stealth_sync(page)
        
        for busqueda in BUSQUEDAS:
            print(f"\n🔍 Procesando: {busqueda['categoria'].upper()}...")
            
            try:
                page.goto(busqueda['url'], timeout=30000)
                page.wait_for_timeout(3000)  # Esperamos a que cargue el JS
                
                # Verificamos si hay bloqueo
                if "captcha" in page.url.lower() or page.locator("text=verificación").count() > 0:
                    print("   ⚠️ Bloqueo detectado, saltando...")
                    continue
                
                productos = extraer_productos_fravega(page, busqueda['categoria'])
                
                for prod in productos[:10]:  # Solo los primeros 10
                    guardar_producto({
                        'titulo': prod['titulo'],
                        'precio': prod['precio'],
                        'envio_gratis': prod['envio_gratis'],
                        'link': prod['link'],
                        'imagen': prod['imagen'],
                        'categoria': busqueda['categoria'],
                        'tienda': 'Frávega'
                    })
                    total_guardados += 1
                
                print(f"   💾 {min(len(productos), 10)} productos guardados.")
                
            except Exception as e:
                print(f"   ❌ Error en {busqueda['categoria']}: {e}")
        
        browser.close()
        print(f"\n🏁 Bot finalizado. TOTAL GUARDADOS: {total_guardados} productos.")

if __name__ == "__main__":
    run()