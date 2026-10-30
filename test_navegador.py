import os
import json
import time
import sqlite3
import re
from google import genai
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

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
        INSERT INTO productos (titulo, precio, envio_gratis, link)
        VALUES (?, ?, ?, ?)
    ''', (producto['titulo'], producto['precio'], producto['envio_gratis'], producto['link']))
    conn.commit()
    conn.close()

# ==================== LIMPIAR LINKS ====================
def limpiar_link(url):
    """Extrae solo la URL base del producto, sin tracking"""
    if not url:
        return ""
    # Buscamos el patrón de MercadoLibre: /MLA-1234567890 o /articulo/MLA123...
    match = re.search(r'(https?://[^/]+/[^?#]+(?:/p/MLA\d+|/MLA-?\d+))', url)
    if match:
        return match.group(1)
    # Si no, devolvemos el dominio principal
    match = re.search(r'(https?://[^/]+)', url)
    return match.group(1) if match else url

# ==================== IA ====================
def extraer_ofertas_con_ia(html_productos):
    print("🧠 Enviando los productos a Gemini...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró GEMINI_API_KEY")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Eres un experto en e-commerce. Te paso el HTML de los resultados de búsqueda de MercadoLibre.
    Extraé los primeros 5 productos. Para cada uno necesito:
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
    
    print("❌ Todos los modelos fallaron.")
    return None

# ==================== MAIN ====================
def run():
    print("🚀 Iniciando bot de ofertas...")
    init_db()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        Stealth().apply_stealth_sync(page)
        
        print("🔍 Buscando zapatillas en MercadoLibre...")
        page.goto("https://listado.mercadolibre.com.ar/zapatillas-running", timeout=30000)
        
        if "account-verification" in page.url:
            print("⚠️ Bloqueo detectado, buscando desde la home...")
            page.goto("https://www.mercadolibre.com.ar/", timeout=30000)
            page.wait_for_timeout(2000)
            search_box = page.locator("input.nav-search-input")
            if search_box.count() > 0:
                search_box.fill("zapatillas running")
                search_box.press("Enter")
                page.wait_for_timeout(4000)
        
        print("📦 Extrayendo tarjetas de productos...")
        try:
            page.wait_for_selector("ol.ui-search-layout", timeout=10000)
            tarjetas = page.locator("ol.ui-search-layout > li").all()
            print(f"✅ Encontramos {len(tarjetas)} tarjetas en la página.")
            
            # ✅ EXTRAER LINKS DIRECTAMENTE CON PLAYWRIGHT (más confiable)
            links_reales = []
            for tarjeta in tarjetas[:10]:
                try:
                    # Buscamos el link del producto dentro de la tarjeta
                    link_elem = tarjeta.locator("a.ui-search-link, a.poly-component__title").first
                    if link_elem.count() > 0:
                        href = link_elem.get_attribute("href")
                        if href:
                            links_reales.append(href)
                except:
                    links_reales.append("")
            
            print(f"✅ Extraídos {len(links_reales)} links reales.")
            
            # Preparamos el HTML para la IA
            html_util = ""
            for i, tarjeta in enumerate(tarjetas[:10]):
                html_util += f"\n<!-- PRODUCTO {i+1} -->\n"
                html_util += tarjeta.inner_html()
                
            print(f"📄 Tamaño del HTML filtrado: {len(html_util)} caracteres")
            
        except Exception as e:
            print(f"❌ No se pudieron extraer las tarjetas: {e}")
            html_util = ""
            links_reales = []
        
        if html_util:
            resultado = extraer_ofertas_con_ia(html_util)
            
            if resultado and "productos" in resultado and len(resultado["productos"]) > 0:
                print(f"\n✅ ¡La IA encontró {len(resultado['productos'])} productos!\n")
                for i, prod in enumerate(resultado['productos'], 1):
                    # ✅ Usamos el link real de Playwright, no el de la IA
                    link_real = links_reales[i-1] if i-1 < len(links_reales) else ""
                    link_limpio = limpiar_link(link_real)
                    
                    envio = "✅ Envío gratis" if prod.get('envio_gratis') else "❌ Sin envío gratis"
                    print(f"{i}. {prod.get('titulo')}")
                    print(f"   💰 ${prod.get('precio')} | {envio}")
                    print(f"   🔗 {link_limpio}")
                    
                    guardar_producto({
                        'titulo': prod.get('titulo'),
                        'precio': float(prod.get('precio', 0)),
                        'envio_gratis': 1 if prod.get('envio_gratis') else 0,
                        'link': link_limpio
                    })
                    print(f"   💾 Guardado en base de datos\n")
                
                print("✅ Todos los productos fueron guardados en ofertas.db")
            else:
                print("\n❌ La IA no pudo extraer productos.")
                if resultado and "error" in resultado:
                    print(f"🤖 La IA dice: {resultado['error']}")
        else:
            print("❌ No se encontró HTML útil.")
            page.wait_for_timeout(10000)
        
        browser.close()
        print("🏁 Bot cerrado.")

if __name__ == "__main__":
    run()
    