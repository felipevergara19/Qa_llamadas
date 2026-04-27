import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, User, Headphones, CheckCircle2, AlertCircle } from 'lucide-react';

export default function CallDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const response = await api.get(`/api/v1/evaluaciones/${id}`);
        setData(response.data);
      } catch (error) {
        console.error("Error fetching detail:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return <div className="p-8 text-gray-500">Cargando detalles de la auditoría...</div>;
  }

  if (!data) {
    return <div className="p-8 text-red-500">Error al cargar la llamada o no existe evaluación.</div>;
  }

  const parseTranscript = (text) => {
    if (!text) return [];
    // Las llamadas traen el formato Agent: ... Debtor: ...
    // Hacemos split usando expresiones regulares para conservar el prefijo
    const lines = text.split(/(?=Agent:|Debtor:)/g);
    return lines.map((line, idx) => {
      const isAgent = line.trim().startsWith('Agent:');
      const isDebtor = line.trim().startsWith('Debtor:');
      const content = line.replace('Agent:', '').replace('Debtor:', '').trim();
      
      if (!isAgent && !isDebtor) return { speaker: 'System', content: line.trim(), key: idx };
      
      return { speaker: isAgent ? 'Agent' : 'Debtor', content, key: idx };
    });
  };

  const transcriptLines = parseTranscript(data.transcripcion_completa);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Panel Izquierdo: Resumen y Rúbrica */}
      <div className="w-1/3 bg-white border-r border-gray-200 overflow-y-auto flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <Link to="/" className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 mb-4 font-medium">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Volver al panel
          </Link>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Llamada #{id}</h2>
          <p className="text-sm text-gray-500 mb-4">Empresa: <span className="font-semibold text-gray-700">{data.cliente}</span></p>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-xs text-blue-600 font-semibold uppercase">Puntaje IA</div>
              <div className="text-2xl font-bold text-blue-900">{data.resultados_ia.puntaje_total} <span className="text-sm font-normal">pts</span></div>
            </div>
            <div className={`p-3 rounded-lg ${data.resultados_ia.error_critico ? 'bg-red-50' : 'bg-green-50'}`}>
              <div className={`text-xs font-semibold uppercase ${data.resultados_ia.error_critico ? 'text-red-600' : 'text-green-600'}`}>Severidad</div>
              <div className={`text-sm font-bold mt-1 ${data.resultados_ia.error_critico ? 'text-red-900' : 'text-green-900'}`}>
                {data.resultados_ia.error_critico ? 'Error Crítico Detectado' : 'Sin errores críticos'}
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 flex-1">
          <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Evaluación Detallada</h3>
          <div className="space-y-3">
            {Object.entries(data.rubrica_detallada || {}).map(([criterio, valor]) => {
              // Si el valor es numérico, 1 es pase, 0 es fallo. Si es booleano, true/false.
              const paso = valor === 1 || valor === true || valor === "1";
              return (
                <div key={criterio} className={`flex items-center justify-between p-3 rounded-lg border ${paso ? 'bg-white border-gray-200' : 'bg-red-50 border-red-100'}`}>
                  <span className="text-sm font-medium text-gray-700 capitalize">{criterio.replace(/_/g, ' ')}</span>
                  {paso ? <CheckCircle2 className="w-5 h-5 text-green-500" /> : <AlertCircle className="w-5 h-5 text-red-500" />}
                </div>
              );
            })}
          </div>

          <div className="mt-8">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Resumen IA</h3>
            <p className="text-sm text-gray-600 leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-100">
              {data.resultados_ia.resumen_analisis}
            </p>
          </div>
        </div>
      </div>

      {/* Panel Derecho: Transcripción */}
      <div className="w-2/3 bg-gray-50 flex flex-col h-full">
        <div className="p-6 bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
          <h3 className="text-lg font-bold text-gray-800">Transcripción de la Llamada</h3>
          <p className="text-sm text-gray-500">Mora: {data.datos_colly.dias_mora} días | Deuda: ${data.datos_colly.deuda_total}</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {transcriptLines.length === 0 ? (
            <div className="text-center text-gray-500 mt-10">No hay transcripción disponible para esta llamada.</div>
          ) : (
            transcriptLines.map((line) => (
              <div key={line.key} className={`flex ${line.speaker === 'Agent' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex max-w-[80%] ${line.speaker === 'Agent' ? 'flex-row-reverse' : 'flex-row'}`}>
                  
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${line.speaker === 'Agent' ? 'bg-blue-100 ml-3' : 'bg-gray-200 mr-3'}`}>
                    {line.speaker === 'Agent' ? <Headphones className="w-4 h-4 text-blue-600" /> : <User className="w-4 h-4 text-gray-600" />}
                  </div>
                  
                  <div className={`p-4 rounded-2xl shadow-sm text-sm leading-relaxed ${
                    line.speaker === 'Agent' 
                      ? 'bg-blue-600 text-white rounded-tr-none' 
                      : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
                  }`}>
                    {line.content}
                  </div>

                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
