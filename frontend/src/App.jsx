import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Settings, LogOut, UserCircle, Users } from 'lucide-react';

import Dashboard    from './views/Dashboard';
import CallDetail   from './views/CallDetail';
import SettingsView from './views/Settings';
import UsersView    from './views/Users';
import Login        from './views/Login';

// HU01: Guard — redirige a /login si no hay token
function PrivateRoute({ children }) {
  const token = localStorage.getItem('qa_token');
  return token ? children : <Navigate to="/login" replace />;
}

function AppLayout() {
  const location = useLocation();
  const userRaw  = localStorage.getItem('qa_user');
  const user     = userRaw ? JSON.parse(userRaw) : null;

  const handleLogout = () => {
    localStorage.removeItem('qa_token');
    localStorage.removeItem('qa_user');
    window.location.href = '/login';
  };

  const roleBadgeColor = {
    admin:        'bg-purple-100 text-purple-800',
    analista_qa:  'bg-blue-100 text-blue-800',
    kam:          'bg-green-100 text-green-800',
    cliente:      'bg-yellow-100 text-yellow-800',
  }[user?.rol] || 'bg-gray-100 text-gray-700';

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-blue-600 tracking-tight">QA Inteligente</h1>
          <p className="text-xs text-gray-400 mt-0.5">Colektia</p>
        </div>

        <nav className="mt-4 px-4 space-y-1 flex-1">
          <Link
            to="/"
            className={`flex items-center px-4 py-3 rounded-lg transition-colors ${location.pathname === '/' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <LayoutDashboard className="w-5 h-5 mr-3" />
            Auditorias
          </Link>

          {/* HU03: Solo Admin ve el panel de usuarios */}
          {user?.rol === 'admin' && (
            <Link
              to="/usuarios"
              className={`flex items-center px-4 py-3 rounded-lg transition-colors ${location.pathname === '/usuarios' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <Users className="w-5 h-5 mr-3" />
              Usuarios
            </Link>
          )}

          {/* Configuracion: solo Admin y Analista QA */}
          {['admin', 'analista_qa'].includes(user?.rol) && (
            <Link
              to="/settings"
              className={`flex items-center px-4 py-3 rounded-lg transition-colors ${location.pathname === '/settings' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <Settings className="w-5 h-5 mr-3" />
              Configuracion
            </Link>
          )}
        </nav>

        {/* HU01: Info usuario + logout */}
        {user && (
          <div className="p-4 border-t border-gray-100">
            <div className="flex items-center gap-2 mb-2">
              <UserCircle className="w-8 h-8 text-gray-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{user.nombre}</p>
                <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${roleBadgeColor}`}>
                  {user.rol}
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Cerrar sesion
            </button>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/"            element={<Dashboard />} />
          <Route path="/llamada/:id" element={<CallDetail />} />
          <Route path="/settings"    element={<SettingsView />} />
          <Route path="/usuarios"    element={<UsersView />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <AppLayout />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
