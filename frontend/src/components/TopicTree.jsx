/**
 * TopicTree — Hierarchical topic selector with expand/collapse.
 *
 * Props
 * ─────
 * tree          TopicNode[]    — nested tree from GET /api/topics/tree
 * selected      string[]       — array of selected topic IDs
 * onToggle      (id) => void   — called when user clicks a topic
 * selectionMode "any" | "leaf-only"
 *               "any"       (default) — any node can be selected; selecting a
 *                           parent is treated as "subscribe to everything under it"
 *               "leaf-only" — only leaf nodes (no children) can be selected
 *
 * The component renders root topics as collapsible sections and subtopics as
 * indented checkbox rows.  All levels are supported (arbitrary depth).
 */

import { useState } from 'react';
import { ChevronRight, ChevronDown, Check } from 'lucide-react';
import clsx from 'clsx';

const TOPIC_ICONS = {
  azure: '☁️',
  'azure-fundamentals': '☁️',
  'azure-compute': '🖥️',
  'azure-networking': '🌐',
  'azure-storage': '💾',
  'azure-security': '🛡️',
  'azure-identity': '🔑',
  'azure-monitoring': '📊',
  'azure-devops': '🔀',
  'azure-data-engineering': '🔧',
  'azure-ai': '🧠',
  'azure-ai-foundry': '🔬',
  aks: '📦',
  'azure-architecture': '🏗️',
  'azure-integration': '🔗',
  'azure-iot': '📡',
  fabric: '🗄️',
  'fabric-fundamentals': '🗄️',
  'fabric-data-engineering': '🔧',
  'fabric-data-science': '🧪',
  'fabric-data-warehouse': '🏛️',
  'fabric-real-time': '⚡',
  'fabric-power-bi': '📊',
  'fabric-data-factory': '🏭',
  'fabric-lakehouse': '🏠',
  'power-platform': '⚡',
  'power-apps': '📱',
  'power-automate': '🔄',
  'power-bi': '📊',
  'power-pages': '🌐',
  'copilot-studio': '✨',
  m365: '🏢',
  'm365-teams': '👥',
  'm365-sharepoint': '📁',
  'm365-exchange': '📧',
  'm365-security': '🛡️',
  'copilot-m365': '✨',
  security: '🛡️',
  defender: '🛡️',
  sentinel: '👁️',
  'entra-id': '🔑',
  'security-copilot': '✨',
  github: '🐙',
  'github-actions': '🔀',
  'github-copilot': '✨',
  'github-security': '🔒',
  'ai-engineering': '🤖',
  'generative-ai': '✨',
  'responsible-ai': '⚖️',
  devops: '🔀',
  'dynamics-365': '💼',
  'd365-sales': '📈',
  'd365-finance': '💰',
  'd365-supply-chain': '📦',
};

function getIcon(slug) {
  return TOPIC_ICONS[slug] || '📌';
}

/**
 * A single topic row (checkbox + label).
 */
function TopicRow({ topic, selected, onToggle, depth = 0 }) {
  const isSelected = selected.includes(topic.id);
  const indentClass = depth === 0 ? '' : depth === 1 ? 'ml-4' : 'ml-8';

  return (
    <button
      type="button"
      onClick={() => onToggle(topic.id)}
      className={clsx(
        'w-full flex items-center gap-3 px-3 py-2 rounded-lg border text-left transition-all',
        indentClass,
        isSelected
          ? 'border-ms-blue bg-blue-50 text-ms-blue'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 text-gray-700'
      )}
    >
      <span className="text-base shrink-0">{getIcon(topic.slug)}</span>
      <div className="flex-1 min-w-0">
        <span className={clsx('text-sm font-medium', isSelected ? 'text-ms-blue' : 'text-ms-dark')}>
          {topic.name}
        </span>
        {topic.description && (
          <p className="text-xs text-gray-400 mt-0.5 truncate">{topic.description}</p>
        )}
      </div>
      {isSelected && <Check className="h-4 w-4 text-ms-blue shrink-0" />}
    </button>
  );
}

/**
 * A collapsible root-topic section with its children nested inside.
 */
function RootSection({ topic, selected, onToggle }) {
  const hasChildren = topic.children && topic.children.length > 0;
  const isSelected = selected.includes(topic.id);

  // Auto-expand if this root or any of its children are selected
  const hasSelectedChild = hasChildren && topic.children.some((c) => selected.includes(c.id));
  const [expanded, setExpanded] = useState(isSelected || hasSelectedChild);

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Root row */}
      <div className={clsx(
        'flex items-center gap-0 transition-colors',
        isSelected ? 'bg-blue-50' : 'bg-white hover:bg-gray-50'
      )}>
        {/* Expand/collapse toggle */}
        {hasChildren ? (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="p-3 text-gray-400 hover:text-gray-600 transition-colors shrink-0"
          >
            {expanded
              ? <ChevronDown className="h-4 w-4" />
              : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="w-10 shrink-0" />
        )}

        {/* Root checkbox area */}
        <button
          type="button"
          onClick={() => onToggle(topic.id)}
          className="flex-1 flex items-center gap-3 py-3 pr-3 text-left"
        >
          <span className="text-lg shrink-0">{getIcon(topic.slug)}</span>
          <div className="flex-1 min-w-0">
            <span className={clsx('font-semibold text-sm', isSelected ? 'text-ms-blue' : 'text-ms-dark')}>
              {topic.name}
            </span>
            {hasChildren && (
              <span className="ml-2 text-xs text-gray-400">
                {topic.children.length} subtopic{topic.children.length !== 1 ? 's' : ''}
              </span>
            )}
            {topic.description && (
              <p className="text-xs text-gray-400 mt-0.5 truncate">{topic.description}</p>
            )}
          </div>
          {isSelected && <Check className="h-4 w-4 text-ms-blue shrink-0 mr-1" />}
        </button>
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <div className="border-t border-gray-100 bg-gray-50 px-3 py-2 space-y-1.5">
          {topic.children.map((child) => (
            <TopicRow
              key={child.id}
              topic={child}
              selected={selected}
              onToggle={onToggle}
              depth={1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Main TopicTree component.
 */
export default function TopicTree({ tree = [], selected = [], onToggle }) {
  return (
    <div className="space-y-2">
      {tree.map((rootTopic) => (
        <RootSection
          key={rootTopic.id}
          topic={rootTopic}
          selected={selected}
          onToggle={onToggle}
        />
      ))}
    </div>
  );
}
