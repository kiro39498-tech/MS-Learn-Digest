import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Check, Loader2, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getTopicTree, completeOnboarding, updatePreferences } from '../services/api';
import TopicCardGrid from '../components/TopicCardGrid';
import clsx from 'clsx';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const DELIVERY_TIMES = ['06:00', '07:00', '08:00', '09:00', '10:00', '12:00', '17:00'];

export default function Onboarding() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [tree, setTree] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);

  const [frequency, setFrequency] = useState('weekly');
  const [deliveryDay, setDeliveryDay] = useState(0);
  const [deliveryTime, setDeliveryTime] = useState('08:00');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getTopicTree()
      .then(r => setTree(r.data))
      .catch(() => {})
      .finally(() => setTopicsLoading(false));
  }, []);

  const toggleTopic = (id) => {
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const handleFinish = async () => {
    if (selectedTopics.length === 0) return;
    setLoading(true);
    try {
      await updatePreferences({
        frequency,
        delivery_day: deliveryDay,
        delivery_time: `${deliveryTime}:00`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
      });
      await completeOnboarding(selectedTopics);
      await refreshUser();
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('Onboarding failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ms-light flex flex-col">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center">
        <BookOpen className="h-6 w-6 text-ms-blue mr-2" />
        <span className="font-semibold text-ms-dark">MS Learn Digest</span>
        <div className="ml-auto text-sm text-gray-500">Step {step} of 2</div>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-200">
        <div className="h-1 bg-ms-blue transition-all duration-500"
          style={{ width: `${(step / 2) * 100}%` }} />
      </div>

      <div className="flex-1 flex items-start justify-center py-10 px-4">
        <div className="w-full max-w-5xl">

          {/* ── Step 1: Topics ── */}
          {step === 1 && (
            <div>
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-ms-dark mb-2">
                  What do you want to learn?
                </h1>
                <p className="text-gray-500">
                  Pick the Microsoft technology areas you want to follow. Select a top-level topic
                  to receive everything under it, or expand any card to pick specific subtopics.
                </p>
              </div>

              {topicsLoading ? (
                <div className="flex justify-center py-20">
                  <Loader2 className="h-8 w-8 text-ms-blue animate-spin" />
                </div>
              ) : (
                <TopicCardGrid
                  tree={tree}
                  selected={selectedTopics}
                  onToggle={toggleTopic}
                />
              )}

              <div className="flex justify-between items-center mt-8 pt-4 border-t bg-ms-light sticky bottom-0 py-4">
                <span className="text-sm text-gray-500">
                  {selectedTopics.length} topic{selectedTopics.length !== 1 ? 's' : ''} selected
                </span>
                <button
                  onClick={() => setStep(2)}
                  disabled={selectedTopics.length === 0}
                  className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next: Schedule <ChevronRight className="ml-1 h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── Step 2: Schedule ── */}
          {step === 2 && (
            <div className="max-w-2xl mx-auto">
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-ms-dark mb-2">
                  When should we deliver?
                </h1>
                <p className="text-gray-500">
                  Configure your digest schedule. We'll send your personalised
                  learning updates at these times.
                </p>
              </div>

              <div className="card space-y-6 mb-8">
                {/* Frequency */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Frequency</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {['daily', 'weekly', 'biweekly', 'monthly'].map(f => (
                      <button key={f} onClick={() => setFrequency(f)}
                        className={clsx('py-2.5 px-3 rounded-lg border-2 text-sm font-medium capitalize transition-all',
                          frequency === f ? 'border-ms-blue bg-blue-50 text-ms-blue' : 'border-gray-200 text-gray-600 hover:border-gray-300')}>
                        {f}
                      </button>
                    ))}
                  </div>
                </div>

                {frequency !== 'daily' && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Day of Week</label>
                    <div className="flex flex-wrap gap-2">
                      {DAYS.map((day, idx) => (
                        <button key={idx} onClick={() => setDeliveryDay(idx)}
                          className={clsx('px-3 py-2 rounded-lg border-2 text-sm font-medium transition-all',
                            deliveryDay === idx ? 'border-ms-blue bg-blue-50 text-ms-blue' : 'border-gray-200 text-gray-600 hover:border-gray-300')}>
                          {day.slice(0, 3)}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Delivery Time</label>
                  <div className="flex flex-wrap gap-2">
                    {DELIVERY_TIMES.map(t => {
                      const hour = parseInt(t.split(':')[0], 10);
                      const label = hour === 12 ? '12:00 PM' : hour < 12 ? `${hour}:00 AM` : `${hour - 12}:00 PM`;
                      return (
                        <button key={t} onClick={() => setDeliveryTime(t)}
                          className={clsx('px-3 py-2 rounded-lg border-2 text-sm font-medium transition-all',
                            deliveryTime === t ? 'border-ms-blue bg-blue-50 text-ms-blue' : 'border-gray-200 text-gray-600 hover:border-gray-300')}>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="mb-6 p-4 bg-blue-50 rounded-xl border border-blue-100">
                <p className="text-sm text-ms-blue font-semibold">
                  ✅ {selectedTopics.length} topic{selectedTopics.length !== 1 ? 's' : ''} selected
                </p>
                <p className="text-xs text-blue-500 mt-1">
                  You can change your topic selections any time in Preferences.
                </p>
              </div>

              <div className="flex justify-between">
                <button onClick={() => setStep(1)} className="btn-secondary">Back</button>
                <button onClick={handleFinish} disabled={loading}
                  className="btn-primary flex items-center disabled:opacity-50">
                  {loading
                    ? <><Loader2 className="animate-spin h-4 w-4 mr-2" />Setting up…</>
                    : <><Check className="h-4 w-4 mr-2" />Complete Setup</>}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
