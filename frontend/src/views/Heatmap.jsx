/**
 * Heatmap.jsx — HU21: Mapa de calor de errores por criterio
 * Muestra qué criterios fallan con más frecuencia, filtrable por empresa.
 */
import { useState, useEffect } from 'react';
import { Flame, Filter } from 'lucide-react';
import api from '../api';

function colorPorTasa(tasa) {
  if (tasa >= 75) return { bg: 'bg-red-600',    text: 'text-white',      label: 'Crítico' };
  if (tasa >= 50) return { bg: 'bg-red-400',    text: 'text-white',      label: 'Alto' };
  if (tasa >= 25) return { bg: 'bg-orange-300', text: 'text-orange-900', label: 'Medio' };
  if (tasa >= 10) return { bg: 'bg-yellow-200', text: 'text-yellow-900', label: 'Bajo' };
  return           { bg: 'bg-green-100',   text: 'text-green-800',  label: 'Mínimo' };
}

export default function Heatmap() {
  const [datos, setDatos]         = useState(null);
  const [empresa, setEmpresa]     = useState('');
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');

  const fetchDatos = async (emp = '') => {
    setLoading(true);
    setError('');
    try {
      const params = emp ? `?empresa=${encodeURIComponent(emp)}` : '';
      const res = await api.get(`/api/v1/metricas/errores${params}`);
      setDatos(res.data);
    } catch {
      setError('No se pudo cargar el mapa de errores.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDatos(); }, []);

  const handleEmpresa = (e) => {
    setEmpresa(e.target.value);
    fetchDatos(e.target.value);
  };

  const maxFallos = datos?.criterios?.[0]?.total_fallos || 1;

  return (
    <div className="p-6 max-w-5xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Flame className="w-6 h-6 text-orange-500" />
            Mapa de Calor de Errores
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Frecuencia de fallo por criterio de auditoría
            {datos && ` · ${datos.total_evaluaciones} evaluaciones analizadas`}
          </p>
        </div>

        {/* Filtro por empresa */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={empresa}
            onChange={handleEmpresa}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">Todas las empresas</option>
            {datos?.empresas_disponibles?.map(e => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Leyenda */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <span className="text-xs text-gray-500 font-medium">Tasa de fallo:</span>
        {[
          { label: 'Mínimo (<10%)',  cls: 'bg-green-100' },
          { label: 'Bajo (10–24%)', cls: 'bg-yellow-200' },
          { label: 'Medio (25–49%)',cls: 'bg-orange-300' },
          { label: 'Alto (50–74%)', cls: 'bg-red-400' },
          { label: 'Crítico (≥75%)',cls: 'bg-red-600' },
        ].map(l => (
          <span key={l.label} className="flex items-center gap-1.5 text-xs text-gray-600">
            <span className={`w-3 h-3 rounded-sm ${l.cls}`} />
            {l.label}
          </span>
        ))}
      </div>

      {/* Contenido */}
      {loading ? (
        <div className="text-center text-gray-400 py-16">Cargando datos...</div>
      ) : error ? (
        <div className="text-red-500 p-4">{error}</div>
      ) : datos?.criterios?.length === 0 ? (
        <div className="text-center text-gray-400 py-16">
          No hay evaluaciones registradas{empresa ? ` para ${empresa}` : ''}.
        </div>
      ) : (
        <div className="space-y-2">
          {datos.criterios.map((item) => {
            const { bg, text, label } = colorPorTasa(item.tasa_fallo);
            const anchoPct = Math.max((item.total_fallos / maxFallos) * 100, 2);
            return (
              <div key={item.criterio} className="flex items-center gap-3 group">
                {/* Nombre del criterio */}
                <div className="w-52 flex-shrink-0 text-right">
                  <span className="text-sm text-gray-700 font-medium capitalize leading-tight">
                    {item.criterio.replace(/_/g, ' ')}
                  </span>
                </div>

                {/* Barra */}
                <div className="flex-1 bg-gray-100 rounded-full h-8 overflow-hidden">
                  <div
                    className={`h-full rounded-full flex items-center px-3 transition-all duration-500 ${bg}`}
                    style={{ width: `${anchoPct}%`, minWidth: '2.5rem' }}
                  >
                    <span className={`text-xs font-bold whitespace-nowrap ${text}`}>
                      {item.tasa_fallo}%
                    </span>
                  </div>
                </div>

                {/* Detalle */}
                <div className="w-36 flex-shrink-0 flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${bg} ${text}`}>
                    {label}
                  </span>
                  <span className="text-xs text-gray-400">
                    {item.total_fallos}/{item.total_evaluado}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
