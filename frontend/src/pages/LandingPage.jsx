import { Link, Navigate } from 'react-router-dom';
import { BookOpen, Zap, Mail, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
  const { user, loading } = useAuth();

  // Don't render or redirect until auth state is known
  if (loading) return null;

  // Already authenticated — send straight to the app
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleGoogleLogin = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      throw new Error("Google Client ID is missing. Please check your environment variables.");
    }
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
    const scope = encodeURIComponent('openid email profile');
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=${scope}`;
    window.location.href = authUrl;
  };

  return (
    <div className="min-h-screen bg-ms-light">
      <nav className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <BookOpen className="h-8 w-8 text-ms-blue" />
              <span className="ml-2 text-xl font-semibold text-ms-dark">MS Learn Digest</span>
            </div>
            <div className="flex items-center space-x-4">
              <button onClick={handleGoogleLogin} className="btn-secondary">Log in</button>
              <button onClick={handleGoogleLogin} className="btn-primary">Get Started</button>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl tracking-tight font-extrabold text-ms-dark sm:text-5xl md:text-6xl">
            <span className="block">Transform Microsoft Learn into an</span>
            <span className="block text-ms-blue">Active Knowledge Engine</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Stop searching for updates. Let AI monitor the MS Learn Catalog, extract what matters, and deliver personalized digests directly to you and your team.
          </p>
          <div className="mt-10 max-w-sm mx-auto sm:max-w-none sm:flex sm:justify-center">
            <button onClick={handleGoogleLogin} className="btn-primary flex items-center justify-center text-lg px-8 py-3">
              <Zap className="mr-2 h-5 w-5" /> Start Learning Smarter
            </button>
          </div>
        </div>

        <div className="bg-ms-gray py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
              <div className="card text-center hover:-translate-y-1 transition-transform">
                <div className="flex justify-center mb-4"><Zap className="h-10 w-10 text-ms-blue" /></div>
                <h3 className="text-lg font-semibold">AI Enriched Insights</h3>
                <p className="mt-2 text-sm text-gray-600">Groq-powered summaries highlighting the business value and key takeaways of new modules.</p>
              </div>
              <div className="card text-center hover:-translate-y-1 transition-transform">
                <div className="flex justify-center mb-4"><Mail className="h-10 w-10 text-ms-blue" /></div>
                <h3 className="text-lg font-semibold">Automated Digests</h3>
                <p className="mt-2 text-sm text-gray-600">Receive beautifully formatted HTML emails containing your personalized learning path updates.</p>
              </div>
              <div className="card text-center hover:-translate-y-1 transition-transform">
                <div className="flex justify-center mb-4"><Users className="h-10 w-10 text-ms-blue" /></div>
                <h3 className="text-lg font-semibold">Team Knowledge</h3>
                <p className="mt-2 text-sm text-gray-600">Create newsletters for your entire organization and ensure everyone stays aligned on tech.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
