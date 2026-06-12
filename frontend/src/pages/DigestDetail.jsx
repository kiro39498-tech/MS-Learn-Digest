import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, ExternalLink, AlertCircle } from 'lucide-react';
import { getDigest } from '../services/api';

export default function DigestDetail() {
  const { digestId } = useParams();
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDigest(digestId)
      .then((r) => setDigest(r.data))
      .catch((err) => setError(err.response?.data?.detail ?? 'Failed to load digest.'))
      .finally(() => setLoading(false));
  }, [digestId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-ms-blue animate-spin" />
      </div>
    );
  }

  if (error || !digest) {
    return (
      <div className="max-w-3xl mx-auto">
        <Link to="/dashboard" className="flex items-center text-sm text-gray-500 hover:text-ms-blue mb-6">
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard
        </Link>
        <div className="card text-center py-12">
          <AlertCircle className="h-10 w-10 text-red-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-700">{error ?? 'Digest not found'}</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <Link to="/dashboard" className="flex items-center text-sm text-gray-500 hover:text-ms-blue">
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard
      </Link>

      {/* Meta */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-ms-dark">{digest.title}</h1>
            <p className="text-sm text-gray-400 mt-1">
              Generated: {new Date(digest.created_at).toLocaleDateString('en-US', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
              })}
              {digest.sent_at && (
                <> · Sent: {new Date(digest.sent_at).toLocaleDateString()}</>
              )}
            </p>
          </div>
          <span className="text-xs bg-blue-100 text-ms-blue px-2 py-1 rounded-full font-medium capitalize">
            {digest.digest_type}
          </span>
        </div>

        {digest.topic_names?.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {digest.topic_names.map((t) => (
              <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Rendered email HTML */}
      {digest.content_html ? (
        <div className="card p-0 overflow-hidden rounded-xl">
          <iframe
            srcDoc={digest.content_html}
            title="Digest content"
            className="w-full border-0"
            style={{ minHeight: '600px', height: '80vh' }}
            sandbox="allow-same-origin"
          />
        </div>
      ) : (
        <div className="card">
          <h2 className="font-semibold text-ms-dark mb-4">Content Items ({digest.items?.length ?? 0})</h2>
          <div className="space-y-3">
            {(digest.items ?? []).map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-ms-dark">{item.title ?? 'Unknown'}</p>
                  <p className="text-xs text-gray-400 capitalize">{item.section?.replace('_', ' ')}</p>
                </div>
                {item.url && (
                  <a href={item.url} target="_blank" rel="noreferrer" className="text-ms-blue">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
