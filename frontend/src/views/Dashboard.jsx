import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { Search, AlertCircle, CheckCircle2, BarChart2, Phone, ShieldCheck, Star, X, FileSpreadsheet, FileText } from 'lucide-react';

export default function Dashboard() {
  const [llamadas, setLlamadas]   = useState([]);
  const [kpis, setKpis]           = useState(null);
  const [loading, setLoading]       = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEmpresa, setFilterEmpresa] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
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

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Panel de Auditorias</h1>
        {/* HU20: Botones de exportación */}
        <div className="flex items-center gap-2">
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
    </div>
  );
}
