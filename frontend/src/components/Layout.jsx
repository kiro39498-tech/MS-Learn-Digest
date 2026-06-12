import { Outlet, Link, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Home, Settings, Users, LogOut, BookOpen, Loader2, FlaskConical, GraduationCap } from 'lucide-react';
import clsx from 'clsx';

export default function Layout() {
  const { user, logout, loading } = useAuth();
  const location = useLocation();

  // Wait for auth state to be resolved before making any routing decision
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ms-light">
        <Loader2 className="h-10 w-10 text-ms-blue animate-spin" />
      </div>
    );
  }

  // Only redirect to home once we know for certain there is no authenticated user
  if (!user) {
    return <Navigate to="/" replace />;
  }

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Preferences', path: '/preferences', icon: Settings },
    { name: 'Learning Center', path: '/learning', icon: GraduationCap },
    { name: 'Teams', path: '/teams', icon: Users },
    { name: 'Admin Testing', path: '/admin/testing', icon: FlaskConical },
  ];

  return (
    <div className="min-h-screen flex bg-ms-gray">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <BookOpen className="h-6 w-6 text-ms-blue" />
          <span className="ml-2 font-semibold text-lg">MS Learn Digest</span>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={clsx(
                  'flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors',
                  isActive 
                    ? 'bg-blue-50 text-ms-blue' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-ms-dark'
                )}
              >
                <Icon className={clsx("mr-3 h-5 w-5", isActive ? "text-ms-blue" : "text-gray-400")} />
                {item.name}
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center">
            <img src={user.avatar_url} alt="Avatar" className="h-9 w-9 rounded-full" />
            <div className="ml-3">
              <p className="text-sm font-medium text-ms-dark">{user.name}</p>
            </div>
          </div>
          <button 
            onClick={logout}
            className="mt-4 flex items-center text-sm font-medium text-gray-500 hover:text-gray-700 w-full"
          >
            <LogOut className="mr-2 h-4 w-4" /> Sign out
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6 md:hidden">
          <BookOpen className="h-6 w-6 text-ms-blue" />
          <span className="ml-2 font-semibold">MS Learn Digest</span>
        </header>
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
