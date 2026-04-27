import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { LayoutDashboard, Settings } from 'lucide-react';

import Dashboard from './views/Dashboard';
import CallDetail from './views/CallDetail';

// Placeholder components
const ConfigPanel = () => <div className="p-6"><h1 className="text-2xl font-bold">Configuración</h1></div>;

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200">
          <div className="p-6">
            <h1 className="text-xl font-bold text-blue-600 tracking-tight">QA Inteligente</h1>
          </div>
          <nav className="mt-6 px-4 space-y-2">
            <Link to="/" className="flex items-center px-4 py-3 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
              <LayoutDashboard className="w-5 h-5 mr-3" />
              Auditorías
            </Link>
            <Link to="/settings" className="flex items-center px-4 py-3 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
              <Settings className="w-5 h-5 mr-3" />
              Configuración
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/llamada/:id" element={<CallDetail />} />
            <Route path="/settings" element={<ConfigPanel />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
