import { useState, useEffect, useCallback } from 'react'
import { format } from 'date-fns'
import { getAlerts, getAlertsHistory, acknowledgeAlert, resolveAlert } from '../services/api'
import { SeverityBadge, StatusBadge } from '../components/AlertBadge'
import LoadingSpinner from '../components/LoadingSpinner'

function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000)
    return () => clearTimeout(t)
  }, [onClose])

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all
      ${type === 'success' ? 'bg-green-800 text-green-100 border border-green-600' : 'bg-red-800 text-red-100 border border-red-600'}`}>
      {type === 'success'
        ? <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
        : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
      }
      {message}
    </div>
  )
}

export default function AlertsPage() {
  const [tab, setTab] = useState('active')
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState({})
  const [toast, setToast] = useState(null)
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [activeOnly, setActiveOnly] = useState(false)

  const showToast = (message, type = 'success') => setToast({ message, type })

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      let res
      if (tab === 'history') {
        res = await getAlertsHistory()
      } else {
        res = await getAlerts(activeOnly ? { active_only: true } : {})
      }
      const arr = Array.isArray(res.data) ? res.data : res.data?.data || res.data?.items || []
      setAlerts(arr)
    } catch (_) {
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }, [tab, activeOnly])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  const handleAcknowledge = async (id) => {
    setActionLoading((prev) => ({ ...prev, [id]: 'ack' }))
    try {
      await acknowledgeAlert(id)
      showToast('Alerta reconhecido com sucesso.')
      fetchAlerts()
    } catch (_) {
      showToast('Erro ao reconhecer alerta.', 'error')
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: null }))
    }
  }

  const handleResolve = async (id) => {
    setActionLoading((prev) => ({ ...prev, [id]: 'res' }))
    try {
      await resolveAlert(id)
      showToast('Alerta resolvido com sucesso.')
      fetchAlerts()
    } catch (_) {
      showToast('Erro ao resolver alerta.', 'error')
    } finally {
      setActionLoading((prev) => ({ ...prev, [id]: null }))
    }
  }

  const filtered = alerts.filter((a) => {
    if (filterSeverity !== 'all' && a.severity?.toLowerCase() !== filterSeverity) return false
    return true
  })

  return (
    <div className="space-y-6">
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-gray-700">
        {[
          { key: 'active', label: 'Alertas Ativos' },
          { key: 'history', label: 'Histórico' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === key
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">Todas severidades</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
        </select>

        {tab === 'active' && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="w-4 h-4 rounded accent-blue-500"
            />
            <span className="text-sm text-gray-300">Somente ativos</span>
          </label>
        )}

        <button
          onClick={fetchAlerts}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>

        <span className="ml-auto text-xs text-gray-500">
          {filtered.length} alerta{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <LoadingSpinner size="lg" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-500">
            <svg className="w-14 h-14 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="font-medium">Nenhum alerta encontrado</p>
            <p className="text-sm mt-1 text-gray-600">Tudo funcionando normalmente.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700 bg-gray-800/50">
                  <th className="table-header">Tipo</th>
                  <th className="table-header">Severidade</th>
                  <th className="table-header">Dispositivo</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Criado em</th>
                  <th className="table-header">Mensagem</th>
                  <th className="table-header text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filtered.map((a, i) => {
                  const isAck = a.status === 'acknowledged'
                  const isRes = a.status === 'resolved'
                  const aLoading = actionLoading[a.id]
                  return (
                    <tr key={a.id || i} className="hover:bg-gray-700/30 transition-colors">
                      <td className="table-cell font-medium text-white">{a.type || a.alert_type || '-'}</td>
                      <td className="table-cell"><SeverityBadge severity={a.severity} /></td>
                      <td className="table-cell text-gray-400">{a.device_id || a.device || '-'}</td>
                      <td className="table-cell"><StatusBadge status={a.status} /></td>
                      <td className="table-cell text-gray-400 whitespace-nowrap">
                        {a.created_at ? format(new Date(a.created_at), 'dd/MM/yy HH:mm') : '-'}
                      </td>
                      <td className="table-cell text-gray-400 max-w-xs truncate">
                        {a.message || a.description || '-'}
                      </td>
                      <td className="table-cell">
                        <div className="flex items-center justify-end gap-2">
                          {!isAck && !isRes && (
                            <button
                              onClick={() => handleAcknowledge(a.id)}
                              disabled={!!aLoading}
                              className="text-xs px-3 py-1 rounded-lg bg-yellow-800 text-yellow-200 hover:bg-yellow-700 transition-colors disabled:opacity-50 whitespace-nowrap"
                            >
                              {aLoading === 'ack' ? '...' : 'Reconhecer'}
                            </button>
                          )}
                          {!isRes && (
                            <button
                              onClick={() => handleResolve(a.id)}
                              disabled={!!aLoading}
                              className="text-xs px-3 py-1 rounded-lg bg-green-800 text-green-200 hover:bg-green-700 transition-colors disabled:opacity-50"
                            >
                              {aLoading === 'res' ? '...' : 'Resolver'}
                            </button>
                          )}
                          {isRes && (
                            <span className="text-xs text-gray-500">Resolvido</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
