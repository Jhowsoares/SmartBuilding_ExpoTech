import { useState, useEffect, useCallback } from 'react'
import { getHealth } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { format } from 'date-fns'

function ServiceCard({ name, status, latency, lastCheck, icon }) {
  const isOk = status === 'operational' || status === 'healthy' || status === true
  const isWarn = status === 'degraded'
  const color = isOk ? 'green' : isWarn ? 'yellow' : 'red'
  const label = isOk ? 'OPERACIONAL' : isWarn ? 'DEGRADADO' : 'OFFLINE'

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-xl ${isOk ? 'bg-green-900/30' : isWarn ? 'bg-yellow-900/30' : 'bg-red-900/30'}`}>
          {icon}
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full border
          ${isOk ? 'text-green-400 border-green-700 bg-green-900/30'
          : isWarn ? 'text-yellow-400 border-yellow-700 bg-yellow-900/30'
          : 'text-red-400 border-red-700 bg-red-900/30'}`}>
          {label}
        </span>
      </div>
      <p className="text-white font-semibold">{name}</p>
      <div className="mt-3 space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-gray-400">Latência</span>
          <span className={`font-mono font-medium text-${color}-400`}>
            {latency != null ? `${latency}ms` : '--'}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-400">Verificado</span>
          <span className="text-gray-300">{lastCheck}</span>
        </div>
      </div>
    </div>
  )
}

const MOCK_SENSORS = [
  { room: 'Sala A - Térreo', time: '10:42:05', temp: '22.4°C', hum: '45%', status: 'ATIVO', statusColor: 'green' },
  { room: 'Auditório Principal', time: '10:41:59', temp: '21.8°C', hum: '50%', status: 'ATIVO', statusColor: 'green' },
  { room: 'Servidor - Rack 1', time: '09:15:22', temp: '--', hum: '--', status: 'OFFLINE', statusColor: 'red' },
  { room: 'Reunião B', time: '10:42:01', temp: '26.1°C', hum: '42%', status: 'ALERTA TEMP', statusColor: 'yellow' },
]

export default function SystemStatusPage() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const fetchHealth = useCallback(async () => {
    try {
      const res = await getHealth()
      setHealth(res.data)
      setLastRefresh(new Date())
    } catch {
      setHealth({ status: 'degraded', database: false, redis: false })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 15000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  const services = health ? [
    {
      name: 'Backend API',
      status: 'operational',
      latency: 42,
      lastCheck: 'Agora',
      icon: <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>,
    },
    {
      name: 'PostgreSQL',
      status: health.database ? 'operational' : 'offline',
      latency: health.database ? 18 : null,
      lastCheck: health.database ? 'Há 2s' : 'Falha',
      icon: <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" /></svg>,
    },
    {
      name: 'Redis Cache',
      status: health.redis ? 'operational' : 'offline',
      latency: health.redis ? 8 : null,
      lastCheck: health.redis ? 'Agora' : 'Falha 1m atrás',
      icon: <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
    },
    {
      name: 'MQTT Broker',
      status: 'operational',
      latency: 8,
      lastCheck: 'Agora',
      icon: <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" /></svg>,
    },
  ] : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white font-semibold">Monitoramento em tempo real da infraestrutura core.</h2>
          <p className="text-gray-400 text-sm mt-0.5">
            Última verificação: {format(lastRefresh, 'HH:mm:ss')}
          </p>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>

      {/* Service cards */}
      {loading ? (
        <div className="flex items-center justify-center h-48"><LoadingSpinner size="lg" /></div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {services.map((s) => <ServiceCard key={s.name} {...s} />)}
        </div>
      )}

      {/* Sensor activity */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-white font-semibold">Atividade dos Sensores</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700 bg-gray-800/50">
                {['Sala', 'Última Leitura', 'Temp', 'Umidade', 'Status'].map((h) => (
                  <th key={h} className="table-header">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {MOCK_SENSORS.map((s) => (
                <tr key={s.room} className="hover:bg-gray-700/30">
                  <td className="table-cell font-medium text-white">{s.room}</td>
                  <td className="table-cell text-gray-400 font-mono text-xs">{s.time}</td>
                  <td className="table-cell text-gray-300">{s.temp}</td>
                  <td className="table-cell text-gray-300">{s.hum}</td>
                  <td className="table-cell">
                    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full
                      ${s.statusColor === 'green' ? 'text-green-400 bg-green-900/30'
                      : s.statusColor === 'yellow' ? 'text-yellow-400 bg-yellow-900/30'
                      : 'text-red-400 bg-red-900/30'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full bg-${s.statusColor}-400`} />
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MQTT connections */}
      <div className="card p-6">
        <h3 className="text-white font-semibold mb-4">Conexões MQTT Ativas</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-400">342</p>
            <p className="text-gray-400 text-sm mt-1">Total de Clientes</p>
            <p className="text-gray-500 text-xs mt-0.5">+12 hoje</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-green-400">320</p>
            <p className="text-gray-400 text-sm mt-1">Publishers (Sensores)</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-purple-400">22</p>
            <p className="text-gray-400 text-sm mt-1">Subscribers (Painéis)</p>
          </div>
        </div>
      </div>
    </div>
  )
}
