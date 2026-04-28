import { useState, useEffect } from 'react';
import api from '../api';
import { Save, Plus, Trash2, Edit3, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('prompt');
  
  // -- PROMPT STATE --
  const [promptText, setPromptText] = useState('');
  const [promptLoading, setPromptLoading] = useState(false);
  const [promptSuccess, setPromptSuccess] = useState(false);

  // -- RUBRICAS STATE --
  const [rubricas, setRubricas] = useState([]);
  const [rubricasLoading, setRubricasLoading] = useState(false);
  
  // -- FORM NUEVA RÚBRICA --
  const [showForm, setShowForm] = useState(false);
  const [newRubrica, setNewRubrica] = useState({
    nombre: '',
    empresa: '',
    puntos: [{ nombre: '', descripcion: '', peso: 1, es_severidad: false }]
  });

  useEffect(() => {
    fetchPrompt();
    fetchRubricas();
  }, []);

  const fetchPrompt = async () => {
    try {
      const res = await api.get('/api/v1/config/prompt');
      setPromptText(res.data.prompt);
    } catch (e) {
      console.error("Error fetching prompt:", e);
    }
  };

  const fetchRubricas = async () => {
    setRubricasLoading(true);
    try {
      const res = await api.get('/api/v1/rubricas');
      setRubricas(res.data);
    } catch (e) {
      console.error("Error fetching rubricas:", e);
    } finally {
      setRubricasLoading(false);
    }
  };

  const savePrompt = async () => {
    setPromptLoading(true);
    try {
      await api.post('/api/v1/config/prompt', { texto: promptText });
      setPromptSuccess(true);
      setTimeout(() => setPromptSuccess(false), 3000);
    } catch (e) {
      console.error("Error saving prompt:", e);
      alert("Error al guardar el prompt");
    } finally {
      setPromptLoading(false);
    }
  };

  const handleAddCriterio = () => {
    setNewRubrica({
      ...newRubrica,
      puntos: [...newRubrica.puntos, { nombre: '', descripcion: '', peso: 1, es_severidad: false }]
    });
  };

  const handleRemoveCriterio = (index) => {
    const updated = [...newRubrica.puntos];
    updated.splice(index, 1);
    setNewRubrica({ ...newRubrica, puntos: updated });
  };

  const handleCriterioChange = (index, field, value) => {
    const updated = [...newRubrica.puntos];
    updated[index][field] = value;
    setNewRubrica({ ...newRubrica, puntos: updated });
  };

  const submitRubrica = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/rubricas', newRubrica);
      setShowForm(false);
      setNewRubrica({ nombre: '', empresa: '', puntos: [{ nombre: '', descripcion: '', peso: 1, es_severidad: false }] });
      fetchRubricas(); // Recargar la lista
    } catch (error) {
      console.error("Error saving rubrica:", error);
      alert("Error al guardar la rúbrica");
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Configuración del Sistema</h1>
      </div>

      {/* TABS */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('prompt')}
            className={`whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'prompt'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tuning de Prompt IA (HU26)
          </button>
          <button
            onClick={() => setActiveTab('rubricas')}
            className={`whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'rubricas'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Gestor de Rúbricas (HU09, HU29)
          </button>
        </nav>
      </div>

      {/* CONTENIDO TABS */}
      {activeTab === 'prompt' && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-gray-800 flex items-center">
              <Edit3 className="w-5 h-5 mr-2 text-blue-500" />
              Prompt Base de Gemini
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Este es el cerebro de la IA. Las variables como {"{llamada_id}"} o {"{guion_dinamico}"} se reemplazarán automáticamente en cada auditoría.
            </p>
          </div>
          
          <textarea
            className="w-full h-96 p-4 border border-gray-300 rounded-lg font-mono text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:bg-white transition-colors"
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
          />

          <div className="mt-4 flex items-center justify-end">
            {promptSuccess && (
              <span className="text-green-600 text-sm font-medium flex items-center mr-4">
                <CheckCircle2 className="w-4 h-4 mr-1" />
                Prompt guardado con éxito
              </span>
            )}
            <button
              onClick={savePrompt}
              disabled={promptLoading}
              className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4 mr-2" />
              {promptLoading ? 'Guardando...' : 'Guardar Cambios'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'rubricas' && (
        <div className="space-y-6">
          {/* HEADER RUBRICAS */}
          <div className="flex justify-between items-center bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div>
              <h2 className="text-lg font-bold text-gray-800">Rúbricas Activas</h2>
              <p className="text-sm text-gray-500">Administra los guiones de evaluación por empresa.</p>
            </div>
            <button 
              onClick={() => setShowForm(!showForm)}
              className="flex items-center bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              {showForm ? 'Cancelar' : 'Nueva Rúbrica'}
            </button>
          </div>

          {/* FORMULARIO NUEVA RUBRICA */}
          {showForm && (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-blue-200 ring-1 ring-blue-100">
              <h3 className="text-lg font-bold text-blue-900 mb-4 border-b pb-2">Crear Nueva Rúbrica</h3>
              <form onSubmit={submitRubrica} className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de la Rúbrica</label>
                    <input 
                      type="text" required
                      className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      placeholder="Ej: Cobranza Temprana - Access"
                      value={newRubrica.nombre}
                      onChange={(e) => setNewRubrica({...newRubrica, nombre: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Empresa (Exacta)</label>
                    <input 
                      type="text" required
                      className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      placeholder="Ej: Access Finance"
                      value={newRubrica.empresa}
                      onChange={(e) => setNewRubrica({...newRubrica, empresa: e.target.value})}
                    />
                  </div>
                </div>

                <div className="mt-6">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="text-md font-semibold text-gray-800">Criterios a Evaluar (Guion)</h4>
                  </div>
                  
                  <div className="space-y-4">
                    {newRubrica.puntos.map((punto, index) => (
                      <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200 relative flex gap-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex gap-4">
                            <div className="flex-1">
                              <label className="block text-xs font-medium text-gray-500 uppercase">Nombre del Paso</label>
                              <input 
                                type="text" required
                                className="mt-1 w-full text-sm border-gray-300 rounded-md shadow-sm"
                                placeholder="Ej: Saludo"
                                value={punto.nombre}
                                onChange={(e) => handleCriterioChange(index, 'nombre', e.target.value)}
                              />
                            </div>
                            <div className="w-24">
                              <label className="block text-xs font-medium text-gray-500 uppercase">Peso (Pts)</label>
                              <input 
                                type="number" min="0" required
                                className="mt-1 w-full text-sm border-gray-300 rounded-md shadow-sm"
                                value={punto.peso}
                                disabled={punto.es_severidad}
                                onChange={(e) => handleCriterioChange(index, 'peso', parseInt(e.target.value))}
                              />
                            </div>
                            <div className="w-32 flex flex-col justify-end pb-2">
                              <label className="flex items-center text-sm text-red-600 font-medium cursor-pointer">
                                <input 
                                  type="checkbox" 
                                  className="rounded border-gray-300 text-red-600 shadow-sm focus:ring-red-500 mr-2"
                                  checked={punto.es_severidad}
                                  onChange={(e) => {
                                    handleCriterioChange(index, 'es_severidad', e.target.checked);
                                    if(e.target.checked) handleCriterioChange(index, 'peso', 0);
                                  }}
                                />
                                Es Severidad
                              </label>
                            </div>
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-500 uppercase">Descripción / Instrucción para la IA</label>
                            <textarea 
                              required rows="2"
                              className="mt-1 w-full text-sm border-gray-300 rounded-md shadow-sm"
                              placeholder="Ej: El agente debe saludar diciendo 'Buenos días'..."
                              value={punto.descripcion}
                              onChange={(e) => handleCriterioChange(index, 'descripcion', e.target.value)}
                            />
                          </div>
                        </div>
                        
                        {/* Botón eliminar */}
                        {newRubrica.puntos.length > 1 && (
                          <button 
                            type="button" 
                            onClick={() => handleRemoveCriterio(index)}
                            className="text-gray-400 hover:text-red-500 transition-colors self-start p-2"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  <button 
                    type="button"
                    onClick={handleAddCriterio}
                    className="mt-4 flex items-center text-sm text-blue-600 font-medium hover:text-blue-800"
                  >
                    <Plus className="w-4 h-4 mr-1" /> Agregar otro paso al guion
                  </button>
                </div>

                <div className="flex justify-end pt-4 border-t border-gray-200">
                  <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium shadow-sm">
                    Guardar Rúbrica
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* LISTA DE RUBRICAS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {rubricasLoading ? (
              <p className="text-gray-500">Cargando rúbricas...</p>
            ) : rubricas.length === 0 ? (
              <p className="text-gray-500 col-span-full">No hay rúbricas creadas aún.</p>
            ) : (
              rubricas.map((r) => (
                <div key={r.id} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-bold text-gray-900">{r.nombre}</h3>
                      <span className="inline-block mt-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-md">
                        {r.empresa}
                      </span>
                    </div>
                    {r.activo ? (
                      <span className="w-3 h-3 bg-green-500 rounded-full" title="Activa"></span>
                    ) : (
                      <span className="w-3 h-3 bg-red-500 rounded-full" title="Inactiva"></span>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Criterios ({r.criterios.length})</h4>
                    <ul className="space-y-2">
                      {r.criterios.map((c, i) => (
                        <li key={i} className="text-sm flex justify-between items-center bg-gray-50 px-2 py-1 rounded">
                          <span className="text-gray-700 truncate mr-2">{c.nombre}</span>
                          {c.es_severidad ? (
                            <ShieldAlert className="w-4 h-4 text-red-500 flex-shrink-0" title="Severidad" />
                          ) : (
                            <span className="text-xs font-bold text-gray-500 bg-gray-200 px-1.5 rounded">{c.peso}p</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
