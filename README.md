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
