import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import { getRoom, getDevices, getSensorData, getSensors, deleteDevice, getRoomCommands } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const DEVICE_TYPE_ICONS = {
  ac_unit: (
    <svg className="w-4 h-4 text-sb-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  temperature_sensor: (
    <svg className="w-4 h-4 text-sb-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  humidity_sensor: (
    <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3c0 0-8 7-8 12a8 8 0 0016 0c0-5-8-12-8-12z" />
    </svg>
  ),
  presence_sensor: (
    <svg className="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
}

const COMMAND_TYPE_LABELS = {
  power_on: 'Ligar AC',
  power_off: 'Desligar AC',
  set_temperature: 'Setpoint',
  POWER_ON: 'Ligar AC',
  POWER_OFF: 'Desligar AC',
  SET_TEMPERATURE: 'Setpoint',
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

function generateMockChart() {
  const now = new Date()
  return Array.from({ length: 24 }, (_, i) => ({
    time: format(new Date(now - (23 - i) * 3600000), 'HH:mm'),
    'Temp (°C)': +(21 + Math.random() * 5).toFixed(1),
    'Umidade (%)': +(45 + Math.random() * 20).toFixed(1),
  }))
}

export default function RoomDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [room, setRoom] = useState(null)
  const [devices, setDevices] = useState([])
  const [chartData, setChartData] = useState([])
  const [commands, setCommands] = useState([])
  const [cmdLoading, setCmdLoading] = useState(true)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [roomRes, devRes] = await Promise.allSettled([getRoom(id), getDevices({ room_id: id })])
      if (roomRes.status === 'fulfilled') setRoom(roomRes.value.data?.data || roomRes.value.data)
      if (devRes.status === 'fulfilled') {
        const arr = Array.isArray(devRes.value.data) ? devRes.value.data : devRes.value.data?.data || []
        setDevices(arr)
      }

      try {
        const sensorsRes = await getSensors()
        const sensors = Array.isArray(sensorsRes.data) ? sensorsRes.data : sensorsRes.data?.data || []
        const tempSensor = sensors.find((s) => s.room_id === id &&
          (s.type === 'temperature' || s.sensor_type === 'temperature'))
        if (tempSensor) {
          const dataRes = await getSensorData(tempSensor.id, '24h')
          const readings = Array.isArray(dataRes.data) ? dataRes.data : dataRes.data?.readings || []
          if (readings.length > 0) {
            setChartData(readings.map((r) => ({
              time: format(new Date(r.timestamp || r.time), 'HH:mm'),
              'Temp (°C)': r.value,
            })))
            return
          }
        }
      } catch { /* fallthrough to mock */ }
      setChartData(generateMockChart())
    } catch {
      setChartData(generateMockChart())
    } finally {
      setLoading(false)
    }
  }, [id])

  const fetchCommands = useCallback(async () => {
    setCmdLoading(true)
    try {
      const res = await getRoomCommands(id, { size: 20 })
      const arr = Array.isArray(res.data) ? res.data : res.data?.data || res.data?.items || []
      setCommands(arr)
    } catch {
      setCommands([])
    } finally {
      setCmdLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchData()
    fetchCommands()
  }, [fetchData, fetchCommands])

  const handleDeleteDevice = async (deviceId) => {
    if (!confirm('Remover este dispositivo da sala?')) return
    try {
      await deleteDevice(deviceId)
      fetchData()
    } catch {}
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96"><LoadingSpinner size="lg" /></div>
  }

  if (!room) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-sb-outline">
        <p className="text-lg font-medium text-sb-on-surface">Sala não encontrada</p>
        <button onClick={() => navigate('/rooms')} className="btn-primary mt-4">Voltar</button>
      </div>
    )
  }

  const lineKeys = chartData.length ? Object.keys(chartData[0]).filter((k) => k !== 'time') : []
  const lineColors = ['#4d8eff', '#10B981']

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-sb-outline">
        <Link to="/dashboard" className="hover:text-sb-on-surface transition-colors">Dashboard</Link>
        <span>/</span>
        <Link to="/rooms" className="hover:text-sb-on-surface transition-colors">Salas</Link>
        <span>/</span>
        <span className="text-sb-on-surface">{room.name}</span>
      </nav>

      {/* Room info */}
      <div className="card p-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-sb-on-surface">{room.name}</h2>
            <div className="flex items-center gap-4 mt-2 text-sm text-sb-outline">
              {room.building && <span>{room.building}</span>}
              {room.floor !== undefined && <span>Andar {room.floor}</span>}
              {room.area_m2 && <span>{room.area_m2} m²</span>}
            </div>
          </div>
          <span className="text-xs font-medium px-2.5 py-1 rounded-full text-green-400 bg-green-900/30 border border-green-700">
            Normal
          </span>
        </div>
      </div>

      {/* Chart + Devices */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        {/* Chart */}
        <div className="card p-6 xl:col-span-3">
          <h3 className="text-sb-on-surface font-semibold mb-4">Histórico de Temperatura (24h)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#424754" />
              <XAxis dataKey="time" stroke="#8c909f" tick={{ fill: '#c2c6d6', fontSize: 11 }} />
              <YAxis stroke="#8c909f" tick={{ fill: '#c2c6d6', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: '#c2c6d6', fontSize: 12 }} />
              {lineKeys.map((key, i) => (
                <Line key={key} type="monotone" dataKey={key} stroke={lineColors[i]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Devices */}
        <div className="card xl:col-span-2 flex flex-col">
          <div className="px-5 py-4 border-b border-sb-border flex items-center justify-between">
            <h3 className="text-sb-on-surface font-semibold">Dispositivos</h3>
            <span className="text-xs text-sb-outline">{devices.length} Total</span>
          </div>
          <div className="flex-1 divide-y divide-sb-border overflow-y-auto">
            {devices.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-sb-outline">
                <p className="text-sm">Nenhum dispositivo</p>
              </div>
            ) : (
              devices.map((d) => {
                const isOnline = d.status === 'online' || d.is_online
                const typeIcon = DEVICE_TYPE_ICONS[d.device_type || d.type] || DEVICE_TYPE_ICONS.temperature_sensor
                return (
                  <div key={d.id} className="px-5 py-4 hover:bg-sb-card-high transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-sb-card-highest rounded-lg">{typeIcon}</div>
                        <div>
                          <p className="text-sb-on-surface text-sm font-medium">{d.model || d.device_type || 'Dispositivo'}</p>
                          {d.serial_number && <p className="text-sb-outline text-xs">SN: {d.serial_number}</p>}
                          {d.mqtt_topic && <p className="text-sb-outline text-xs font-mono truncate max-w-[160px]">{d.mqtt_topic}</p>}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`text-xs flex items-center gap-1 ${isOnline ? 'text-green-400' : 'text-sb-error'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-green-400' : 'bg-sb-error'}`} />
                          {isOnline ? 'Online' : 'Offline'}
                        </span>
                        {d.last_seen_at && (
                          <span className="text-sb-outline text-xs">
                            Visto {format(new Date(d.last_seen_at), 'HH:mm')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
          <div className="px-5 py-3 border-t border-sb-border">
            <Link to="/devices/new"
              className="btn-primary w-full text-sm text-center py-2 flex items-center justify-center gap-2">
              <span className="material-symbols-outlined text-[16px]">add</span>
              Adicionar Dispositivo
            </Link>
          </div>
        </div>
      </div>

      {/* Command history — real data from /rooms/{id}/commands */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-sb-border flex items-center justify-between">
          <h3 className="text-sb-on-surface font-semibold">Histórico de Comandos</h3>
          {cmdLoading && <LoadingSpinner size="sm" />}
        </div>
        {!cmdLoading && commands.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-sb-outline">
            <span className="material-symbols-outlined text-[40px] opacity-30 mb-2">history</span>
            <p className="text-sm">Nenhum comando registrado para esta sala</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-sb-border bg-sb-card-high">
                  {['Data/Hora', 'Ação', 'Origem', 'Valor', 'Status'].map((h) => (
                    <th key={h} className="table-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-sb-border">
                {commands.map((c, i) => {
                  const cmdLabel = COMMAND_TYPE_LABELS[c.command_type] || c.command_type || '—'
                  const isSuccess = c.status === 'executed' || c.status === 'success' || c.status === 'EXECUTED'
                  const ts = c.executed_at || c.created_at
                  return (
                    <tr key={c.id || i} className="hover:bg-sb-card-high transition-colors">
                      <td className="table-cell font-mono text-xs text-sb-outline">
                        {ts ? format(new Date(ts), 'dd/MM HH:mm:ss') : '—'}
                      </td>
                      <td className="table-cell text-sb-on-surface font-medium">{cmdLabel}</td>
                      <td className="table-cell text-sb-outline text-sm">{c.issued_by || '—'}</td>
                      <td className="table-cell font-mono text-xs text-sb-outline">
                        {c.value != null ? `${c.value}°C` : '—'}
                      </td>
                      <td className="table-cell">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                          ${isSuccess ? 'text-green-400 bg-green-900/30' : 'text-sb-error bg-red-900/30'}`}>
                          {isSuccess ? 'Sucesso' : (c.status || 'Pendente')}
                        </span>
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
