'use client';

import { useState, useEffect, useMemo } from 'react';
import Image from 'next/image';

interface Oferta {
  id: number;
  titulo: string;
  precio: number;
  envio_gratis: number;
  imagen: string;
  categoria: string;
  link: string;
  fecha: string;
}

// ==================== CONFIGURACIÓN DE CATEGORÍAS ====================
const CATEGORIAS = [
  { id: 'todas', nombre: 'Todas', emoji: '🔥' },
  { id: 'celulares', nombre: 'Celulares', emoji: '📱' },
  { id: 'computacion', nombre: 'Computación', emoji: '💻' },
  { id: 'televisores', nombre: 'TVs', emoji: '📺' },
  { id: 'cocinas', nombre: 'Cocinas', emoji: '🍳' },
  { id: 'heladeras', nombre: 'Heladeras', emoji: '🧊' },
  { id: 'muebles', nombre: 'Muebles', emoji: '🪑' },
  { id: 'zapatillas', nombre: 'Zapatillas', emoji: '👟' },
  { id: 'camperas', nombre: 'Camperas', emoji: '🧥' },
];

export default function Home() {
  const [ofertas, setOfertas] = useState<Oferta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filtros
  const [filtroEnvio, setFiltroEnvio] = useState(false);
  const [categoriaActiva, setCategoriaActiva] = useState('todas');
  const [busqueda, setBusqueda] = useState('');

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    fetch(`${apiUrl}/ofertas`)
      .then(res => {
        if (!res.ok) throw new Error('Error al conectar con la API');
        return res.json();
      })
      .then(data => {
        // Filtramos duplicados por título y precio
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

  // ✅ Filtrado optimizado con useMemo
  const ofertasFiltradas = useMemo(() => {
    return ofertas.filter(oferta => {
      // Filtro de categoría
      if (categoriaActiva !== 'todas' && oferta.categoria !== categoriaActiva) return false;
      
      // Filtro de envío gratis
      if (filtroEnvio && oferta.envio_gratis !== 1) return false;
      
      // Filtro de búsqueda por texto
      if (busqueda.trim() !== '') {
        const termino = busqueda.toLowerCase().trim();
        if (!oferta.titulo.toLowerCase().includes(termino)) return false;
      }
      
      return true;
    });
  }, [ofertas, categoriaActiva, filtroEnvio, busqueda]);

  // ==================== ESTADOS ====================
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
      {/* ==================== HEADER ==================== */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-gray-900 flex items-center gap-2">
                🛒 Cazador de Ofertas
              </h1>
              <p className="text-sm text-gray-500 mt-1">Las mejores ofertas reales, filtradas por IA</p>
            </div>
            <div className="bg-green-100 text-green-800 px-4 py-2 rounded-full font-semibold text-sm">
              {ofertasFiltradas.length} ofertas
            </div>
          </div>

          {/* BUSCADOR */}
          <div className="relative">
            <input
              type="text"
              placeholder="¿Qué estás buscando? Ej: TV Samsung, iPhone, zapatillas..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full px-12 py-3 bg-gray-100 rounded-xl border border-transparent focus:bg-white focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all text-gray-900 placeholder-gray-500"
            />
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-lg">🔍</span>
          </div>
        </div>

        {/* CATEGORÍAS (Scroll horizontal en mobile) */}
        <div className="border-t border-gray-100 bg-white">
          <div className="max-w-7xl mx-auto px-4 py-3 overflow-x-auto scrollbar-hide">
            <div className="flex gap-2 min-w-max">
              {CATEGORIAS.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setCategoriaActiva(cat.id)}
                  className={`px-4 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap ${
                    categoriaActiva === cat.id
                      ? 'bg-green-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {cat.emoji} {cat.nombre}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* ==================== FILTROS ACTIVOS ==================== */}
        <div className="mb-6 flex items-center gap-3 flex-wrap">
          <button
            onClick={() => setFiltroEnvio(!filtroEnvio)}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-all ${
              filtroEnvio
                ? 'bg-green-600 text-white shadow-md'
                : 'bg-white text-gray-700 border border-gray-200 hover:border-gray-300'
            }`}
          >
            🚚 Solo envío gratis
          </button>

          {(categoriaActiva !== 'todas' || filtroEnvio || busqueda) && (
            <button
              onClick={() => {
                setCategoriaActiva('todas');
                setFiltroEnvio(false);
                setBusqueda('');
              }}
              className="px-4 py-2 rounded-full text-sm font-semibold bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-all"
            >
              ✕ Limpiar filtros
            </button>
          )}
        </div>

        {/* ==================== GRID DE OFERTAS ==================== */}
        {ofertasFiltradas.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {ofertasFiltradas.map((oferta) => (
              <article
                key={oferta.id}
                className="group bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col"
              >
                {/* IMAGEN */}
                <div className="relative h-52 bg-gray-50 overflow-hidden">
                  {oferta.imagen ? (
                    <Image
                      src={oferta.imagen}
                      alt={oferta.titulo}
                      fill
                      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                      className="object-contain p-3 group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-6xl opacity-20">
                      📦
                    </div>
                  )}
                  
                  {/* Badge de categoría */}
                  <div className="absolute top-3 left-3">
                    <span className="bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded-full text-[11px] font-bold text-gray-700 uppercase tracking-wide shadow-sm">
                      {oferta.categoria}
                    </span>
                  </div>
                </div>

                {/* CONTENIDO */}
                <div className="p-4 flex flex-col flex-1">
                  <h2 className="font-bold text-base text-gray-900 mb-2 line-clamp-2 min-h-[48px] leading-snug">
                    {oferta.titulo}
                  </h2>
                  
                  <div className="mt-auto">
                    <div className="flex items-baseline gap-2 mb-2">
                      <span className="text-2xl font-black text-green-600">
                        ${oferta.precio.toLocaleString('es-AR')}
                      </span>
                    </div>

                    {oferta.envio_gratis === 1 && (
                      <div className="mb-3">
                        <span className="inline-block text-xs bg-green-50 text-green-700 px-2.5 py-1 rounded-full font-semibold border border-green-200">
                          🚚 Envío gratis
                        </span>
                      </div>
                    )}

                    <a
                      href={oferta.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full bg-gray-900 text-white text-center py-2.5 rounded-xl font-semibold hover:bg-green-600 transition-colors text-sm"
                    >
                      Ver oferta →
                    </a>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          /* ==================== SIN RESULTADOS ==================== */
          <div className="text-center py-20">
            <p className="text-6xl mb-4">🔍</p>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No hay ofertas con esos filtros</h2>
            <p className="text-gray-500 mb-6">Probá cambiando la categoría o limpiando los filtros.</p>
            <button
              onClick={() => {
                setCategoriaActiva('todas');
                setFiltroEnvio(false);
                setBusqueda('');
              }}
              className="px-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors"
            >
              Ver todas las ofertas
            </button>
          </div>
        )}
      </div>

      {/* ==================== FOOTER ==================== */}
      <footer className="border-t border-gray-200 mt-16 py-8 text-center text-gray-500 text-sm">
        <p className="font-semibold text-gray-700 mb-1">Cazador de Ofertas</p>
        <p>Hecho con ❤️ para equilibrar la economía popular</p>
      </footer>
    </main>
  );
}