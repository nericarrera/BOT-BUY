import os
import json
import time
import sqlite3
import re
from google import genai
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv
from config import BUSQUEDAS # ✅ Importamos la configuración

load_dotenv()

# ... (Funciones init_db, guardar_producto y limpiar_link quedan igual, pero guardar_producto ahora recibe categoría y tienda) ...

def guardar_producto(producto):
    conn = sqlite3.connect('ofertas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (titulo, precio, envio_gratis, link, categoria, tienda)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (producto['titulo'], producto['precio'], producto['envio_gratis'], producto['link'], producto['categoria'], producto['tienda']))
    conn.commit()
    conn.close()

# ... (la función extraer_ofertas_con_ia queda igual) ...

def run():
    print("🚀 Iniciando bot de ofertas MULTI-CATEGORÍA...")
    def init_db():
        ...

    init_db()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        Stealth().apply_stealth_sync(page)
        
        # ✅ RECORREMOS CADA BÚSQUEDA
        for busqueda in BUSQUEDAS:
            print(f"\n🔍 Buscando: {busqueda['categoria'].upper()}...")
            
            try:
                page.goto(busqueda['url'], timeout=30000)
                page.wait_for_timeout(3000)
                
                if "account-verification" in page.url:
                    print("⚠️ Bloqueo detectado, saltando...")
                    continue
                
                page.wait_for_selector("ol.ui-search-layout", timeout=10000)
                tarjetas = page.locator("ol.ui-search-layout > li").all()
                print(f"✅ {len(tarjetas)} tarjetas encontradas.")
                
                # Extraer links
                links_reales = []
                for tarjeta in tarjetas[:10]:
                    try:
                        link_elem = tarjeta.locator("a.ui-search-link, a.poly-component__title").first
                        if link_elem.count() > 0:
                            links_reales.append(link_elem.get_attribute("href") or "")
                    except:
                        links_reales.append("")
                
                # Extraer HTML
                html_util = ""
                for i, tarjeta in enumerate(tarjetas[:10]):
                    html_util += f"\n<!-- PRODUCTO {i+1} -->\n"
                    html_util += tarjeta.inner_html()
                
                # IA
                def extraer_ofertas_con_ia(html_util):
                    ...

                resultado = extraer_ofertas_con_ia(html_util)
                
                if resultado and "productos" in resultado:
                    for i, prod in enumerate(resultado['productos'], 1):
                        link_real = links_reales[i-1] if i-1 < len(links_reales) else ""
                        def limpiar_link(link_real):
                            ...

                        link_limpio = limpiar_link(link_real)
                        
                        guardar_producto({
                            'titulo': prod.get('titulo'),
                            'precio': float(prod.get('precio', 0)),
                            'envio_gratis': 1 if prod.get('envio_gratis') else 0,
                            'link': link_limpio,
                            'categoria': busqueda['categoria'], # ✅ Guardamos categoría
                            'tienda': 'MercadoLibre'             # ✅ Guardamos tienda
                        })
                    print(f"   💾 {len(resultado['productos'])} productos guardados.")
                
            except Exception as e:
                print(f"❌ Error en {busqueda['categoria']}: {e}")
        
        browser.close()
        print("\n🏁 Bot finalizado.")

if __name__ == "__main__":
    run()