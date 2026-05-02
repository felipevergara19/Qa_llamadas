import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { ShieldCheck, LogIn } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // OAuth2PasswordRequestForm requiere form-urlencoded, no JSON
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const res = await api.post('/api/v1/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      localStorage.setItem('qa_token', res.data.access_token);
      localStorage.setItem('qa_user', JSON.stringify({
        nombre: res.data.nombre,
        rol: res.data.rol,
        cliente_id: res.data.cliente_id,
      }));

      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-800 to-blue-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">

        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mb-3">
            <ShieldCheck className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">QA Inteligente</h1>
          <p className="text-sm text-gray-500 mt-1">Plataforma de Auditoria de Llamadas</p>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="usuario@colektia.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2.5 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors"
          >
            <LogIn className="w-4 h-4" />
            {loading ? 'Iniciando sesion...' : 'Iniciar sesion'}
          </button>
        </form>

        {/* Roles badge */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center mb-3">Roles del sistema</p>
          <div className="flex flex-wrap gap-1.5 justify-center">
            {['Admin', 'Analista QA', 'KAM', 'Cliente'].map(r => (
              <span key={r} className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">{r}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
