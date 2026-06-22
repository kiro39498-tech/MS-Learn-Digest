/**
 * TopicCardGrid — Modern card-based topic selector.
 *
 * Replaces the tree/checkbox view with a Coursera/Microsoft Learn-style
 * card grid that shows:
 *   - Icon + name + short description
 *   - Subtopic count
 *   - Selected state (highlighted border + checkmark)
 *   - Expandable subtopic cards (click parent → show children inline)
 *   - Search + category filter
 *   - "Recommended" section for popular root topics
 *
 * Props
 * ─────
 * tree         TopicNode[]  — nested tree from GET /api/topics/tree
 * selected     string[]     — array of selected topic IDs
 * onToggle     (id) => void — called when a card is selected/deselected
 */

import { useState, useMemo } from 'react';
import { Check, ChevronDown, ChevronUp, Search, X } from 'lucide-react';
import clsx from 'clsx';

// ── Emoji / colour mapping ─────────────────────────────────────────────────────

const TOPIC_ICONS = {
  azure: '☁️', 'azure-fundamentals': '☁️', 'azure-compute': '🖥️',
  'azure-networking': '🌐', 'azure-storage': '💾', 'azure-security': '🛡️',
  'azure-identity': '🔑', 'azure-monitoring': '📊', 'azure-devops': '🔀',
  'azure-data-engineering': '🔧', 'azure-ai': '🧠', 'azure-ai-foundry': '🔬',
  aks: '📦', 'azure-architecture': '🏗️', 'azure-integration': '🔗',
  'azure-iot': '📡',
  fabric: '🗄️', 'fabric-fundamentals': '🗄️', 'fabric-data-engineering': '🔧',
  'fabric-data-science': '🧪', 'fabric-data-warehouse': '🏛️',
  'fabric-real-time': '⚡', 'fabric-power-bi': '📊',
  'fabric-data-factory': '🏭', 'fabric-lakehouse': '🏠',
  'power-platform': '⚡', 'power-apps': '📱', 'power-automate': '🔄',
  'power-bi': '📊', 'power-pages': '🌐', 'copilot-studio': '✨',
  m365: '🏢', 'm365-teams': '👥', 'm365-sharepoint': '📁',
  'm365-exchange': '📧', 'm365-security': '🛡️', 'copilot-m365': '✨',
  security: '🛡️', defender: '🛡️', sentinel: '👁️', 'entra-id': '🔑',
  'security-copilot': '✨',
  github: '🐙', 'github-actions': '🔀', 'github-copilot': '✨',
  'github-security': '🔒',
  'ai-engineering': '🤖', 'generative-ai': '✨', 'responsible-ai': '⚖️',
  devops: '🔀', 'dynamics-365': '💼', 'd365-sales': '📈',
  'd365-finance': '💰', 'd365-supply-chain': '📦',
};

const CARD_COLORS = {
  azure: 'from-blue-500 to-blue-600',
  fabric: 'from-purple-500 to-purple-600',
  'power-platform': 'from-yellow-500 to-orange-500',
  m365: 'from-teal-500 to-teal-600',
  security: 'from-red-500 to-red-600',
  github: 'from-gray-700 to-gray-800',
  'ai-engineering': 'from-violet-500 to-violet-600',
  devops: 'from-green-500 to-green-600',
  'dynamics-365': 'from-indigo-500 to-indigo-600',
};

const RECOMMENDED_SLUGS = ['azure', 'fabric', 'power-platform', 'azure-ai-foundry', 'azure-ai'];

function getIcon(slug) { return TOPIC_ICONS[slug] || '📌'; }
function getGradient(slug) { return CARD_COLORS[slug] || 'from-ms-blue to-blue-700'; }

// ── Subtopic pill card ─────────────────────────────────────────────────────────

