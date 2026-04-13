import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/profile', label: 'Profile', icon: '👤' },
  { to: '/resumes', label: 'Resumes', icon: '📄' },
  { to: '/jobs', label: 'Jobs', icon: '💼' },
  { to: '/sources', label: 'Sources', icon: '🔗' },
  { to: '/applications', label: 'Apps', icon: '📋' },
];

export default function Navbar() {
  const location = useLocation();
  const { logout } = useAuth();

  return (
    <nav className="bg-gray-900 text-white">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold">JobCodex</Link>
          <div className="flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`px-3 py-2 rounded-md text-sm flex items-center gap-1 ${
                  location.pathname === item.to
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <span>{item.icon}</span>
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            ))}
            <button
              onClick={logout}
              className="ml-2 px-3 py-2 text-sm text-gray-300 hover:text-white"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
