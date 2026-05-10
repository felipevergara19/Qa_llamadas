/**
 * Users.jsx — HU03: Administración de usuarios (solo Admin)
 * Permite listar, crear, editar y desactivar usuarios.
 */
import { useEffect, useState } from 'react';
import { UserPlus, Pencil, UserX, UserCheck, X, Save } from 'lucide-react';
import api from '../api';

const ROLES = ['admin', 'analista_qa', 'kam', 'cliente'];

const roleBadge = {
  admin:       'bg-purple-100 text-purple-800',
  analista_qa: 'bg-blue-100   text-blue-800',
  kam:         'bg-green-100  text-green-800',
  cliente:     'bg-yellow-100 text-yellow-800',
};

const EMPTY_FORM = { nombre: '', email: '', password: '', rol: 'analista_qa', cliente_id: '' };

export default function Users() {
  const [usuarios,  setUsuarios]  = useState([]);
  const [clientes,  setClientes]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editando,  setEditando]  = useState(null);
  const [form,      setForm]      = useState(EMPTY_FORM);
  const [saving,    setSaving]    = useState(false);
  const [feedback,  setFeedback]  = useState('');

  // ── Cargar datos ─────────────────────────────────────────────────────────────
  const fetchData = async () => {
    try {
      setLoading(true);
      const [uRes, cRes] = await Promise.all([
        api.get('/api/v1/usuarios'),
        api.get('/api/v1/clientes'),
      ]);
      setUsuarios(uRes.data);
      setClientes(cRes.data);
    } catch {
      setError('No se pudo cargar la información.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // ── Modal ────────────────────────────────────────────────────────────────────
  const abrirCrear = () => {
    setEditando(null);
    setForm(EMPTY_FORM);
    setFeedback('');
    setShowModal(true);
  };

  const abrirEditar = (u) => {
    setEditando(u);
    setForm({ nombre: u.nombre, email: u.email, password: '', rol: u.rol, cliente_id: u.cliente_id ?? '' });
    setFeedback('');
    setShowModal(true);
  };

  const cerrarModal = () => { setShowModal(false); setFeedback(''); };

  // ── Guardar ──────────────────────────────────────────────────────────────────
  const guardar = async () => {
    if (!form.nombre || !form.email || (!editando && !form.password)) {
      setFeedback('Completa nombre, email y contraseña.');
      return;
    }
    setSaving(true);
    setFeedback('');
    try {
      if (editando) {
        await api.put(`/api/v1/usuarios/${editando.id}`, {
          nombre:     form.nombre,
          rol:        form.rol,
          cliente_id: form.cliente_id || null,
          activo:     editando.activo,
        });
      } else {
        await api.post('/api/v1/usuarios', {
          nombre:     form.nombre,
          email:      form.email,
          password:   form.password,
          rol:        form.rol,
          cliente_id: form.cliente_id || null,
        });
      }
      cerrarModal();
      fetchData();
    } catch (e) {
      setFeedback(e.response?.data?.detail || 'Error al guardar.');
    } finally {
      setSaving(false);
    }
  };

  // ── Activar / Desactivar ─────────────────────────────────────────────────────
  const toggleActivo = async (u) => {
    try {
      if (u.activo) {
        await api.delete(`/api/v1/usuarios/${u.id}`);
      } else {
        await api.put(`/api/v1/usuarios/${u.id}`, {
          nombre: u.nombre, rol: u.rol, cliente_id: u.cliente_id, activo: true,
        });
      }
      fetchData();
    } catch {
      alert('No se pudo cambiar el estado del usuario.');
    }
  };

  const nombreEmpresa = (id) =>
    clientes.find((c) => c.id === id)?.nombre_empresa ?? '—';

  // ── Render ───────────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">Cargando usuarios...</div>
  );
  if (error) return (
    <div className="p-8 text-red-500">{error}</div>
  );

  return (
    <div className="p-6 max-w-6xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Administración de Usuarios</h1>
          <p className="text-sm text-gray-400 mt-0.5">{usuarios.length} usuarios registrados</p>
        </div>
        <button
          onClick={abrirCrear}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <UserPlus className="w-4 h-4" />
          Nuevo usuario
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {['Nombre', 'Email', 'Rol', 'Empresa', 'Estado', 'Acciones'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {usuarios.map((u) => (
              <tr key={u.id} className={`hover:bg-gray-50 transition-colors ${!u.activo ? 'opacity-50' : ''}`}>
                <td className="px-4 py-3 font-medium text-gray-800">{u.nombre}</td>
                <td className="px-4 py-3 text-gray-500">{u.email}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${roleBadge[u.rol]}`}>
                    {u.rol}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{nombreEmpresa(u.cliente_id)}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${u.activo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                    {u.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => abrirEditar(u)}
                      title="Editar"
                      className="p-1.5 rounded hover:bg-blue-50 text-blue-500 transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => toggleActivo(u)}
                      title={u.activo ? 'Desactivar' : 'Reactivar'}
                      className={`p-1.5 rounded transition-colors ${u.activo ? 'hover:bg-red-50 text-red-400' : 'hover:bg-green-50 text-green-500'}`}
                    >
                      {u.activo ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">

            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-gray-800">
                {editando ? 'Editar usuario' : 'Nuevo usuario'}
              </h2>
              <button onClick={cerrarModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Nombre completo</label>
                <input
                  type="text"
                  value={form.nombre}
                  onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Ej: Ana Martínez"
                />
              </div>

              {!editando && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="usuario@empresa.com"
                  />
                </div>
              )}

              {!editando && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Contraseña</label>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="Mínimo 8 caracteres"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Rol</label>
                <select
                  value={form.rol}
                  onChange={(e) => setForm({ ...form, rol: e.target.value, cliente_id: '' })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>

              {['kam', 'cliente'].includes(form.rol) && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Empresa cliente</label>
                  <select
                    value={form.cliente_id}
                    onChange={(e) => setForm({ ...form, cliente_id: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    <option value="">— Sin empresa —</option>
                    {clientes.map((c) => (
                      <option key={c.id} value={c.id}>{c.nombre_empresa}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {feedback && (
              <p className="mt-3 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{feedback}</p>
            )}

            <div className="flex gap-3 mt-6">
              <button
                onClick={cerrarModal}
                className="flex-1 border border-gray-300 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={guardar}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
