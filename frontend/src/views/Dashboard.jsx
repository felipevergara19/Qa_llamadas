import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { Search, AlertCircle, CheckCircle2, BarChart2, Phone, ShieldCheck, Star, X, FileSpreadsheet, FileText, BrainCircuit, Upload } from 'lucide-react';

export default function Dashboard() {
  const [llamadas, setLlamadas]   = useState([]);
  const [kpis, setKpis]           = useState(null);
  const [precision, setPrecision] = useState(null);
  const [loading, setLoading]       = useState(true);

  const userRaw   = localStorage.getItem('qa_user');
  const userActual = userRaw ? JSON.parse(userRaw) : null;
  const esAdmin   = userActual?.rol === 'admin';
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEmpresa, setFilterEmpresa] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [alertaDismissed, setAlertaDismissed] = useState(false);
  const [showUpload, setShowUpload]     = useState(false);
  const [uploadForm, setUploadForm]     = useState({ empresa: '', call_id: '', estatus: 'Manual', dias_mora: 0 });
  const [uploadFile, setUploadFile]     = useState(null);
  const [uploading, setUploading]       = useState(false);
  const [uploadResult, setUploadResult] = useState(null); // { ok, msg }

  useEffect(() => {
    const peticiones = [
      api.get('/api/v1/llamadas'),
      api.get('/api/v1/dashboard'),
    ];
    if (esAdmin) peticiones.push(api.get('/api/v1/metricas/precision'));

    Promise.all(peticiones)
      .then(([resLlamadas, resDash, resPrecision]) => {
        setLlamadas(resLlamadas.data.data || []);
        setKpis(resDash.data);
        if (resPrecision) setPrecision(resPrecision.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredLlamadas = llamadas.filter((item) => {
    const matchesSearch =
      item.id_llamada.toString().includes(searchTerm) ||
      item.empresa.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEmpresa = filterEmpresa ? item.empresa === filterEmpresa : true;
    const fecha = String(item.fecha_llamada).substring(0, 10);
    const matchesDesde = fechaDesde ? fecha >= fechaDesde : true;
    const matchesHasta = fechaHasta ? fecha <= fechaHasta : true;
    return matchesSearch && matchesEmpresa && matchesDesde && matchesHasta;
  });

  // HU18: KPIs recalculados desde las llamadas filtradas
  const hayFiltros = searchTerm || filterEmpresa || fechaDesde || fechaHasta;
  const kpisVivos = (() => {
    if (!hayFiltros && kpis) return kpis; // sin filtros → usar datos del backend
    const total     = filteredLlamadas.length;
    const auditadas = filteredLlamadas.filter(l => l.resultados_ia.estatus_ia !== 'Pendiente').length;
    const puntajes  = filteredLlamadas.map(l => l.resultados_ia.puntaje).filter(p => p > 0);
    const promedio  = puntajes.length ? (puntajes.reduce((a, b) => a + b, 0) / puntajes.length) : 0;
    const dist      = {};
    filteredLlamadas.forEach(l => {
      const e = l.resultados_ia.estatus_ia || 'Pendiente';
      dist[e] = (dist[e] || 0) + 1;
    });
    return {
      kpis_globales: {
        total_llamadas_recibidas: total,
        total_llamadas_auditadas: auditadas,
        cobertura_porcentaje: total > 0 ? +((auditadas / total) * 100).toFixed(1) : 0,
        calidad_promedio: +promedio.toFixed(2),
      },
      distribucion_estatus: dist,
    };
  })();

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

  // ── HU20: Exportación (sin librerías externas) ───────────────────────────────
  const HEADERS = ['ID', 'Empresa', 'Fecha', 'Días Mora', 'Estatus Original', 'Estatus IA', 'Puntaje', 'Error Crítico'];

  const filaCSV = (ll) => [
    `#${ll.id_llamada}`,
    ll.empresa,
    String(ll.fecha_llamada).substring(0, 10),
    ll.dias_mora,
    ll.estatus_original,
    ll.resultados_ia.estatus_ia,
    `${ll.resultados_ia.puntaje} pts`,
    ll.resultados_ia.error_critico ? 'Sí' : 'No',
  ].map(v => `"${String(v).replace(/"/g, '""')}"`).join(',');

  const exportarExcel = () => {
    const csv = [
      '﻿' + HEADERS.join(','),   // BOM para que Excel abra en UTF-8
      ...filteredLlamadas.map(filaCSV),
    ].join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `auditoria_qa_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportarPDF = () => {
    const fecha = new Date().toLocaleString('es-CL');
    const filas = filteredLlamadas.map(ll => `
      <tr>
        <td>#${ll.id_llamada}</td>
        <td>${ll.empresa}</td>
        <td>${String(ll.fecha_llamada).substring(0, 10)}</td>
        <td>${ll.dias_mora}d</td>
        <td>${ll.estatus_original}</td>
        <td>${ll.resultados_ia.estatus_ia}</td>
        <td>${ll.resultados_ia.puntaje} pts</td>
        <td style="${ll.resultados_ia.error_critico ? 'color:#dc2626;font-weight:bold' : ''}">${ll.resultados_ia.error_critico ? '⚠ Sí' : 'No'}</td>
      </tr>`).join('');

    const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
      <title>Reporte QA</title>
      <style>
        body { font-family: Arial, sans-serif; font-size: 11px; margin: 20px; }
        h2   { color: #1e40af; margin-bottom: 4px; }
        p    { color: #6b7280; margin: 0 0 12px; }
        table{ width: 100%; border-collapse: collapse; }
        th   { background: #1d4ed8; color: white; padding: 6px 8px; text-align: left; font-size: 10px; }
        td   { padding: 5px 8px; border-bottom: 1px solid #e5e7eb; }
        tr:nth-child(even) td { background: #f8fafc; }
      </style></head><body>
      <h2>Reporte de Auditorías QA — Colektia</h2>
      <p>Generado: ${fecha} | Total: ${filteredLlamadas.length} llamadas</p>
      <table><thead><tr>${HEADERS.map(h => `<th>${h}</th>`).join('')}</tr></thead>
      <tbody>${filas}</tbody></table>
      <script>window.onload = () => { window.print(); }<\/script>
      </body></html>`;

    const win = window.open('', '_blank');
    win.document.write(html);
    win.document.close();
  };

  // ── HU08: Carga manual ───────────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!uploadForm.empresa.trim()) { setUploadResult({ ok: false, msg: 'Ingresa el nombre de la empresa.' }); return; }
    if (!uploadFile)                { setUploadResult({ ok: false, msg: 'Selecciona un archivo .txt.' }); return; }
    setUploading(true);
    setUploadResult(null);
    try {
      const fd = new FormData();
      fd.append('empresa',   uploadForm.empresa);
      fd.append('call_id',   uploadForm.call_id);
      fd.append('estatus',   uploadForm.estatus);
      fd.append('dias_mora', uploadForm.dias_mora);
      fd.append('archivo',   uploadFile);
      const res = await api.post('/api/v1/llamadas/carga-manual', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadResult({ ok: true, msg: `✓ Llamada #${res.data.id_interno} encolada correctamente (${res.data.caracteres} caracteres).` });
      setUploadFile(null);
      setUploadForm({ empresa: '', call_id: '', estatus: 'Manual', dias_mora: 0 });
      // Refrescar listado
      api.get('/api/v1/llamadas').then(r => setLlamadas(r.data.data || []));
    } catch (e) {
      setUploadResult({ ok: false, msg: e.response?.data?.detail || 'Error al cargar el archivo.' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Panel de Auditorias</h1>
        <div className="flex items-center gap-2">
          {/* HU08: Carga manual */}
          {['admin', 'analista_qa'].includes(userActual?.rol) && (
            <button
              onClick={() => { setShowUpload(true); setUploadResult(null); }}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
              Cargar transcripción
            </button>
          )}
          {/* HU20: Botones de exportación */}
          <button
            onClick={exportarExcel}
            disabled={filteredLlamadas.length === 0}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Excel
          </button>
          <button
            onClick={exportarPDF}
            disabled={filteredLlamadas.length === 0}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
          >
            <FileText className="w-4 h-4" />
            PDF
          </button>
        </div>
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

      {/* HU18: Panel de filtros dinámicos */}
      <div className="mb-4 bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Desde</label>
            <input
              type="date"
              value={fechaDesde}
              onChange={e => setFechaDesde(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Hasta</label>
            <input
              type="date"
              value={fechaHasta}
              onChange={e => setFechaHasta(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Empresa</label>
            <select
              value={filterEmpresa}
              onChange={e => setFilterEmpresa(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">Todas las empresas</option>
              {uniqueEmpresas.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          {hayFiltros && (
            <button
              onClick={() => { setFechaDesde(''); setFechaHasta(''); setFilterEmpresa(''); setSearchTerm(''); }}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 pb-1"
            >
              <X className="w-3 h-3" /> Limpiar filtros
            </button>
          )}
          {hayFiltros && (
            <span className="text-xs text-gray-400 pb-1 ml-auto">
              Mostrando {filteredLlamadas.length} de {llamadas.length} llamadas
            </span>
          )}
        </div>
      </div>

      {kpisVivos && (
        <>
          {/* KPI CARDS - HU17 + HU18 (reactivos a filtros) */}
          <div className="grid grid-cols-2 gap-4 mb-4 sm:grid-cols-4">
            {[
              { label: 'Llamadas Recibidas',  value: kpisVivos.kpis_globales.total_llamadas_recibidas,  icon: <Phone className="w-6 h-6 text-blue-500" />,   bg: 'bg-blue-50 border-blue-100' },
              { label: 'Llamadas Auditadas',  value: kpisVivos.kpis_globales.total_llamadas_auditadas,  icon: <ShieldCheck className="w-6 h-6 text-green-500" />, bg: 'bg-green-50 border-green-100' },
              { label: 'Cobertura SLA',       value: kpisVivos.kpis_globales.cobertura_porcentaje + '%',icon: <BarChart2 className="w-6 h-6 text-purple-500" />, bg: 'bg-purple-50 border-purple-100' },
              { label: 'Calidad Promedio',    value: kpisVivos.kpis_globales.calidad_promedio + ' pts', icon: <Star className="w-6 h-6 text-yellow-500" />,  bg: 'bg-yellow-50 border-yellow-100' },
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

          {/* HU24: Métrica de precisión de IA — solo admin */}
          {esAdmin && precision && (
            <div className={`mb-4 rounded-xl border p-4 shadow-sm flex items-center gap-5 ${
              precision.accuracy_porcentaje === null
                ? 'bg-gray-50 border-gray-200'
                : precision.cumple_meta
                  ? 'bg-green-50 border-green-200'
                  : precision.accuracy_porcentaje >= 70
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-red-50 border-red-200'
            }`}>
              <BrainCircuit className={`w-8 h-8 flex-shrink-0 ${
                precision.accuracy_porcentaje === null ? 'text-gray-400'
                  : precision.cumple_meta ? 'text-green-600'
                  : precision.accuracy_porcentaje >= 70 ? 'text-yellow-600'
                  : 'text-red-600'
              }`} />
              <div className="flex-1">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-0.5">
                  Precisión de la IA — Métrica HU24
                </p>
                <div className="flex items-baseline gap-3 flex-wrap">
                  <span className="text-3xl font-bold text-gray-900">
                    {precision.accuracy_porcentaje !== null ? `${precision.accuracy_porcentaje}%` : 'Sin datos'}
                  </span>
                  <span className="text-sm text-gray-500">
                    meta: ≥ {precision.meta_porcentaje}%
                    {precision.cumple_meta
                      ? <span className="ml-2 text-green-600 font-semibold">✓ Cumple</span>
                      : precision.accuracy_porcentaje !== null
                        ? <span className="ml-2 text-red-600 font-semibold">✗ No cumple</span>
                        : null
                    }
                  </span>
                </div>
              </div>
              <div className="text-right text-xs text-gray-500 space-y-0.5 flex-shrink-0">
                <div><span className="font-semibold text-gray-700">{precision.revisadas_por_humano}</span> revisadas</div>
                <div><span className="font-semibold text-green-600">{precision.aprobadas_por_humano}</span> aprobadas</div>
                <div><span className="font-semibold text-red-600">{precision.rechazadas_por_humano}</span> rechazadas</div>
                <div><span className="font-semibold text-gray-400">{precision.pendientes_revision}</span> pendientes</div>
              </div>
            </div>
          )}

          {/* DISTRIBUCION ESTATUS */}
          {Object.keys(kpisVivos.distribucion_estatus || {}).length > 0 && (
            <div className="mb-6 bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Distribucion por Estatus IA {hayFiltros && <span className="text-blue-400">(filtrado)</span>}
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(kpisVivos.distribucion_estatus).map(([estatus, cantidad]) => (
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
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="relative max-w-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm"
              placeholder="Buscar por ID o empresa..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
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

      {/* HU08: Modal de carga manual de transcripción */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-600" />
                Cargar transcripción manual
              </h2>
              <button onClick={() => { setShowUpload(false); setUploadResult(null); }} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Empresa *</label>
                <input
                  type="text"
                  value={uploadForm.empresa}
                  onChange={e => setUploadForm({ ...uploadForm, empresa: e.target.value })}
                  placeholder="Ej: Sistecredito"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Call ID (opcional)</label>
                  <input
                    type="text"
                    value={uploadForm.call_id}
                    onChange={e => setUploadForm({ ...uploadForm, call_id: e.target.value })}
                    placeholder="Auto-generado si vacío"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Días de mora</label>
                  <input
                    type="number"
                    min="0"
                    value={uploadForm.dias_mora}
                    onChange={e => setUploadForm({ ...uploadForm, dias_mora: parseInt(e.target.value) || 0 })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Archivo .txt *</label>
                <div className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${uploadFile ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-300'}`}>
                  <input
                    type="file"
                    accept=".txt,.text"
                    className="hidden"
                    id="file-upload"
                    onChange={e => setUploadFile(e.target.files[0] || null)}
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    {uploadFile ? (
                      <span className="text-sm text-blue-700 font-medium">📄 {uploadFile.name}</span>
                    ) : (
                      <span className="text-sm text-gray-500">Haz clic para seleccionar un archivo .txt</span>
                    )}
                  </label>
                </div>
              </div>
            </div>

            {uploadResult && (
              <div className={`mt-3 text-sm px-3 py-2 rounded-lg font-medium ${uploadResult.ok ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                {uploadResult.msg}
              </div>
            )}

            <div className="flex gap-3 mt-5">
              <button
                onClick={() => { setShowUpload(false); setUploadResult(null); }}
                className="flex-1 border border-gray-300 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                Cerrar
              </button>
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
              >
                <Upload className="w-4 h-4" />
                {uploading ? 'Cargando...' : 'Cargar y encolar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
