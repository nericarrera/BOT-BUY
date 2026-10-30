'use client';

import { useState, useEffect } from 'react';

interface Oferta {
  id: number;
  titulo: string;
  precio: number;
  envio_gratis: number;
  link: string;
  fecha: string;
}

export default function Home() {
  const [ofertas, setOfertas] = useState<Oferta[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroEnvio, setFiltroEnvio] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // ✅ URL desde variable de entorno (funciona en local y en Vercel)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    fetch(`${apiUrl}/ofertas`)
      .then(res => {
        if (!res.ok) throw new Error('Error al conectar con la API');
        return res.json();
      })
      .then(data => {
        // Filtramos duplicados
        const unicas = data.ofertas.filter((oferta: Oferta, index: number, self: Oferta[]) =>
          index === self.findIndex(o => o.titulo === oferta.titulo && o.precio === oferta.precio)
        );
        setOfertas(unicas);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const ofertasFiltradas = filtroEnvio
    ? ofertas.filter(o => o.envio_gratis === 1)
    : ofertas;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Buscando las mejores ofertas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center max-w-md">
          <p className="text-6xl mb-4">⚠️</p>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No pudimos conectar con el bot</h2>
          <p className="text-gray-500 mb-6">{error}</p>
          <p className="text-sm text-gray-400">
            Asegurate de que la API de Python esté corriendo con:<br/>
            <code className="bg-gray-100 px-2 py-1 rounded text-xs">uvicorn api:app --reload</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-black text-gray-900 flex items-center gap-2">
                🛒 Bot de Ofertas
              </h1>
              <p className="text-gray-500 mt-1">Las mejores ofertas de MercadoLibre, actualizadas con IA</p>
            </div>
            <div className="bg-green-100 text-green-800 px-4 py-2 rounded-full font-semibold">
              {ofertasFiltradas.length} ofertas encontradas
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* FILTROS */}
        <div className="mb-8 flex items-center gap-4">
          <button
            onClick={() => setFiltroEnvio(!filtroEnvio)}
            className={`px-5 py-2.5 rounded-full font-semibold transition-all ${
              filtroEnvio
                ? 'bg-green-600 text-white shadow-lg'
                : 'bg-white text-gray-700 border border-gray-200 hover:border-gray-300'
            }`}
          >
            ✅ Solo envío gratis
          </button>
        </div>

        {/* GRID DE OFERTAS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {ofertasFiltradas.map((oferta) => (
            <div
              key={oferta.id}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
            >
              <div className="p-6">
                <h2 className="font-bold text-lg text-gray-900 mb-3 line-clamp-2 min-h-[56px]">
                  {oferta.titulo}
                </h2>
                
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-3xl font-black text-green-600">
                    ${oferta.precio.toLocaleString('es-AR')}
                  </span>
                </div>

                {oferta.envio_gratis === 1 && (
                  <span className="inline-block text-xs bg-green-100 text-green-800 px-3 py-1.5 rounded-full font-semibold mb-4">
                    🚚 Envío gratis
                  </span>
                )}

                <a
                  href={oferta.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-gray-900 text-white text-center py-3 rounded-xl font-semibold hover:bg-gray-800 transition-colors"
                >
                  Ver en MercadoLibre →
                </a>
              </div>
            </div>
          ))}
        </div>

        {ofertasFiltradas.length === 0 && (
          <div className="text-center py-20">
            <p className="text-6xl mb-4">🔍</p>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No hay ofertas con ese filtro</h2>
            <p className="text-gray-500">Probá desactivando el filtro de envío gratis.</p>
          </div>
        )}
      </div>

      <footer className="border-t border-gray-200 mt-16 py-8 text-center text-gray-500 text-sm">
        Hecho con ❤️ para equilibrar la economía popular
      </footer>
    </main>
  );
}