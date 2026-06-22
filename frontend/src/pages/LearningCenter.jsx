/**
 * Learning Center — Professional Learning Platform
 * Shows phases, streaks, milestones, skill levels, analytics dashboard
 */
import { useState, useEffect, useCallback } from 'react';
import {
  BookOpen, GraduationCap, Play, Check, Trophy, Flame,
  ChevronDown, ChevronUp, Loader2, XCircle, CheckCircle2,
  Target, Clock, BookMarked, BarChart2, AlertTriangle, RefreshCw,
  Star, Zap, Award, TrendingUp, Layers,
} from 'lucide-react';
import {
  getLearningTopics, getMyLearningTracks,
  subscribeToLearningTrack, unsubscribeFromLearningTrack,
  updateLearningFrequency, getLearningTopicModules,
  getLearningTopicPhases, updateLearningPhases,
} from '../services/api';
import api from '../services/api';
import PhaseSelector from '../components/PhaseSelector';
import clsx from 'clsx';
import { Settings } from 'lucide-react';

// ── Constants ─────────────────────────────────────────────────────────────────

const FREQ_OPTIONS = [
  { value: 'daily',    label: 'Daily',     desc: 'One lesson/day' },
  { value: 'weekly',   label: 'Weekly',    desc: 'One lesson/week' },
  { value: 'biweekly', label: 'Bi-weekly', desc: 'Every two weeks' },
];

