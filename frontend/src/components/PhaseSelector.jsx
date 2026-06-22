/**
 * PhaseSelector — Phase-based learning track enrollment modal/panel.
 *
 * Props:
 *   topic          LearningTopicResponse
 *   phases         [{phase_name, phase_number, module_count, difficulty_levels}]
 *   onConfirm      ({isFullTrack, selectedPhases, frequency}) => void
 *   onClose        () => void
 *   initialFreq    string
 */
import { useState } from 'react';
import { Check, X, Trophy, Clock, ChevronRight, Loader2, Layers } from 'lucide-react';
import clsx from 'clsx';

const FREQ_OPTIONS = [
  { value: 'daily',    label: 'Daily',     desc: 'One lesson per day' },
  { value: 'weekly',   label: 'Weekly',    desc: 'One lesson per week' },
  { value: 'biweekly', label: 'Bi-weekly', desc: 'Every two weeks' },
];

const DIFF_COLORS = {
  beginner:     'bg-green-100 text-green-700',
  intermediate: 'bg-yellow-100 text-yellow-700',
  advanced:     'bg-red-100 text-red-700',
  expert:       'bg-purple-100 text-purple-700',
};

export default function PhaseSelector({ topic, phases = [], onConfirm, onClose, initialFreq = 'weekly', initialMode = 'full', initialSelected = [] }) {
  const [mode, setMode] = useState(initialMode);          // 'full' | 'custom'
  const [selected, setSelected] = useState(initialSelected);      // selected phase_names
  const [freq, setFreq] = useState(initialFreq);
  const [confirming, setConfirming] = useState(false);

  const togglePhase = (phaseName) => {
    setSelected(prev =>
      prev.includes(phaseName) ? prev.filter(p => p !== phaseName) : [...prev, phaseName]
    );
  };

  const selectAll = () => setSelected(phases.map(p => p.phase_name));
  const clearAll  = () => setSelected([]);

  const handleConfirm = async () => {
    if (mode === 'custom' && selected.length === 0) return;
    setConfirming(true);
    try {
      await onConfirm({
        isFullTrack: mode === 'full',
        selectedPhases: mode === 'full' ? [] : selected,
        frequency: freq,
      });
    } finally {
      setConfirming(false);
    }
  };

  const totalModules = mode === 'full'
    ? phases.reduce((s, p) => s + p.module_count, 0)
    : phases.filter(p => selected.includes(p.phase_name))
        .reduce((s, p) => s + p.module_count, 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="bg-gradient-to-r from-ms-blue to-blue-700 rounded-t-2xl px-6 py-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/75 text-xs font-semibold uppercase tracking-wide mb-1">
                {topic.icon} {topic.name}
              </p>
              <h2 className="text-white text-xl font-bold">Customise Your Track</h2>
              <p className="text-white/80 text-sm mt-1">
                Choose to receive all phases or only the ones you need.
              </p>
            </div>
            <button onClick={onClose}
              className="text-white/70 hover:text-white transition-colors p-1">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="px-6 py-5 space-y-5">

          {/* Mode toggle */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setMode('full')}
              className={clsx(
                'flex flex-col items-center p-4 rounded-xl border-2 text-left transition-all',
                mode === 'full'
                  ? 'border-ms-blue bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300',
              )}
            >
              <Layers className={clsx('h-6 w-6 mb-2', mode === 'full' ? 'text-ms-blue' : 'text-gray-400')} />
              <span className={clsx('text-sm font-bold', mode === 'full' ? 'text-ms-blue' : 'text-ms-dark')}>
                Full Track
              </span>
              <span className="text-xs text-gray-500 mt-1 text-center leading-tight">
                All {phases.length} phases<br/>{phases.reduce((s,p) => s+p.module_count,0)} lessons
              </span>
              {mode === 'full' && (
                <span className="mt-2 text-xs bg-ms-blue text-white px-2 py-0.5 rounded-full">Selected</span>
              )}
            </button>

            <button
              onClick={() => setMode('custom')}
              className={clsx(
                'flex flex-col items-center p-4 rounded-xl border-2 text-left transition-all',
                mode === 'custom'
                  ? 'border-ms-blue bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300',
              )}
            >
              <Check className={clsx('h-6 w-6 mb-2', mode === 'custom' ? 'text-ms-blue' : 'text-gray-400')} />
              <span className={clsx('text-sm font-bold', mode === 'custom' ? 'text-ms-blue' : 'text-ms-dark')}>
                Select Phases
              </span>
              <span className="text-xs text-gray-500 mt-1 text-center leading-tight">
                Only phases you need
              </span>
              {mode === 'custom' && (
                <span className="mt-2 text-xs bg-ms-blue text-white px-2 py-0.5 rounded-full">Selected</span>
              )}
            </button>
          </div>

          {/* Phase cards — shown in custom mode */}
          {mode === 'custom' && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold text-ms-dark">
                  Choose phases ({selected.length} of {phases.length} selected)
                </p>
                <div className="flex gap-2 text-xs">
                  <button onClick={selectAll} className="text-ms-blue hover:underline">All</button>
                  <span className="text-gray-300">|</span>
                  <button onClick={clearAll} className="text-gray-400 hover:text-red-500">None</button>
                </div>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {phases.map(phase => {
                  const isSelected = selected.includes(phase.phase_name);
                  const primaryDiff = phase.difficulty_levels?.[0] || 'beginner';
                  return (
                    <button
                      key={phase.phase_name}
                      onClick={() => togglePhase(phase.phase_name)}
                      className={clsx(
                        'w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 text-left transition-all',
                        isSelected
                          ? 'border-ms-blue bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white',
                      )}
                    >
                      <div className={clsx(
                        'w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all',
                        isSelected ? 'bg-ms-blue border-ms-blue' : 'border-gray-300',
                      )}>
                        {isSelected && <Check className="h-3 w-3 text-white" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={clsx('text-sm font-semibold truncate',
                          isSelected ? 'text-ms-blue' : 'text-ms-dark')}>
                          {phase.phase_name}
                        </p>
                        <p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                          <Clock className="h-3 w-3" />
                          {phase.module_count} lesson{phase.module_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <span className={clsx(
                        'text-xs font-semibold px-2 py-0.5 rounded-full shrink-0',
                        DIFF_COLORS[primaryDiff] || 'bg-gray-100 text-gray-500',
                      )}>
                        {primaryDiff}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Frequency */}
          <div>
            <p className="text-sm font-semibold text-ms-dark mb-2">Delivery Frequency</p>
            <div className="grid grid-cols-3 gap-2">
              {FREQ_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setFreq(opt.value)}
                  className={clsx(
                    'py-2 px-3 rounded-xl border-2 text-xs font-semibold transition-all text-center',
                    freq === opt.value
                      ? 'border-ms-blue bg-blue-50 text-ms-blue'
                      : 'border-gray-200 text-gray-600 hover:border-gray-300',
                  )}
                >
                  <span className="block">{opt.label}</span>
                  <span className="block font-normal text-gray-400 mt-0.5 text-xs">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Summary */}
          {totalModules > 0 && (
            <div className="bg-blue-50 rounded-xl px-4 py-3 border border-blue-100">
              <p className="text-sm text-ms-blue font-semibold">
                {mode === 'full' ? 'Full Track' : `${selected.length} phase${selected.length !== 1 ? 's' : ''}`}
                {' — '}{totalModules} lesson{totalModules !== 1 ? 's' : ''}
              </p>
              <p className="text-xs text-blue-500 mt-0.5">
                Delivered {FREQ_OPTIONS.find(f => f.value === freq)?.desc?.toLowerCase()}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button onClick={onClose}
              className="flex-1 btn-secondary text-sm">
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={confirming || (mode === 'custom' && selected.length === 0)}
              className="flex-1 btn-primary flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              {confirming
                ? <><Loader2 className="h-4 w-4 animate-spin" />Enrolling…</>
                : <><ChevronRight className="h-4 w-4" />Start Learning</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
