const severityConfig = {
  info: 'bg-blue-900 text-blue-300 border border-blue-700',
  warning: 'bg-yellow-900 text-yellow-300 border border-yellow-700',
  critical: 'bg-red-900 text-red-300 border border-red-700',
  error: 'bg-red-900 text-red-300 border border-red-700',
}

const statusConfig = {
  active: 'bg-red-900 text-red-300 border border-red-700',
  acknowledged: 'bg-yellow-900 text-yellow-300 border border-yellow-700',
  resolved: 'bg-green-900 text-green-300 border border-green-700',
}

export function SeverityBadge({ severity }) {
  const cls = severityConfig[severity?.toLowerCase()] || 'bg-gray-700 text-gray-300'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {severity || 'unknown'}
    </span>
  )
}

export function StatusBadge({ status }) {
  const cls = statusConfig[status?.toLowerCase()] || 'bg-gray-700 text-gray-300'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status || 'unknown'}
    </span>
  )
}
