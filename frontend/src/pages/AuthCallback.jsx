import { useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { exchangeGoogleCode } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const called = useRef(false); // guard against React StrictMode double-invoke

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const code = searchParams.get('code');
    if (!code) {
      navigate('/', { replace: true });
      return;
    }

    exchangeGoogleCode(code, `${window.location.origin}/auth/callback`)
      .then((response) => {
        // login() stores token, fetches /api/users/me, sets user, then navigates
        login(response.data.access_token);
      })
      .catch((error) => {
        console.error('OAuth exchange failed:', error);
        navigate('/', { replace: true });
      });
  }, [searchParams, navigate, login]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-ms-light">
      <div className="text-center">
        <Loader2 className="h-10 w-10 text-ms-blue animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-ms-dark">Authenticating...</h2>
        <p className="text-gray-500 mt-2">Please wait while we log you in.</p>
      </div>
    </div>
  );
}
