import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, User, Headphones, CheckCircle2, AlertCircle, Info } from 'lucide-react';

export default function CallDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/api/v1/evaluaciones/${id}`)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-gray-500">Cargando detalles de la auditoria...</div>;
  if (!data)   return <div className="p-8 text-red-500">Error al cargar la llamada o no existe evaluacion.</div>;

  const parseTranscript = (text) => {
    if (!text) return [];
    return text.split(/(?=Agent:|Debtor:)/g).map((line, idx) => {
      const isAgent  = line.trim().startsWith('Agent:');
      const isDebtor = line.trim().startsWith('Debtor:');
      const content  = line.replace('Agent:', '').replace('Debtor:', '').trim();
      return { speaker: isAgent ? 'Agent' : isDebtor ? 'Debtor' : 'System', content, key: idx };
    });
  };

  const transcriptLines = parseTranscript(data.transcripcion_completa);

  // HU14: usar feedback_criterios si existe, fallback a rubrica_detallada
  const feedbackItems = data.feedback_criterios && data.feedback_criterios.length > 0
    ? data.feedback_criterios
    : Object.entries(data.rubrica_detallada || {})
        .filter(([k]) => !['Resumen','Estatus_detectado','Estatus_coherente'].includes(k))
        .map(([nombre, val]) => ({
          criterio: nombre,
          resultado: val === 1 || val === true || val === '1',
          descripcion: null,
          peso: 1,
          es_severidad: false,
        }));

  const estadoValidacion = data.resultados_ia?.estado_validacion || 'pendiente';
  const badgeValidacion = {
    pendiente:  'bg-yellow-100 text-yellow-800',
    aprobada:   'bg-green-100 text-green-800',
    rechazada:  'bg-red-100 text-red-800',
  }[estadoValidacion] || 'bg-gray-100 text-gray-700';

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">

      {/* PANEL IZQUIERDO */}
      <div className="w-1/3 bg-white border-r border-gray-200 overflow-y-auto flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <Link to="/" className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 mb-4 font-medium">
            <ArrowLeft className="w-4 h-4 mr-1" />Volver al panel
          </Link>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Llamada #{id}</h2>
          <p className="text-sm text-gray-500 mb-1">Empresa: <span className="font-semibold text-gray-700">{data.cliente}</span></p>
          <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${badgeValidacion}`}>
            Validacion: {estadoValidacion}
          </span>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-xs text-blue-600 font-semibold uppercase">Puntaje IA</div>
              <div className="text-2xl font-bold text-blue-900">
                {data.resultados_ia.puntaje_total} <span className="text-sm font-normal">pts</span>
              </div>
            </div>
            <div className={`p-3 rounded-lg ${data.resultados_ia.error_critico ? 'bg-red-50' : 'bg-green-50'}`}>
              <div className={`text-xs font-semibold uppercase ${data.resultados_ia.error_critico ? 'text-red-600' : 'text-green-600'}`}>Severidad</div>
              <div className={`text-sm font-bold mt-1 ${data.resultados_ia.error_critico ? 'text-red-900' : 'text-green-900'}`}>
                {data.resultados_ia.error_critico ? 'Error Critico' : 'Sin errores'}
              </div>
            </div>
          </div>
        </div>

        {/* HU14: FEEDBACK POR CRITERIO */}
        <div className="p-6 flex-1">
          <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Evaluacion por Criterio</h3>
          <div className="space-y-3">
            {feedbackItems.map((item) => (
              <div
                key={item.criterio}
                className={`p-3 rounded-lg border ${
                  item.es_severidad
                    ? item.resultado ? 'bg-white border-gray-200' : 'bg-red-50 border-red-300'
                    : item.resultado  ? 'bg-white border-gray-200' : 'bg-orange-50 border-orange-100'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 mb-0.5">
                      <span className="text-sm font-semibold text-gray-800 capitalize">
                        {item.criterio.replace(/_/g, ' ')}
                      </span>
                      {item.es_severidad && (
                        <span className="text-xs px-1 rounded bg-red-100 text-red-700 font-bold">SEV</span>
                      )}
                      {item.peso > 1 && (
                        <span className="text-xs px-1 rounded bg-blue-100 text-blue-700">x{item.peso}</span>
                      )}
                    </div>
                    {item.descripcion && (
                      <p className="text-xs text-gray-500 leading-snug flex gap-1">
                        <Info className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-400" />
                        {item.descripcion}
                      </p>
                    )}
                  </div>
                  <div className="flex-shrink-0 mt-0.5">
                    {item.resultado
                      ? <CheckCircle2 className="w-5 h-5 text-green-500" />
                      : <AlertCircle  className="w-5 h-5 text-red-500" />
                    }
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* RESUMEN IA */}
          <div className="mt-6">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Resumen IA</h3>
            <p className="text-sm text-gray-600 leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-100">
              {data.resultados_ia.resumen_analisis}
            </p>
          </div>
        </div>
      </div>

      {/* PANEL DERECHO: TRANSCRIPCION */}
      <div className="w-2/3 bg-gray-50 flex flex-col h-full">
        <div className="p-6 bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
          <h3 className="text-lg font-bold text-gray-800">Transcripcion de la Llamada</h3>
          <p className="text-sm text-gray-500">
            Mora: {data.datos_colly.dias_mora} dias | Deuda: ${data.datos_colly.deuda_total}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {transcriptLines.length === 0 ? (
            <div className="text-center text-gray-500 mt-10">No hay transcripcion disponible.</div>
          ) : (
            transcriptLines.map((line) => (
              <div key={line.key} className={`flex ${line.speaker === 'Agent' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex max-w-[80%] ${line.speaker === 'Agent' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${line.speaker === 'Agent' ? 'bg-blue-100 ml-3' : 'bg-gray-200 mr-3'}`}>
                    {line.speaker === 'Agent'
                      ? <Headphones className="w-4 h-4 text-blue-600" />
                      : <User className="w-4 h-4 text-gray-600" />
                    }
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