const SKILL_COLORS = {
  beginner:     'bg-green-100 text-green-700 border-green-200',
  intermediate: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  advanced:     'bg-red-100 text-red-700 border-red-200',
  expert:       'bg-purple-100 text-purple-700 border-purple-200',
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function ProgressBar({ pct, status, height = 'h-2' }) {
  const color = status === 'completed' ? 'bg-green-500' : 'bg-ms-blue';
  return (
    <div className={`${height} bg-gray-200 rounded-full overflow-hidden`}>
      <div className={clsx(height, 'rounded-full transition-all duration-700', color)}
        style={{ width: `${pct}%` }} />
    </div>
  );
}

function SkillBadge({ level }) {
  return (
    <span className={clsx(
      'text-xs font-semibold px-2 py-0.5 rounded-full border',
      SKILL_COLORS[level] || 'bg-gray-100 text-gray-600 border-gray-200',
    )}>
      {level?.charAt(0).toUpperCase() + level?.slice(1)}
    </span>
  );
}

function FrequencyPicker({ value, onChange, disabled }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {FREQ_OPTIONS.map((opt) => (
        <button key={opt.value} type="button" disabled={disabled} onClick={() => onChange(opt.value)}
          title={opt.desc}
          className={clsx('px-3 py-1.5 rounded-lg border text-xs font-medium transition-all',
            value === opt.value ? 'border-ms-blue bg-blue-50 text-ms-blue' : 'border-gray-200 text-gray-600 hover:border-gray-300',
            disabled && 'opacity-50 cursor-not-allowed',
          )}>
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ── Analytics Widget ──────────────────────────────────────────────────────────

function AnalyticsDashboard({ analytics }) {
  if (!analytics) return null;
  const metrics = [
    { label: 'Lessons This Month', value: analytics.lessons_last_30_days, icon: BookOpen, color: 'text-ms-blue' },
    { label: 'Total Lessons',      value: analytics.total_lessons_sent,   icon: TrendingUp, color: 'text-green-600' },
    { label: 'Milestones Hit',     value: analytics.milestones_completed, icon: Award, color: 'text-yellow-500' },
    { label: 'Best Streak',        value: `${analytics.longest_streak_days}d`, icon: Flame, color: 'text-orange-500' },
  ];
  return (
    <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100">
      <h3 className="text-sm font-bold text-ms-dark mb-3 flex items-center gap-2">
        <BarChart2 className="h-4 w-4 text-ms-blue" /> Your Learning Analytics
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {metrics.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl p-3 text-center shadow-sm border border-blue-100">
            <Icon className={clsx('h-5 w-5 mx-auto mb-1', color)} />
            <p className="text-xl font-bold text-ms-dark">{value}</p>
            <p className="text-xs text-gray-500 mt-0.5 leading-tight">{label}</p>
          </div>
        ))}
      </div>
      {analytics.current_streak_days > 1 && (
        <div className="mt-3 flex items-center gap-2 text-sm font-semibold text-orange-600">
          <Flame className="h-4 w-4" /> {analytics.current_streak_days}-day streak! Keep it going 🔥
        </div>
      )}
    </div>
  );
}

// ── Active Track Card ─────────────────────────────────────────────────────────

function ActiveTrackCard({ progress, onUnsubscribe, onFrequencyChange, onPhasesChange }) {
  const [showCurriculum, setShowCurriculum] = useState(false);
  const [showPhaseEditor, setShowPhaseEditor] = useState(false);
  const [modules, setModules] = useState([]);
  const [phases, setPhases] = useState([]);
  const [loadingMods, setLoadingMods] = useState(false);
  const [loadingPhases, setLoadingPhases] = useState(false);
  const [freq, setFreq] = useState(progress.frequency);
  const [updatingFreq, setUpdatingFreq] = useState(false);

  const handleToggleCurriculum = async () => {
    if (!showCurriculum && modules.length === 0) {
      setLoadingMods(true);
      try { const r = await getLearningTopicModules(progress.topic_id); setModules(r.data); }
      catch (_) {}
      setLoadingMods(false);
    }
    setShowCurriculum(v => !v);
  };

  const handleFreqChange = async (f) => {
    setFreq(f); setUpdatingFreq(true);
    try { await onFrequencyChange(progress.topic_id, f); } finally { setUpdatingFreq(false); }
  };

  const handleOpenPhaseEditor = async () => {
    if (phases.length === 0) {
      setLoadingPhases(true);
      try {
        const r = await getLearningTopicPhases(progress.topic_id);
        setPhases(r.data.phases || []);
      } catch (_) {}
      setLoadingPhases(false);
    }
    setShowPhaseEditor(true);
  };

  const handlePhaseConfirm = async ({ isFullTrack, selectedPhases, frequency }) => {
    await onPhasesChange(progress.topic_id, isFullTrack, selectedPhases, frequency);
    setShowPhaseEditor(false);
    // Reset modules so the curriculum refreshes next time it opens
    setModules([]);
    setFreq(frequency);
  };

  // Group modules by phase for curriculum view
  const phaseGroups = modules.reduce((acc, mod) => {
    const p = mod.phase_name || 'General';
    if (!acc[p]) acc[p] = [];
    acc[p].push(mod);
    return acc;
  }, {});

  const isMilestone = modules.find(m => m.sequence_number === progress.current_module_sequence)?.is_milestone;
  const isCustomPhases = !progress.is_full_track && progress.selected_phases?.length > 0;

  return (
    <>
      {/* Phase editor modal — reuse PhaseSelector */}
      {showPhaseEditor && (
        <PhaseSelector
          topic={{ id: progress.topic_id, name: progress.topic_name, icon: progress.topic_icon }}
          phases={phases}
          onConfirm={handlePhaseConfirm}
          onClose={() => setShowPhaseEditor(false)}
          initialFreq={freq}
          initialMode={progress.is_full_track ? 'full' : 'custom'}
          initialSelected={progress.selected_phases || []}
        />
      )}

      <div className={clsx('card border-2 transition-colors', isMilestone ? 'border-yellow-300 bg-yellow-50/30' : 'border-gray-200')}>
        {isMilestone && (
          <div className="flex items-center gap-2 text-xs font-bold text-yellow-700 bg-yellow-100 rounded-lg px-3 py-1.5 mb-3">
            <Trophy className="h-3.5 w-3.5" /> Next up: Milestone Project!
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{progress.topic_icon || '📚'}</span>
            <div>
              <h3 className="font-bold text-ms-dark">{progress.topic_name}</h3>
              {progress.current_phase_name && (
                <p className="text-xs text-ms-blue font-medium mt-0.5">{progress.current_phase_name}</p>
              )}
              <p className="text-xs text-gray-500 mt-0.5">
                Module {progress.current_module_sequence}/{progress.total_modules}
                {' · '}{progress.modules_remaining} remaining
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <SkillBadge level={progress.skill_level || 'beginner'} />
            {progress.current_streak_days > 0 && (
              <span className="text-xs font-semibold text-orange-500 flex items-center gap-0.5">
                <Flame className="h-3 w-3" /> {progress.current_streak_days}d streak
              </span>
            )}
          </div>
        </div>

        {/* Phase subscription badge */}
        {isCustomPhases ? (
          <div className="mt-2 flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-lg px-3 py-1.5">
            <Layers className="h-3.5 w-3.5 text-ms-blue shrink-0" />
            <span className="text-xs font-semibold text-ms-blue flex-1">
              Selected phases: {progress.selected_phases.length}
              {' — '}{progress.selected_phases.slice(0,2).join(', ')}
              {progress.selected_phases.length > 2 && ` +${progress.selected_phases.length - 2} more`}
            </span>
            {progress.status !== 'completed' && (
              <button
                onClick={handleOpenPhaseEditor}
                disabled={loadingPhases}
                className="text-xs text-ms-blue hover:text-blue-700 font-medium flex items-center gap-1 shrink-0"
              >
                {loadingPhases
                  ? <Loader2 className="h-3 w-3 animate-spin" />
                  : <Settings className="h-3 w-3" />}
                Edit
              </button>
            )}
          </div>
        ) : (
          progress.status !== 'completed' && (
            <div className="mt-2 flex items-center gap-2 bg-gray-50 border border-gray-100 rounded-lg px-3 py-1.5">
              <Layers className="h-3.5 w-3.5 text-gray-400 shrink-0" />
              <span className="text-xs text-gray-500 flex-1">Full track — all phases</span>
              <button
                onClick={handleOpenPhaseEditor}
                disabled={loadingPhases}
                className="text-xs text-ms-blue hover:text-blue-700 font-medium flex items-center gap-1 shrink-0"
              >
                {loadingPhases
                  ? <Loader2 className="h-3 w-3 animate-spin" />
                  : <Settings className="h-3 w-3" />}
                Edit phases
              </button>
            </div>
          )
        )}

        {/* Progress */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span className="font-semibold">{progress.progress_pct}%</span>
          </div>
          <ProgressBar pct={progress.progress_pct} status={progress.status} />
        </div>

        {/* Stats row */}
        <div className="mt-3 grid grid-cols-3 gap-2 text-center">
          <div className="bg-gray-50 rounded-lg p-2 border">
            <p className="text-xs text-gray-500">Completed</p>
            <p className="text-sm font-bold text-ms-dark">{progress.modules_completed}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 border">
            <p className="text-xs text-gray-500">Total Sent</p>
            <p className="text-sm font-bold text-ms-dark">{progress.total_lessons_sent || 0}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 border">
            <p className="text-xs text-gray-500">Best Streak</p>
            <p className="text-sm font-bold text-orange-500">{progress.longest_streak_days || 0}d</p>
          </div>
        </div>

        {/* Frequency */}
        {progress.status !== 'completed' && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2 font-medium">Delivery frequency</p>
            <FrequencyPicker value={freq} onChange={handleFreqChange} disabled={updatingFreq} />
          </div>
        )}

        {progress.last_sent_at && (
          <p className="text-xs text-gray-400 mt-3">
            Last lesson: {new Date(progress.last_sent_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </p>
        )}

        {/* Actions */}
        <div className="mt-4 flex items-center gap-3 flex-wrap">
          <button onClick={handleToggleCurriculum} className="btn-secondary text-xs flex items-center gap-1">
            {loadingMods ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
              : showCurriculum ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {showCurriculum ? 'Hide' : 'View'} Curriculum
          </button>
          <button onClick={() => onUnsubscribe(progress.topic_id)}
            className="text-xs text-red-400 hover:text-red-600 transition-colors">
            Unsubscribe
          </button>
        </div>

        {/* Phase-grouped curriculum */}
        {showCurriculum && modules.length > 0 && (
          <div className="mt-4 border-t pt-4 max-h-72 overflow-y-auto space-y-3">
            {Object.entries(phaseGroups).map(([phaseName, phaseMods]) => (
              <div key={phaseName}>
                <p className="text-xs font-bold text-ms-blue uppercase tracking-wide mb-1.5">{phaseName}</p>
                <div className="space-y-1">
                  {phaseMods.map((mod) => {
                    const done    = mod.sequence_number < progress.current_module_sequence;
                    const current = mod.sequence_number === progress.current_module_sequence;
                    return (
                      <div key={mod.id} className={clsx(
                        'flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs',
                        mod.is_milestone && done    ? 'bg-yellow-50 border border-yellow-200' :
                        mod.is_milestone && current ? 'bg-yellow-100 border border-yellow-300 font-bold' :
                        done    ? 'bg-green-50 text-green-700' :
                        current ? 'bg-blue-50 text-ms-blue font-semibold border border-blue-200' : 'text-gray-400',
                      )}>
                        <span className="text-gray-300 font-mono w-5 shrink-0">{String(mod.sequence_number).padStart(2,'0')}</span>
                        {mod.is_milestone && <Trophy className="h-3 w-3 text-yellow-500 shrink-0" />}
                        <span className="flex-1 truncate">{mod.title}</span>
                        {done    && <Check className="h-3.5 w-3.5 text-green-500 shrink-0" />}
                        {current && <Play  className="h-3.5 w-3.5 text-ms-blue shrink-0" />}
                        <SkillBadge level={mod.skill_level || mod.difficulty_level} />
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

// ── Browse Topic Card ─────────────────────────────────────────────────────────

function TopicCard({ topic, onSubscribe }) {
  const [showSelector, setShowSelector] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [modules, setModules] = useState([]);
  const [phases, setPhases] = useState([]);
  const [loadingMods, setLoadingMods] = useState(false);

  const handlePreview = async () => {
    if (!showPreview && modules.length === 0) {
      setLoadingMods(true);
      try {
        const [modRes, phaseRes] = await Promise.all([
          getLearningTopicModules(topic.id),
          getLearningTopicPhases(topic.id),
        ]);
        setModules(modRes.data);
        setPhases(phaseRes.data.phases || []);
      } catch (_) {}
      setLoadingMods(false);
    }
    setShowPreview(v => !v);
  };

  const handleOpenSelector = async () => {
    // Load phases if not already loaded
    if (phases.length === 0) {
      setLoadingMods(true);
      try {
        const phaseRes = await getLearningTopicPhases(topic.id);
        setPhases(phaseRes.data.phases || []);
      } catch (_) {}
      setLoadingMods(false);
    }
    setShowSelector(true);
  };

  const handleConfirm = async ({ isFullTrack, selectedPhases, frequency }) => {
    await onSubscribe(topic.id, frequency, isFullTrack, selectedPhases);
    setShowSelector(false);
  };

  const phaseCount = phases.length || new Set(modules.map(m => m.phase_name)).size;
  const milestoneCount = modules.filter(m => m.is_milestone).length;

  return (
    <>
      {showSelector && (
        <PhaseSelector
          topic={topic}
          phases={phases}
          onConfirm={handleConfirm}
          onClose={() => setShowSelector(false)}
        />
      )}

      <div className="card border border-gray-200 hover:border-ms-blue hover:shadow-md transition-all flex flex-col">
        {/* Topic header */}
        <div className="flex items-start gap-3">
          <span className="text-3xl shrink-0">{topic.icon || '📚'}</span>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-ms-dark">{topic.name}</h3>
            {topic.description && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{topic.description}</p>
            )}
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400 flex-wrap">
              <span className="flex items-center gap-1">
                <BookMarked className="h-3.5 w-3.5" />{topic.total_modules} lessons
              </span>
              {topic.estimated_hours && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />~{topic.estimated_hours}h
                </span>
              )}
              {topic.difficulty_range && (
                <span className="flex items-center gap-1">
                  <Target className="h-3.5 w-3.5" />{topic.difficulty_range}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Curriculum preview */}
        <div className="mt-3">
          <button type="button" onClick={handlePreview}
            className="text-xs text-ms-blue hover:underline flex items-center gap-1">
            {loadingMods ? <Loader2 className="h-3 w-3 animate-spin" />
              : showPreview ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {showPreview ? 'Hide' : 'Preview'} curriculum
          </button>

          {showPreview && (
            <div className="mt-2">
              <div className="flex gap-2 mb-2 text-xs text-gray-500">
                {phaseCount > 0 && (
                  <span className="bg-gray-100 px-2 py-0.5 rounded-full">{phaseCount} phases</span>
                )}
                {milestoneCount > 0 && (
                  <span className="bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded-full border border-yellow-200">
                    🏆 {milestoneCount} milestones
                  </span>
                )}
              </div>
              {phases.length > 0 ? (
                <div className="bg-gray-50 rounded-lg p-3 max-h-44 overflow-y-auto space-y-1.5">
                  {phases.map(p => (
                    <div key={p.phase_name} className="flex items-center justify-between text-xs py-1 border-b border-gray-100 last:border-0">
                      <span className="text-ms-dark font-medium truncate flex-1 mr-2">{p.phase_name}</span>
                      <span className="text-gray-400 shrink-0">{p.module_count} lessons</span>
                    </div>
                  ))}
                </div>
              ) : modules.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-3 max-h-44 overflow-y-auto">
                  {modules.slice(0, 8).map(mod => (
                    <div key={mod.id} className="flex items-center gap-2 text-xs text-gray-600 py-0.5">
                      <span className="font-mono text-gray-300 w-5">{String(mod.sequence_number).padStart(2,'0')}</span>
                      <span className="flex-1 truncate">{mod.title}</span>
                    </div>
                  ))}
                  {modules.length > 8 && (
                    <p className="text-xs text-gray-400 mt-1 text-center">+{modules.length - 8} more</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Enroll button */}
        <button
          onClick={handleOpenSelector}
          disabled={loadingMods}
          className="mt-auto w-full btn-primary flex items-center justify-center gap-2 text-sm disabled:opacity-50 mt-4"
        >
          {loadingMods
            ? <><Loader2 className="h-4 w-4 animate-spin" />Loading…</>
            : <><Play className="h-4 w-4" />Enrol in Track</>}
        </button>
      </div>
    </>
  );
}

// ── Setup Banner ──────────────────────────────────────────────────────────────

function SetupBanner({ onSeed, seeding }) {
  return (
    <div className="card border-2 border-yellow-300 bg-yellow-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-6 w-6 text-yellow-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-yellow-800">Learning Engine — Setup Required</h3>
          <p className="text-sm text-yellow-700 mt-1">
            The learning curriculum hasn't been seeded. Apply the migration then click below.
          </p>
          <div className="mt-2 text-xs text-yellow-700 font-mono bg-yellow-100 rounded-lg p-3">
            alembic upgrade head
          </div>
          <button onClick={onSeed} disabled={seeding}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium rounded-lg disabled:opacity-50">
            {seeding ? <><Loader2 className="h-4 w-4 animate-spin" />Seeding…</>
              : <><RefreshCw className="h-4 w-4" />Seed Curriculum</>}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function LearningCenter() {
  const [topics,    setTopics]    = useState([]);
  const [myTracks,  setMyTracks]  = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [setupNeeded, setSetupNeeded] = useState(false);
  const [seeding,   setSeeding]   = useState(false);
  const [tab, setTab] = useState('browse');
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const loadData = useCallback(async () => {
    try {
      const [topicsRes, myRes] = await Promise.all([
        getLearningTopics().catch(() => ({ data: [] })),
        getMyLearningTracks().catch(() => ({ data: [] })),
      ]);
      const topicList = topicsRes.data || [];
      const trackList = myRes.data || [];
      setTopics(topicList);
      setMyTracks(trackList);
      setSetupNeeded(topicList.length === 0);

      // Load analytics separately — don't block on failure
      if (trackList.length > 0) {
        api.get('/api/learning/analytics')
          .then(r => setAnalytics(r.data))
          .catch(() => {});
      }
    } catch (err) {
      console.error(err);
      setSetupNeeded(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const r = await api.post('/api/learning/seed');
      if (r.data.total_topics > 0) {
        showToast(`Seeded ${r.data.total_topics} learning topics!`);
        setSetupNeeded(false);
        await loadData();
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Seed failed — run alembic upgrade head first.', 'error');
    } finally {
      setSeeding(false);
    }
  };

  const subscribedIds = new Set(myTracks.map(t => String(t.topic_id)));
  const availableTopics = topics.filter(t => !subscribedIds.has(String(t.id)));
  const activeTracks    = myTracks.filter(t => t.status === 'active');
  const completedTracks = myTracks.filter(t => t.status === 'completed');

  const handleSubscribe = async (topicId, frequency, isFullTrack = true, selectedPhases = []) => {
    try {
      await subscribeToLearningTrack(topicId, frequency, isFullTrack, selectedPhases);
      const modeLabel = isFullTrack ? 'Full track' : `${selectedPhases.length} phase${selectedPhases.length !== 1 ? 's' : ''}`;
      showToast(`Enrolled! ${modeLabel} — first lesson arrives at the scheduled time.`);
      await loadData();
      setTab('active');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to subscribe', 'error');
    }
  };

  const handleUnsubscribe = async (topicId) => {
    if (!window.confirm('Unsubscribe? Your progress will be lost.')) return;
    try {
      await unsubscribeFromLearningTrack(topicId);
      showToast('Unsubscribed from track.');
      await loadData();
    } catch (err) {
      showToast('Failed to unsubscribe', 'error');
    }
  };

  const handleFrequencyChange = async (topicId, frequency) => {
    try {
      await updateLearningFrequency(topicId, frequency);
      showToast('Delivery frequency updated.');
      await loadData();
    } catch (err) {
      showToast('Failed to update frequency', 'error');
    }
  };

  const handlePhasesChange = async (topicId, isFullTrack, selectedPhases, frequency) => {
    try {
      // Update phases first
      await updateLearningPhases(topicId, isFullTrack, selectedPhases);
      // Update frequency if it changed
      await updateLearningFrequency(topicId, frequency);
      const modeLabel = isFullTrack ? 'Full track' : `${selectedPhases.length} phase${selectedPhases.length !== 1 ? 's' : ''}`;
      showToast(`Updated: ${modeLabel}`);
      await loadData();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update phases', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 text-ms-blue animate-spin" />
      </div>
    );
  }

  const TAB_DEFS = [
    { key: 'browse',    label: 'Browse Tracks',  count: availableTopics.length },
    { key: 'active',    label: 'My Learning',     count: activeTracks.length },
    { key: 'completed', label: 'Completed',       count: completedTracks.length },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">

      {/* Toast */}
      {toast && (
        <div className={clsx(
          'fixed top-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2',
          toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-green-600 text-white',
        )}>
          {toast.type === 'error' ? <XCircle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
          {toast.msg}
        </div>
      )}

      {/* Page header */}
      <div className="flex items-start gap-4">
        <div className="bg-ms-blue rounded-xl p-3">
          <GraduationCap className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ms-dark">Learning Center</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Professional learning tracks — Beginner to Expert. Phased curriculum, milestone projects,
            interview prep, and AI-generated lessons delivered to your inbox.
          </p>
        </div>
      </div>

      {/* Setup banner */}
      {setupNeeded && <SetupBanner onSeed={handleSeed} seeding={seeding} />}

      {!setupNeeded && topics.length > 0 && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold text-ms-blue">{activeTracks.length}</p>
              <p className="text-xs text-gray-500 mt-1">Active Tracks</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-green-600">{completedTracks.length}</p>
              <p className="text-xs text-gray-500 mt-1">Completed</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-purple-600">{topics.length}</p>
              <p className="text-xs text-gray-500 mt-1">Tracks Available</p>
            </div>
          </div>

          {/* Analytics dashboard — only when user has tracks */}
          {analytics && myTracks.length > 0 && (
            <AnalyticsDashboard analytics={analytics} />
          )}

          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
            {TAB_DEFS.map(({ key, label, count }) => (
              <button key={key} onClick={() => setTab(key)}
                className={clsx('px-4 py-2 rounded-md text-sm font-medium transition-all',
                  tab === key ? 'bg-white text-ms-blue shadow-sm' : 'text-gray-600 hover:text-gray-800')}>
                {label}
                {count > 0 && (
                  <span className={clsx('ml-2 text-xs px-1.5 py-0.5 rounded-full',
                    tab === key ? 'bg-blue-100 text-ms-blue' : 'bg-gray-200 text-gray-500')}>
                    {count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* ── Browse tab ── */}
          {tab === 'browse' && (
            <div>
              {availableTopics.length === 0 && myTracks.length > 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Trophy className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">You're enrolled in all available tracks!</p>
                  <button onClick={() => setTab('active')} className="btn-primary mt-4 text-sm">
                    View My Tracks →
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {availableTopics.map(t => (
                    <TopicCard key={t.id} topic={t} onSubscribe={handleSubscribe} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── My Learning tab ── */}
          {tab === 'active' && (
            <div className="space-y-4">
              {activeTracks.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">No active tracks yet</p>
                  <button onClick={() => setTab('browse')} className="btn-primary mt-4 text-sm">
                    Browse Tracks →
                  </button>
                </div>
              ) : (
                activeTracks.map(track => (
                  <ActiveTrackCard key={track.topic_id} progress={track}
                    onUnsubscribe={handleUnsubscribe}
                    onFrequencyChange={handleFrequencyChange}
                    onPhasesChange={handlePhasesChange}
                  />
                ))
              )}
            </div>
          )}

          {/* ── Completed tab ── */}
          {tab === 'completed' && (
            <div className="space-y-4">
              {completedTracks.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Trophy className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">No completed tracks yet — keep going!</p>
                </div>
              ) : (
                completedTracks.map(track => (
                  <div key={track.topic_id}
                    className="card border-2 border-green-200 bg-green-50">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{track.topic_icon || '📚'}</span>
                      <div className="flex-1">
                        <h3 className="font-bold text-ms-dark">{track.topic_name}</h3>
                        <p className="text-xs text-green-700 mt-0.5">
                          ✅ {track.total_modules} modules completed
                          {track.completed_at && (
                            <> · {new Date(track.completed_at).toLocaleDateString('en-US',
                              { month: 'short', day: 'numeric', year: 'numeric' })}</>
                          )}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Best streak: {track.longest_streak_days || 0}d
                          {' · '}{track.total_lessons_sent || 0} lessons received
                        </p>
                      </div>
                      <Trophy className="h-8 w-8 text-yellow-500 shrink-0" />
                    </div>
                    <div className="mt-3">
                      <ProgressBar pct={100} status="completed" height="h-2" />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
