from playwright.sync_api import sync_playwright

def run():
    print("🚀 Iniciando navegador invisible...")
    
    with sync_playwright() as p:
        # headless=False para que puedas VER el navegador trabajar
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🔍 Buscando zapatillas en MercadoLibre...")
        page.goto("https://listado.mercadolibre.com.ar/zapatillas-running")
        
        # Esperamos a que carguen los resultados
        page.wait_for_selector(".ui-search-result__wrapper", timeout=15000)
        
        # Extraemos el primer producto
        primer_titulo = page.locator(".ui-search-item__title").first.inner_text()
        primer_precio = page.locator(".andes-money-amount__fraction").first.inner_text()
        
        print("✅ ¡Encontramos algo!")
        print(f"Producto: {primer_titulo}")
        print(f"Precio: ${primer_precio}")
        
        # Esperamos 5 segundos para que veas la ventana
        page.wait_for_timeout(5000)
        browser.close()
        print("🏁 Navegador cerrado.")

if __name__ == "__main__":
    run()