function SubtopicPill({ topic, isSelected, onToggle }) {
  return (
    <button
      type="button"
      onClick={() => onToggle(topic.id)}
      className={clsx(
        'flex items-center gap-2 px-3 py-2 rounded-xl border-2 text-left text-sm transition-all w-full',
        isSelected
          ? 'border-ms-blue bg-blue-50 text-ms-blue font-semibold'
          : 'border-gray-200 bg-white text-gray-700 hover:border-ms-blue hover:bg-blue-50/40',
      )}
    >
      <span className="text-base shrink-0">{getIcon(topic.slug)}</span>
      <span className="flex-1 leading-tight">{topic.name}</span>
      {isSelected && (
        <span className="shrink-0 bg-ms-blue rounded-full p-0.5">
          <Check className="h-3 w-3 text-white" />
        </span>
      )}
    </button>
  );
}

// ── Root topic card ────────────────────────────────────────────────────────────

function TopicCard({ topic, selected, onToggle }) {
  const isSelected = selected.includes(topic.id);
  const hasChildren = topic.children && topic.children.length > 0;

  // Auto-expand if any child is selected
  const hasSelectedChild = hasChildren && topic.children.some(c => selected.includes(c.id));
  const [expanded, setExpanded] = useState(hasSelectedChild);

  const selectedChildCount = hasChildren
    ? topic.children.filter(c => selected.includes(c.id)).length
    : 0;

  return (
    <div className={clsx(
      'rounded-2xl border-2 overflow-hidden transition-all duration-200 flex flex-col',
      isSelected
        ? 'border-ms-blue shadow-md shadow-blue-100'
        : selectedChildCount > 0
          ? 'border-blue-300 shadow-sm'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm',
    )}>
      {/* Card header — gradient bar */}
      <div
        className={clsx(
          'bg-gradient-to-r p-4 cursor-pointer select-none',
          getGradient(topic.slug),
        )}
        onClick={() => onToggle(topic.id)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{getIcon(topic.slug)}</span>
            <div>
              <h3 className="text-white font-bold text-base leading-tight">{topic.name}</h3>
              {hasChildren && (
                <p className="text-white/75 text-xs mt-0.5">
                  {topic.children.length} subtopic{topic.children.length !== 1 ? 's' : ''}
                </p>
              )}
            </div>
          </div>
          {/* Selection indicator */}
          <div className={clsx(
            'w-7 h-7 rounded-full border-2 flex items-center justify-center shrink-0 transition-all',
            isSelected
              ? 'bg-white border-white'
              : 'border-white/50 bg-white/10',
          )}>
            {isSelected && (
              <Check className={clsx('h-4 w-4', `text-${topic.slug === 'github' ? 'gray-800' : 'ms-blue'}`)} style={{ color: '#0078d4' }} />
            )}
          </div>
        </div>
      </div>

      {/* Card body */}
      <div className="bg-white p-4 flex-1 flex flex-col">
        {topic.description && (
          <p className="text-xs text-gray-500 leading-relaxed mb-3 line-clamp-2">
            {topic.description}
          </p>
        )}

        {/* Status row */}
        <div className="flex items-center justify-between mb-3">
          {isSelected ? (
            <span className="text-xs font-semibold text-ms-blue bg-blue-50 px-2 py-1 rounded-full">
              ✓ Selected
            </span>
          ) : selectedChildCount > 0 ? (
            <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
              {selectedChildCount} subtopic{selectedChildCount !== 1 ? 's' : ''} selected
            </span>
          ) : (
            <span className="text-xs text-gray-400">Not selected</span>
          )}
        </div>

        {/* Expand subtopics */}
        {hasChildren && (
          <>
            <button
              type="button"
              onClick={() => setExpanded(v => !v)}
              className="flex items-center gap-1.5 text-xs text-ms-blue hover:text-blue-700 font-medium mt-auto transition-colors"
            >
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              {expanded ? 'Hide' : 'Show'} subtopics
            </button>

            {expanded && (
              <div className="mt-3 grid grid-cols-1 gap-1.5 border-t pt-3">
                {topic.children.map(child => (
                  <SubtopicPill
                    key={child.id}
                    topic={child}
                    isSelected={selected.includes(child.id)}
                    onToggle={onToggle}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Main TopicCardGrid export ──────────────────────────────────────────────────

export default function TopicCardGrid({ tree = [], selected = [], onToggle }) {
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');

  // Category filter tabs
  const FILTERS = [
    { key: 'all',      label: 'All Topics' },
    { key: 'cloud',    label: '☁️ Cloud',      slugs: ['azure'] },
    { key: 'data',     label: '🗄️ Data',       slugs: ['fabric', 'power-platform', 'dynamics-365'] },
    { key: 'ai',       label: '🧠 AI',         slugs: ['ai-engineering'] },
    { key: 'security', label: '🛡️ Security',   slugs: ['security'] },
    { key: 'dev',      label: '🔀 DevOps',     slugs: ['github', 'devops'] },
    { key: 'm365',     label: '🏢 M365',       slugs: ['m365'] },
  ];

  // Recommended topics (subset of root topics)
  const recommended = tree.filter(t => RECOMMENDED_SLUGS.includes(t.slug));

  const visibleTopics = useMemo(() => {
    let nodes = tree;

    // Apply category filter
    if (activeFilter !== 'all') {
      const filterDef = FILTERS.find(f => f.key === activeFilter);
      if (filterDef?.slugs) {
        nodes = nodes.filter(t =>
          filterDef.slugs.some(s => t.slug === s || t.slug.startsWith(s + '-'))
        );
      }
    }

    // Apply search
    if (search.trim()) {
      const q = search.toLowerCase();
      nodes = nodes.filter(t =>
        t.name.toLowerCase().includes(q) ||
        (t.description || '').toLowerCase().includes(q) ||
        (t.children || []).some(c =>
          c.name.toLowerCase().includes(q) ||
          (c.description || '').toLowerCase().includes(q)
        )
      );
    }

    return nodes;
  }, [tree, search, activeFilter]);

  const totalSelected = selected.length;
  const isRecommendedSection = activeFilter === 'all' && !search.trim();

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search topics and subtopics…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="input pl-9 pr-9"
        />
        {search && (
          <button onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Category filter chips */}
      <div className="flex gap-2 flex-wrap">
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setActiveFilter(f.key)}
            className={clsx(
              'px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
              activeFilter === f.key
                ? 'bg-ms-blue text-white border-ms-blue'
                : 'bg-white text-gray-600 border-gray-200 hover:border-ms-blue hover:text-ms-blue',
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Selection counter */}
      {totalSelected > 0 && (
        <div className="flex items-center justify-between bg-blue-50 border border-blue-100 rounded-xl px-4 py-2.5">
          <span className="text-sm font-semibold text-ms-blue">
            {totalSelected} topic{totalSelected !== 1 ? 's' : ''} selected
          </span>
          <button onClick={() => selected.forEach(id => onToggle(id))}
            className="text-xs text-gray-400 hover:text-red-500 transition-colors">
            Clear all
          </button>
        </div>
      )}

      {/* Recommended section — only on "All" with no search */}
      {isRecommendedSection && recommended.length > 0 && (
        <div>
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-2">
            ⭐ Recommended Tracks
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
            {recommended.map(topic => (
              <TopicCard
                key={topic.id}
                topic={topic}
                selected={selected}
                onToggle={onToggle}
              />
            ))}
          </div>
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wide mb-3">
            All Topics
          </h3>
        </div>
      )}

      {/* Main grid */}
      {visibleTopics.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {visibleTopics
            .filter(t => !isRecommendedSection || !RECOMMENDED_SLUGS.includes(t.slug))
            .map(topic => (
              <TopicCard
                key={topic.id}
                topic={topic}
                selected={selected}
                onToggle={onToggle}
              />
            ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          <Search className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No topics match "{search}"</p>
          <button onClick={() => setSearch('')}
            className="text-xs text-ms-blue hover:underline mt-1">
            Clear search
          </button>
        </div>
      )}
    </div>
  );
}
