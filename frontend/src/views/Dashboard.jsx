import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { Search, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

export default function Dashboard() {
  const [llamadas, setLlamadas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEmpresa, setFilterEmpresa] = useState('');

  useEffect(() => {
    fetchLlamadas();
  }, []);

  const fetchLlamadas = async () => {
    try {
      const response = await api.get('/api/v1/llamadas');
      setLlamadas(response.data.data || []);
    } catch (error) {
      console.error("Error fetching llamadas:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLlamadas = llamadas.filter((item) => {
    const matchesSearch = 
      item.id_llamada.toString().includes(searchTerm) || 
      item.empresa.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesEmpresa = filterEmpresa ? item.empresa === filterEmpresa : true;
    
    return matchesSearch && matchesEmpresa;
  });

  const getStatusBadge = (status, isIA = false) => {
    let colorClass = "bg-gray-100 text-gray-800";
    const s = status.toLowerCase();
    
    if (s.includes('aprobado') || s.includes('entregado') || s.includes('compromiso') || s.includes('pagado')) {
      colorClass = "bg-green-100 text-green-800";
    } else if (s.includes('reprobado') || s.includes('equivocado') || s.includes('rechazado')) {
      colorClass = "bg-red-100 text-red-800";
    }

    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${colorClass}`}>
        {status}
      </span>
    );
  };

  const uniqueEmpresas = [...new Set(llamadas.map(l => l.empresa))];

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Panel de Auditorías</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Filtros */}
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex gap-4">
          <div className="relative flex-1 max-w-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm"
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

        {/* Tabla */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empresa</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mora / Venc.</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estatus Original</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estatus IA</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Puntaje</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alertas</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{llamada.id_llamada}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="font-semibold text-gray-900">{llamada.empresa}</div>
                      <div className="text-xs text-gray-400">{llamada.fecha_llamada.substring(0,10)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>{llamada.dias_mora} días</div>
                      <div className="text-xs text-gray-400">{llamada.fecha_vencimiento}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getStatusBadge(llamada.estatus_original)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getStatusBadge(llamada.resultados_ia.estatus_ia, true)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-semibold">
                      {llamada.resultados_ia.puntaje} pts
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {llamada.resultados_ia.error_critico ? (
                        <span className="flex items-center text-red-600 font-medium text-xs">
                          <AlertCircle className="w-4 h-4 mr-1" />
                          Crítico
                        </span>
                      ) : (
                        <span className="flex items-center text-green-600 font-medium text-xs">
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          Ok
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link to={`/llamada/${llamada.id_llamada}`} className="text-blue-600 hover:text-blue-900 font-medium">
                        Ver Detalle
                      </Link>
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
