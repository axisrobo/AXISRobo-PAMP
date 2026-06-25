import React from 'react';

type RiskLevel = 'Very Critical' | 'Critical' | 'High' | 'Medium' | 'Low' | string | null | undefined;

const RISK_STYLES: Record<string, string> = {
  'Very Critical': 'bg-red-100 text-red-700 border border-red-300',
  'Critical':      'bg-red-50 text-red-600 border border-red-200',
  'High':          'bg-orange-100 text-orange-700 border border-orange-300',
  'Medium':        'bg-yellow-100 text-yellow-700 border border-yellow-300',
  'Low':           'bg-green-100 text-green-700 border border-green-300',
};

interface RiskLevelBadgeProps {
  level: RiskLevel;
  className?: string;
}

export function RiskLevelBadge({ level, className = '' }: RiskLevelBadgeProps) {
  if (!level) {
    return <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-500 ${className}`}>—</span>;
  }
  const style = RISK_STYLES[level] ?? 'bg-gray-100 text-gray-600 border border-gray-200';
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${style} ${className}`}>
      {level}
    </span>
  );
}
