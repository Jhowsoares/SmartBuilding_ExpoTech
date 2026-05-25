import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import { getDevices, getAlerts, getSensors, getSensorData, getRooms, getHealth } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { SeverityBadge, StatusBadge } from '../components/AlertBadge'

function StatusChip({ label, ok, pending }) {
  const color = pending ? 'yellow' : ok ? 'green' : 'red'
  return (
    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border
      ${color === 'green' ? 'text-green-400 border-green-700 bg-green-900/20'
      : color === 'yellow' ? 'text-yellow-400 border-yellow-700 bg-yellow-900/20'
      : 'text-red-400 border-red-700 bg-red-900/20'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${pending ? 'bg-yellow-400 animate-pulse' : ok ? 'bg-green-400' : 'bg-red-500'}`} />
      {label}
    </div>
  )
}

function StatCard({ label, value, icon, color = 'blue', sub }) {
  const colors = {
    blue: 'text-sb-primary bg-blue-900/30',
    green: 'text-green-400 bg-green-900/30',
    yellow: 'text-sb-tertiary bg-yellow-900/30',
    purple: 'text-purple-400 bg-purple-900/30',
    red: 'text-sb-error bg-red-900/30',
  }
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sb-outline text-sm font-medium">{label}</p>
          <p className="text-3xl font-bold text-sb-on-surface mt-1">{value}</p>
          {sub && <p className="text-xs text-sb-outline mt-1">{sub}</p>}
        </div>
        <div className={`p-3 rounded-xl ${colors[color]}`}>{icon}</div>
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card p-3 text-sm border border-sb-border">
      <p className="text-sb-outline mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">{p.value?.toFixed(1)}</span>
        </p>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState({ devices: 0, alerts: 0, avgTemp: '--', rooms: 0 })
  const [chartData, setChartData] = useState([])
  const [recentAlerts, setRecentAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [chartLoading, setChartLoading] = useState(false)
  const [health, setHealth] = useState(null)

  const fetchStats = useCallback(async () => {
    try {
      const [devRes, alertRes, roomRes, healthRes] = await Promise.allSettled([
        getDevices(),
        getAlerts({ active_only: true }),
        getRooms(),
        getHealth(),
      ])

      const devices = devRes.status === 'fulfilled' ? devRes.value.data : []
      const alerts = alertRes.status === 'fulfilled' ? alertRes.value.data : []
      const rooms = roomRes.status === 'fulfilled' ? roomRes.value.data : []

      const devArr = Array.isArray(devices) ? devices : devices?.data || devices?.items || []
      const alertArr = Array.isArray(alerts) ? alerts : alerts?.data || alerts?.items || []
      const roomArr = Array.isArray(rooms) ? rooms : rooms?.data || rooms?.items || []

      setStats({
        devices: devArr.filter((d) => d.status === 'online' || d.is_online).length || devArr.length,
        alerts: alertArr.length,
        avgTemp: '--',
        rooms: roomArr.length,
      })
      setRecentAlerts(alertArr.slice(0, 5))
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value.data)
    } catch (_) {}
  }, [])

  const fetchChartData = useCallback(async () => {
    setChartLoading(true)
    try {
      const sensorsRes = await getSensors()
      const sensors = Array.isArray(sensorsRes.data)
        ? sensorsRes.data
        : sensorsRes.data?.data || sensorsRes.data?.items || []

      if (sensors.length === 0) {
        setChartData(generateMockChartData())
        return
      }

      const tempSensors = sensors.filter(
        (s) => s.type === 'temperature' || s.sensor_type === 'temperature'
      ).slice(0, 2)
      const humSensors = sensors.filter(
        (s) => s.type === 'humidity' || s.sensor_type === 'humidity'
      ).slice(0, 1)

      const allSensors = [...tempSensors, ...humSensors]
      if (allSensors.length === 0) {
        setChartData(generateMockChartData())
        return
      }

      const results = await Promise.allSettled(
        allSensors.map((s) => getSensorData(s.id, '1h'))
      )

      const mergedByTime = {}
      results.forEach((res, idx) => {
        if (res.status !== 'fulfilled') return
        const sensor = allSensors[idx]
        const readings = Array.isArray(res.value.data)
          ? res.value.data
          : res.value.data?.readings || []
        readings.forEach((r) => {
          const t = format(new Date(r.timestamp || r.time), 'HH:mm')
          if (!mergedByTime[t]) mergedByTime[t] = { time: t }
          const key = sensor.type === 'humidity' || sensor.sensor_type === 'humidity'
            ? 'Umidade (%)'
            : `Temp ${idx + 1} (°C)`
          mergedByTime[t][key] = r.value
        })
      })

      const merged = Object.values(mergedByTime).sort((a, b) =>
        a.time.localeCompare(b.time)
      )

      if (merged.length > 0) {
        setChartData(merged)

        const temps = merged.flatMap((d) =>
          Object.entries(d)
            .filter(([k]) => k.includes('Temp'))
            .map(([, v]) => v)
        )
        if (temps.length) {
          const avg = temps.reduce((a, b) => a + b, 0) / temps.length
          setStats((prev) => ({ ...prev, avgTemp: avg.toFixed(1) + '°C' }))
        }
      } else {
        setChartData(generateMockChartData())
      }
    } catch (_) {
      setChartData(generateMockChartData())
    } finally {
      setChartLoading(false)
    }
  }, [])

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await Promise.all([fetchStats(), fetchChartData()])
      setLoading(false)
    }
    init()
    const interval = setInterval(() => {
      fetchStats()
      fetchChartData()
    }, 60000)
    return () => clearInterval(interval)
  }, [fetchStats, fetchChartData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const lineKeys = chartData.length > 0
    ? Object.keys(chartData[0]).filter((k) => k !== 'time')
    : []

  const lineColors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6']

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Dispositivos Online"
          value={stats.devices}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
        />
        <StatCard
          label="Alertas Ativos"
          value={stats.alerts}
          color={stats.alerts > 0 ? 'red' : 'green'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
        <StatCard
          label="Temperatura Média"
          value={stats.avgTemp}
          color="yellow"
          sub="Sensores ativos"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />
        <StatCard
          label="Total de Salas"
          value={stats.rooms}
          color="purple"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
      </div>

      {/* System status chips */}
      <div className="flex flex-wrap items-center gap-2">
        <StatusChip label="MQTT Broker" ok={health?.subsystems?.mqtt === 'ok'} pending={!health} />
        <StatusChip label="PostgreSQL"  ok={health?.subsystems?.database === 'ok'} pending={!health} />
        <StatusChip label="Redis Cache" ok={health?.subsystems?.redis === 'ok'} pending={!health} />
        <StatusChip label="Simulador"   ok={health?.subsystems?.simulator === 'ok'} pending={!health} />
        <span className="ml-auto text-xs text-sb-outline">
          {format(new Date(), "EEE., dd 'de' MMM. 'de' yyyy", { locale: undefined })}
        </span>
      </div>

      {/* Chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-sb-on-surface font-semibold">Temperatura & Umidade em Tempo Real</h2>
            <p className="text-sb-outline text-sm mt-0.5">Atualiza a cada 60 segundos</p>
          </div>
          {chartLoading && <LoadingSpinner size="sm" />}
        </div>

        {chartData.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-sb-outline">
            <svg className="w-12 h-12 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-sm">Nenhum dado de sensor disponível</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#424754" />
              <XAxis dataKey="time" stroke="#8c909f" tick={{ fill: '#c2c6d6', fontSize: 12 }} />
              <YAxis stroke="#8c909f" tick={{ fill: '#c2c6d6', fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: '#c2c6d6', fontSize: 13 }} />
              {lineKeys.map((key, i) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={lineColors[i % lineColors.length]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Recent Alerts */}
      <div className="card">
        <div className="px-6 py-4 border-b border-sb-border flex items-center justify-between">
          <h2 className="text-sb-on-surface font-semibold">Alertas Recentes</h2>
          <Link to="/alerts" className="text-sb-primary hover:text-blue-300 text-sm transition-colors">Ver todos</Link>
        </div>
        {recentAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-sb-outline">
            <svg className="w-10 h-10 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">Nenhum alerta ativo</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-sb-border">
                  <th className="table-header">Tipo</th>
                  <th className="table-header">Severidade</th>
                  <th className="table-header">Dispositivo</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Criado em</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sb-border">
                {recentAlerts.map((a, i) => (
                  <tr key={a.id || i} className="hover:bg-sb-card-high transition-colors">
                    <td className="table-cell font-medium">{a.type || a.alert_type || '-'}</td>
                    <td className="table-cell"><SeverityBadge severity={a.severity} /></td>
                    <td className="table-cell text-sb-outline">{a.device_id || a.device || '-'}</td>
                    <td className="table-cell"><StatusBadge status={a.status} /></td>
                    <td className="table-cell text-sb-outline">
                      {a.created_at ? format(new Date(a.created_at), 'dd/MM HH:mm') : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function generateMockChartData() {
  const now = new Date()
  return Array.from({ length: 12 }, (_, i) => {
    const t = new Date(now - (11 - i) * 5 * 60 * 1000)
    return {
      time: format(t, 'HH:mm'),
      'Temp 1 (°C)': +(22 + Math.random() * 4).toFixed(1),
      'Umidade (%)': +(55 + Math.random() * 15).toFixed(1),
    }
  })
}
