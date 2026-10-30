# BOT-BUY

# 🛒 Bot de Ofertas con IA

Un bot que busca ofertas reales en MercadoLibre Argentina usando Inteligencia Artificial (Google Gemini) y guarda el historial de precios.

**Objetivo:** Democratizar el acceso a buenos precios y equilibrar la economía hacia las personas.

## ¿Cómo funciona?

1. Abre un navegador invisible (Playwright) y busca productos.
2. Extrae el HTML.
3. Le pasa el HTML a Gemini, que devuelve un JSON con títulos y precios.
4. Limpia los links y guarda todo en SQLite.
5. Una API en FastAPI sirve los datos a un frontend en Next.js.

## Instalación local

1. Cloná el repo:
   ```bash
   git clone https://github.com/TU-USUARIO/BOT-BUY.git
   cd bot-ofertas-ia

  2. *Creá el venv y activalo:
bash
python -m venv venv
source venv/Scripts/activate
Instalá las dependencias:

  3. *Instalá las dependencias:
bash
pip install -r requirements.txt
playwright install chromium
Configurá la API Key de Gemini en un archivo .env:

  4. *Configurá la API Key de Gemini en un archivo .env:
env
GEMINI_API_KEY=tu_clave_aca
Corré el bot:

  5. *Corré el bot:
bash
python test_navegador.py
Corré la API:

  6. *Corré la API:
bash
uvicorn api:app --reload
Corré el frontend (en otra terminal):

  7. Corré el frontend (en otra terminal):
bash
cd frontend-ofertas
npm install
npm run dev
