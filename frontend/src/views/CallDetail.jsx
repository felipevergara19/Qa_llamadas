import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, User, Headphones, CheckCircle2, AlertCircle, Info, RefreshCw, ThumbsUp, ThumbsDown, RotateCcw } from 'lucide-react';

export default function CallDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reauditando, setReauditando] = useState(false);
  const [reauditoriaMsg, setReauditoriaMsg] = useState(null); // { ok, texto }
  const [validando, setValidando] = useState(false);
  const [validacionMsg, setValidacionMsg] = useState(null); // { ok, texto }
  const [comentario, setComentario] = useState('');
  const [mostrarFormValidacion, setMostrarFormValidacion] = useState(false);

  const userRaw = localStorage.getItem('qa_user');
  const currentUser = userRaw ? JSON.parse(userRaw) : null;
  const puedeValidar = ['admin', 'analista_qa'].includes(currentUser?.rol);

  const fetchData = () => {
    setLoading(true);
    api.get(`/api/v1/evaluaciones/${id}`)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [id]);

  const handleValidar = async (estado) => {
    if (!comentario.trim()) {
      setValidacionMsg({ ok: false, texto: 'Debes escribir una justificación antes de validar.' });
      return;
    }
    setValidando(true);
    setValidacionMsg(null);
    try {
      await api.put(`/api/v1/evaluaciones/${id}/validacion`, { estado, comentario: comentario.trim() });
      setValidacionMsg({ ok: true, texto: `Evaluación "${estado}" registrada correctamente.` });
      setComentario('');
      setMostrarFormValidacion(false);
      fetchData();
    } catch (e) {
      const msg = e.response?.data?.detail || 'Error al actualizar la validación';
      setValidacionMsg({ ok: false, texto: msg });
    } finally {
      setValidando(false);
    }
  };

  const handleReauditar = async () => {
    if (!window.confirm('¿Re-auditar esta llamada con IA? La evaluación actual se reemplazará.')) return;
    setReauditando(true);
    setReauditoriaMsg(null);
    try {
      const res = await api.post(`/api/v1/auditoria/reauditar/${id}`);
      setReauditoriaMsg({ ok: true, texto: `Re-auditoría completada — ${res.data.puntaje_logrado} pts${res.data.error_critico ? ' · ERROR CRÍTICO detectado' : ''}` });
      fetchData(); // recargar el panel con los nuevos resultados
    } catch (e) {
      const msg = e.response?.data?.detail || 'Error al re-auditar';
      setReauditoriaMsg({ ok: false, texto: msg });
    } finally {
      setReauditando(false);
    }
  };

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

          {/* HU22: Apelación de nota — Validación humana (HITL) */}
          {puedeValidar && (
            <div className="mt-4 border border-gray-200 rounded-xl overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 flex items-center justify-between">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Validación humana (HITL)
                </p>
                {estadoValidacion !== 'pendiente' && (
                  <button
                    onClick={() => { setMostrarFormValidacion(true); setValidacionMsg(null); }}
                    title="Editar validación"
                    className="text-xs text-gray-400 hover:text-blue-500 flex items-center gap-1"
                  >
                    <RotateCcw className="w-3 h-3" /> Cambiar
                  </button>
                )}
              </div>

              {/* Estado actual ya validado */}
              {estadoValidacion !== 'pendiente' && !mostrarFormValidacion ? (
                <div className={`p-4 ${estadoValidacion === 'aprobada' ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {estadoValidacion === 'aprobada'
                      ? <ThumbsUp className="w-4 h-4 text-green-600" />
                      : <ThumbsDown className="w-4 h-4 text-red-600" />
                    }
                    <span className={`text-sm font-bold ${estadoValidacion === 'aprobada' ? 'text-green-800' : 'text-red-800'}`}>
                      Evaluación {estadoValidacion === 'aprobada' ? 'Aprobada' : 'Rechazada'}
                    </span>
                  </div>
                  {data.resultados_ia.comentario_auditor && (
                    <p className="text-xs text-gray-600 bg-white border border-gray-200 rounded-lg px-3 py-2 italic leading-relaxed">
                      "{data.resultados_ia.comentario_auditor}"
                    </p>
                  )}
                </div>
              ) : (
                /* Formulario de validación */
                <div className="p-4 space-y-3">
                  <p className="text-xs text-gray-500">
                    Revisa la transcripción y los criterios, luego escribe tu justificación y valida.
                  </p>
                  <textarea
                    value={comentario}
                    onChange={(e) => setComentario(e.target.value)}
                    rows={3}
                    placeholder="Ej: Se verificó manualmente que el agente sí realizó el saludo correcto aunque la IA lo marcó como fallo..."
                    className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleValidar('aprobada')}
                      disabled={validando}
                      className="flex-1 flex items-center justify-center gap-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <ThumbsUp className="w-4 h-4" />
                      Aprobar
                    </button>
                    <button
                      onClick={() => handleValidar('rechazada')}
                      disabled={validando}
                      className="flex-1 flex items-center justify-center gap-1.5 bg-red-600 hover:bg-red-700 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <ThumbsDown className="w-4 h-4" />
                      Rechazar
                    </button>
                  </div>
                  {validacionMsg && (
                    <div className={`text-xs px-3 py-2 rounded-lg font-medium ${
                      validacionMsg.ok
                        ? 'bg-green-50 text-green-700 border border-green-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                      {validacionMsg.ok ? '✓ ' : '✗ '}{validacionMsg.texto}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* HU27: Botón re-auditoría individual */}
          <div className="mt-4">
            <button
              onClick={handleReauditar}
              disabled={reauditando}
              className="w-full flex items-center justify-center gap-2 border border-gray-300 hover:border-blue-400 hover:bg-blue-50 text-gray-600 hover:text-blue-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${reauditando ? 'animate-spin' : ''}`} />
              {reauditando ? 'Re-auditando con IA…' : 'Re-auditar esta llamada'}
            </button>
            {reauditoriaMsg && (
              <div className={`mt-2 text-xs px-3 py-2 rounded-lg font-medium ${
                reauditoriaMsg.ok
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {reauditoriaMsg.ok ? '✓ ' : '✗ '}{reauditoriaMsg.texto}
              </div>
            )}
          </div>

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
                {data.resultados_ia.error_critico ? 'Error Crítico' : 'Sin errores'}
              </div>
              {/* Indicador de anulación humana */}
              {!data.resultados_ia.error_critico && estadoValidacion === 'aprobada' && (
                <div className="text-xs text-green-600 mt-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Anulado por analista
                </div>
              )}
            </div>
          </div>

          {/* Banner de errores críticos con detalle */}
          {data.resultados_ia.error_critico && (() => {
            const errores = data.resultados_ia.errores_criticos || [];
            return (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs font-bold text-red-700 uppercase mb-1.5 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  Criterio(s) de severidad que fallaron
                </p>
                {errores.length > 0 ? (
                  <ul className="space-y-1">
                    {errores.map((e, i) => (
                      <li key={i} className="text-xs text-red-800 bg-red-100 px-2 py-1 rounded font-medium">
                        · {e}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-red-600 italic">Re-audita esta llamada para obtener el detalle.</p>
                )}
              </div>
            );
          })()}
        </div>

        {/* HU14: FEEDBACK POR CRITERIO */}
        <div className="p-6 flex-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Evaluacion por Criterio</h3>
            {/* HU12: Versión de rúbrica usada */}
            {data.rubrica_version && (
              <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-semibold">
                Rúbrica v{data.rubrica_version}
              </span>
            )}
          </div>
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
