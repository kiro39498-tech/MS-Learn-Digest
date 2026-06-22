import { useState, useEffect } from 'react';
import { Save, Loader2, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getTopicTree, getMyTopics, subscribeTopics, updatePreferences } from '../services/api';
import TopicCardGrid from '../components/TopicCardGrid';
import clsx from 'clsx';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIMES = [
  '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00',
];

export default function Preferences() {
  const { user, refreshUser } = useAuth();
  const pref = user?.preferences;

  const [tree, setTree] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [treeLoading, setTreeLoading] = useState(true);

  const [frequency, setFrequency] = useState(pref?.frequency ?? 'weekly');
  const [deliveryDay, setDeliveryDay] = useState(pref?.delivery_day ?? 0);
  const [deliveryTime, setDeliveryTime] = useState(() => {
    if (pref?.delivery_time && typeof pref.delivery_time === 'string') {
      return pref.delivery_time.substring(0, 5);
    }
    return '08:00';
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    Promise.all([getTopicTree(), getMyTopics()])
      .then(([treeRes, myRes]) => {
        setTree(treeRes.data);
        setSelectedTopics(myRes.data.map(t => t.id));
      })
      .catch(console.error)
      .finally(() => setTreeLoading(false));
  }, []);

  const toggleTopic = (id) => {
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      if (selectedTopics.length > 0) {
        await subscribeTopics(selectedTopics);
      }
      await updatePreferences({
        frequency,
        delivery_day: deliveryDay,
        delivery_time: `${deliveryTime}:00`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ms-dark">Delivery Preferences</h1>
          <p className="text-gray-500 mt-1">Customize what and when you learn.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving || selectedTopics.length === 0}
          className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving  ? <><Loader2 className="animate-spin h-4 w-4 mr-2" />Saving…</>
          : saved  ? <><Check   className="h-4 w-4 mr-2" />Saved!</>
          :           <><Save   className="h-4 w-4 mr-2" />Save Preferences</>}
        </button>
      </div>

      {/* ── Topics ── */}
      <div className="card">
        <div className="flex items-center justify-between border-b pb-3 mb-5">
          <div>
            <h2 className="text-lg font-semibold">Topics of Interest</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Select top-level topics for everything, or expand cards to pick subtopics.
            </p>
          </div>
          <span className="text-sm text-gray-400 shrink-0">{selectedTopics.length} selected</span>
        </div>

        {treeLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 text-ms-blue animate-spin" />
          </div>
        ) : (
          <TopicCardGrid
            tree={tree}
            selected={selectedTopics}
            onToggle={toggleTopic}
          />
        )}
      </div>

      {/* ── Schedule ── */}
      <div className="card space-y-5">
        <h2 className="text-lg font-semibold border-b pb-3">Delivery Schedule</h2>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Frequency</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {['daily', 'weekly', 'biweekly', 'monthly'].map(f => (
              <button key={f} onClick={() => setFrequency(f)}
                className={clsx('py-2 px-3 rounded-lg border-2 text-sm font-medium capitalize transition-all',
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
          <label className="block text-sm font-semibold text-gray-700 mb-2">Delivery Time (local time)</label>
          <select className="input max-w-xs" value={deliveryTime} onChange={e => setDeliveryTime(e.target.value)}>
            {TIMES.map(t => {
              const hour = parseInt(t.split(':')[0], 10);
              const label = hour === 12 ? '12:00 PM' : hour < 12 ? `${hour}:00 AM` : `${hour - 12}:00 PM`;
              return <option key={t} value={t}>{label}</option>;
            })}
          </select>
        </div>
      </div>

      <div className="flex justify-end">
        <button onClick={handleSave} disabled={saving || selectedTopics.length === 0}
          className="btn-primary flex items-center disabled:opacity-50">
          {saving  ? <><Loader2 className="animate-spin h-4 w-4 mr-2" />Saving…</>
          : saved  ? <><Check   className="h-4 w-4 mr-2" />Saved!</>
          :           <><Save   className="h-4 w-4 mr-2" />Save Preferences</>}
        </button>
      </div>
    </div>
  );
}
