import os
import json
from google import genai
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

# Cargar la clave del archivo .env
load_dotenv()

def extraer_ofertas_con_ia(html_content):
    print("🧠 Enviando la página a Gemini para que extraiga los datos...")
    
    # Configurar el nuevo cliente de Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró GEMINI_API_KEY en el archivo .env")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Eres un experto en e-commerce. Te paso el HTML de una página de búsqueda de MercadoLibre.
    Extraé los primeros 5 productos. Para cada uno necesito:
    1. titulo
    2. precio (solo el número, sin puntos ni símbolos)
    3. envio_gratis (true/false)
    4. link (la URL del producto)
    
    Devolveme ÚNICAMENTE un JSON válido con un array llamado "productos".
    No agregues texto extra, solo el JSON.
    
    HTML:
    {html_content[:30000]} 
    """
    
    try:
        # Usamos el modelo flash, que es rápido y tiene capa gratuita
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt
        )
        
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpio)
    except Exception as e:
        print(f"❌ Error con la IA: {e}")
        return None

def run():
    print("🚀 Iniciando navegador 'disfrazado'...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        Stealth().apply_stealth_sync(page)
        
        print("🔍 Buscando zapatillas en MercadoLibre...")
        page.goto("https://listado.mercadolibre.com.ar/zapatillas-running", timeout=30000)
        
        # Si nos manda a verificar, volvemos a la home y buscamos
        if "account-verification" in page.url:
            page.goto("https://www.mercadolibre.com.ar/", timeout=30000)
            page.locator("input.nav-search-input").fill("zapatillas running")
            page.locator("input.nav-search-input").press("Enter")
            page.wait_for_timeout(3000)
        
        # Esperamos a que cargue la grilla de productos
        try:
            page.wait_for_selector("ol.ui-search-layout", timeout=15000)
        except:
            print("⚠️ No se encontró la grilla, intentando igual...")
            
        # Pasamos el HTML a la IA
        html = page.content()
        resultado = extraer_ofertas_con_ia(html)
        
        if resultado and "productos" in resultado:
            print(f"\n✅ ¡La IA encontró {len(resultado['productos'])} productos!\n")
            for i, prod in enumerate(resultado['productos'], 1):
                envio = "✅ Envío gratis" if prod.get('envio_gratis') else "❌ Sin envío gratis"
                print(f"{i}. {prod.get('titulo')}")
                print(f"   💰 ${prod.get('precio')} | {envio}")
                print(f"   🔗 {prod.get('link')}\n")
        else:
            print("❌ La IA no pudo extraer los productos.")
            page.wait_for_timeout(10000)
        
        browser.close()
        print("🏁 Navegador cerrado.")

if __name__ == "__main__":
    run()