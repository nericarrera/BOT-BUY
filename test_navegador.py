import os
import json
import time
import sqlite3
import re
from google import genai
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
            categoria TEXT,
            tienda TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de datos lista (ofertas.db)")

def guardar_producto(producto):
    conn = sqlite3.connect('ofertas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (titulo, precio, envio_gratis, link, categoria, tienda)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (producto['titulo'], producto['precio'], producto['envio_gratis'], producto['link'], producto['categoria'], producto['tienda']))
    conn.commit()
    conn.close()

# ==================== LIMPIAR LINKS ====================
def limpiar_link(url):
    if not url:
        return ""
    match = re.search(r'(MLA\d+)', url)
    if match:
        return f"https://articulo.mercadolibre.com.ar/{match.group(1)}"
    match = re.search(r'(https?://[^/]+)', url)
    return match.group(1) if match else url

# ==================== IA ====================
def extraer_ofertas_con_ia(html_productos, categoria):
    print(f"🧠 Enviando {categoria} a Gemini...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró GEMINI_API_KEY")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Eres un experto en e-commerce. Te paso el HTML de los resultados de búsqueda de MercadoLibre para la categoría "{categoria}".
    Extraé hasta 5 productos. Para cada uno necesito:
    1. titulo
    2. precio (solo el número, sin puntos ni símbolos)
    3. envio_gratis (true/false)
    4. link (la URL base del producto, sin parámetros de tracking)
    
    Si no encontrás productos, devolveme un JSON con un campo "error".
    Devolveme ÚNICAMENTE un JSON válido con un array llamado "productos".
    No agregues texto extra, solo el JSON.
    
    HTML de productos:
    {html_productos[:40000]} 
    """
    
    modelos = ['gemini-3.8-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
    
    for modelo in modelos:
        for intento in range(2):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt
                )
                texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(texto_limpio)
                
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    print(f"   ⏳ Google saturado. Esperando 3 segundos...")
                    time.sleep(3)
                elif "404" in error_msg or "NOT_FOUND" in error_msg:
                    print(f"   ⚠️ Modelo {modelo} no disponible. Probando el siguiente...")
                    break
                else:
                    print(f"   ❌ Error inesperado: {e}")
                    time.sleep(2)
    
    print(f"❌ Todos los modelos fallaron para {categoria}.")
    return None

# ==================== MAIN ====================
def run():
    print("🚀 Iniciando bot de ofertas MULTI-CATEGORÍA...")
    init_db()
    
    total_guardados = 0 # ✅ NUEVO: Contador global
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        Stealth().apply_stealth_sync(page)
        
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
                resultado = extraer_ofertas_con_ia(html_util, busqueda['categoria'])
                
                # ✅ NUEVO: Manejo explícito de éxito/error
                if resultado and "productos" in resultado:
                    productos_guardados = 0
                    for i, prod in enumerate(resultado['productos'], 1):
                        try:
                            link_real = links_reales[i-1] if i-1 < len(links_reales) else ""
                            link_limpio = limpiar_link(link_real)
                            
                            guardar_producto({
                                'titulo': prod.get('titulo'),
                                'precio': float(prod.get('precio', 0)),
                                'envio_gratis': 1 if prod.get('envio_gratis') else 0,
                                'link': link_limpio,
                                'categoria': busqueda['categoria'],
                                'tienda': 'MercadoLibre'
                            })
                            productos_guardados += 1
                        except Exception as e:
                            print(f"   ❌ Error guardando producto: {e}")
                    
                    total_guardados += productos_guardados
                    print(f"   💾 {productos_guardados} productos guardados.")
                    
                else:
                    print(f"   ⚠️ La IA no devolvió productos para {busqueda['categoria']}.")
                    if resultado and "error" in resultado:
                        print(f"   🤖 IA dice: {resultado['error']}")
                
            except Exception as e:
                print(f"❌ Error en {busqueda['categoria']}: {e}")
        
        browser.close()
        print(f"\n🏁 Bot finalizado. TOTAL GUARDADOS: {total_guardados} productos.")

if __name__ == "__main__":
    run()