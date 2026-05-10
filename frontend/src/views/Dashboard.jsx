import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { Search, AlertCircle, CheckCircle2, BarChart2, Phone, ShieldCheck, Star, X } from 'lucide-react';

export default function Dashboard() {
  const [llamadas, setLlamadas]   = useState([]);
  const [kpis, setKpis]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [searchTerm, setSearchTerm]       = useState('');
  const [filterEmpresa, setFilterEmpresa] = useState('');
  const [alertaDismissed, setAlertaDismissed] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/api/v1/llamadas'),
      api.get('/api/v1/dashboard'),
    ]).then(([resLlamadas, resDash]) => {
      setLlamadas(resLlamadas.data.data || []);
      setKpis(resDash.data);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredLlamadas = llamadas.filter((item) => {
    const matchesSearch =
      item.id_llamada.toString().includes(searchTerm) ||
      item.empresa.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEmpresa = filterEmpresa ? item.empresa === filterEmpresa : true;
    return matchesSearch && matchesEmpresa;
  });

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    let cls = 'bg-gray-100 text-gray-800';
    if (s.includes('aprobado') || s.includes('entregado') || s.includes('compromiso') || s.includes('pagado'))
      cls = 'bg-green-100 text-green-800';
    else if (s.includes('reprobado') || s.includes('equivocado') || s.includes('rechazado'))
      cls = 'bg-red-100 text-red-800';
    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${cls}`}>
        {status}
      </span>
    );
  };

  const uniqueEmpresas = [...new Set(llamadas.map(l => l.empresa))];
  const llamadasCriticas = llamadas.filter(l => l.resultados_ia.error_critico);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Panel de Auditorias</h1>
      </div>

      {/* HU25: Banner de alerta crítica global */}
      {!alertaDismissed && llamadasCriticas.length > 0 && (
        <div className="mb-6 flex items-start gap-3 bg-red-50 border border-red-300 text-red-800 rounded-xl px-4 py-3 shadow-sm">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0 text-red-600" />
          <div className="flex-1">
            <p className="font-semibold text-sm">
              {llamadasCriticas.length} llamada{llamadasCriticas.length > 1 ? 's' : ''} con error crítico detectado
            </p>
            <p className="text-xs text-red-600 mt-0.5">
              {llamadasCriticas.length > 1
                ? `IDs: ${llamadasCriticas.map(l => '#' + l.id_llamada).join(', ')} — Revisar criterios de severidad.`
                : `Llamada #${llamadasCriticas[0].id_llamada} (${llamadasCriticas[0].empresa}) — Revisar criterios de severidad.`
              }
            </p>
          </div>
          <button
            onClick={() => setAlertaDismissed(true)}
            className="text-red-400 hover:text-red-600 transition-colors flex-shrink-0"
            title="Cerrar alerta"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {kpis && (
        <>
          {/* KPI CARDS - HU17 */}
          <div className="grid grid-cols-2 gap-4 mb-4 sm:grid-cols-4">
            {[
              { label: 'Llamadas Recibidas',  value: kpis.kpis_globales.total_llamadas_recibidas,  icon: <Phone className="w-6 h-6 text-blue-500" />,   bg: 'bg-blue-50 border-blue-100' },
              { label: 'Llamadas Auditadas',  value: kpis.kpis_globales.total_llamadas_auditadas,  icon: <ShieldCheck className="w-6 h-6 text-green-500" />, bg: 'bg-green-50 border-green-100' },
              { label: 'Cobertura SLA',       value: kpis.kpis_globales.cobertura_porcentaje + '%',icon: <BarChart2 className="w-6 h-6 text-purple-500" />, bg: 'bg-purple-50 border-purple-100' },
              { label: 'Calidad Promedio',    value: kpis.kpis_globales.calidad_promedio + ' pts', icon: <Star className="w-6 h-6 text-yellow-500" />,  bg: 'bg-yellow-50 border-yellow-100' },
            ].map((card) => (
              <div key={card.label} className={`rounded-xl border p-4 flex items-center gap-4 shadow-sm ${card.bg}`}>
                <div className="flex-shrink-0">{card.icon}</div>
                <div>
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{card.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                </div>
              </div>
            ))}
          </div>

          {/* DISTRIBUCION ESTATUS */}
          {Object.keys(kpis.distribucion_estatus || {}).length > 0 && (
            <div className="mb-6 bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Distribucion por Estatus IA</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(kpis.distribucion_estatus).map(([estatus, cantidad]) => (
                  <span key={estatus} className="px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-700">
                    {estatus}: <span className="font-bold">{cantidad}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* TABLA */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex gap-4">
          <div className="relative flex-1 max-w-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm"
              placeholder="Buscar por ID o Cliente..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <select
            className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={filterEmpresa}
            onChange={(e) => setFilterEmpresa(e.target.value)}
          >
            <option value="">Todas las Empresas</option>
            {uniqueEmpresas.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {['ID','Empresa','Mora / Venc.','Estatus Original','Estatus IA','Puntaje','Alertas','Acciones'].map(h => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan="8" className="px-6 py-4 text-center text-sm text-gray-500">Cargando datos...</td></tr>
              ) : filteredLlamadas.length === 0 ? (
                <tr><td colSpan="8" className="px-6 py-4 text-center text-sm text-gray-500">No se encontraron llamadas</td></tr>
              ) : (
                filteredLlamadas.map((llamada) => (
                  <tr key={llamada.id_llamada} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{llamada.id_llamada}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="font-semibold text-gray-900">{llamada.empresa}</div>
                      <div className="text-xs text-gray-400">{String(llamada.fecha_llamada).substring(0, 10)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>{llamada.dias_mora} dias</div>
                      <div className="text-xs text-gray-400">{llamada.fecha_vencimiento}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(llamada.estatus_original)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(llamada.resultados_ia.estatus_ia)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-semibold">{llamada.resultados_ia.puntaje} pts</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {llamada.resultados_ia.error_critico ? (
                        <span className="flex items-center text-red-600 font-medium text-xs"><AlertCircle className="w-4 h-4 mr-1" />Critico</span>
                      ) : (
                        <span className="flex items-center text-green-600 font-medium text-xs"><CheckCircle2 className="w-4 h-4 mr-1" />Ok</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link to={`/llamada/${llamada.id_llamada}`} className="text-blue-600 hover:text-blue-900 font-medium">Ver Detalle</Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
