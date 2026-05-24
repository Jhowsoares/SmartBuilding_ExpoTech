import { useState, useEffect } from 'react'
import { getRooms, getDevices, controlDevice } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function DeviceControl({ device, onRefresh }) {
  const [loading, setLoading] = useState('')
  const [setpoint, setSetpoint] = useState(device.setpoint || 22)
  const [localPower, setLocalPower] = useState(
    device.power_status === 'on' || device.is_on || false
  )

  const isOnline = device.status === 'online' || device.is_online

  const sendControl = async (action, value) => {
    setLoading(action)
    try {
      await controlDevice(device.id, { action, value })
      if (action === 'on') setLocalPower(true)
      if (action === 'off') setLocalPower(false)
      if (action === 'setpoint') setSetpoint(value)
      onRefresh()
    } catch (err) {
      console.error('Control error', err)
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="bg-gray-700/40 rounded-xl p-4 border border-gray-700 space-y-3">
      {/* Device header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <div>
            <p className="text-white text-sm font-medium">{device.name || `Dispositivo ${device.id}`}</p>
            <p className="text-gray-500 text-xs">{device.type || device.device_type || 'AC'}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`inline-block w-2 h-2 rounded-full ${isOnline ? 'bg-green-400' : 'bg-red-500'}`} />
          <span className={`text-xs ${isOnline ? 'text-green-400' : 'text-red-400'}`}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>

      {/* Power toggle */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => sendControl('on', null)}
          disabled={loading === 'on' || !isOnline}
          className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors ${
            localPower
              ? 'bg-green-600 text-white'
              : 'bg-gray-600 text-gray-300 hover:bg-green-700'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading === 'on' ? '...' : 'Ligar'}
        </button>
        <button
          onClick={() => sendControl('off', null)}
          disabled={loading === 'off' || !isOnline}
          className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors ${
            !localPower
              ? 'bg-red-700 text-white'
              : 'bg-gray-600 text-gray-300 hover:bg-red-800'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading === 'off' ? '...' : 'Desligar'}
        </button>
      </div>

      {/* Setpoint */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-400">Temperatura Alvo</span>
          <span className="text-xs font-bold text-blue-400">{setpoint}°C</span>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="range"
            min={16}
            max={30}
            value={setpoint}
            onChange={(e) => setSetpoint(Number(e.target.value))}
            disabled={!isOnline || loading === 'setpoint'}
            className="flex-1 accent-blue-500 disabled:opacity-50"
          />
          <button
            onClick={() => sendControl('setpoint', setpoint)}
            disabled={!isOnline || loading === 'setpoint'}
            className="text-xs btn-primary py-1 px-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading === 'setpoint' ? '...' : 'OK'}
          </button>
        </div>
        <div className="flex justify-between text-xs text-gray-600 mt-0.5">
          <span>16°C</span>
          <span>30°C</span>
        </div>
      </div>
    </div>
  )
}

function RoomCard({ room, onRefresh }) {
  const [devices, setDevices] = useState([])
  const [devLoading, setDevLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const fetchDevices = async () => {
    setDevLoading(true)
    try {
      const res = await getDevices({ room_id: room.id })
      const arr = Array.isArray(res.data) ? res.data : res.data?.items || []
      setDevices(arr)
    } catch (_) {
      setDevices([])
    } finally {
      setDevLoading(false)
    }
  }

  useEffect(() => {
    fetchDevices()
  }, [room.id])

  const onlineCount = devices.filter((d) => d.status === 'online' || d.is_online).length

  return (
    <div className="card overflow-hidden">
      {/* Room header */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-white font-semibold">{room.name}</h3>
            <div className="flex items-center gap-3 mt-1">
              {room.building && (
                <span className="text-gray-400 text-xs flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
                  </svg>
                  {room.building}
                </span>
              )}
              {room.floor !== undefined && (
                <span className="text-gray-400 text-xs">Andar {room.floor}</span>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-white">{devices.length}</p>
            <p className="text-xs text-gray-400">dispositivos</p>
          </div>
        </div>

        {/* Devices summary */}
        <div className="flex items-center gap-2 text-xs">
          <span className="flex items-center gap-1 text-green-400">
            <span className="w-2 h-2 rounded-full bg-green-400" />
            {onlineCount} online
          </span>
          {devices.length - onlineCount > 0 && (
            <span className="flex items-center gap-1 text-red-400">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              {devices.length - onlineCount} offline
            </span>
          )}
        </div>

        {/* Expand toggle */}
        {devices.length > 0 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-3 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            {expanded ? 'Ocultar controles' : 'Ver controles'}
            <svg
              className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>

      {/* Devices */}
      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-gray-700 pt-4">
          {devLoading ? (
            <LoadingSpinner size="sm" className="py-4" />
          ) : devices.length === 0 ? (
            <p className="text-gray-500 text-xs text-center py-2">
              Nenhum dispositivo nesta sala
            </p>
          ) : (
            devices.map((d) => (
              <DeviceControl key={d.id} device={d} onRefresh={fetchDevices} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default function RoomsPage() {
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const fetchRooms = async () => {
    setLoading(true)
    try {
      const res = await getRooms()
      const arr = Array.isArray(res.data) ? res.data : res.data?.items || []
      setRooms(arr)
    } catch (_) {
      setRooms([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRooms()
  }, [])

  const filtered = rooms.filter((r) =>
    r.name?.toLowerCase().includes(search.toLowerCase()) ||
    r.building?.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            className="input-field pl-9"
            placeholder="Buscar sala ou prédio..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button onClick={fetchRooms} className="btn-secondary flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Atualizar
        </button>
      </div>

      {/* Rooms grid */}
      {filtered.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-20 text-gray-500">
          <svg className="w-16 h-16 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5" />
          </svg>
          <p className="text-lg font-medium">
            {rooms.length === 0 ? 'Nenhuma sala encontrada' : 'Nenhum resultado para a busca'}
          </p>
          <p className="text-sm mt-1 text-gray-600">
            {rooms.length === 0 ? 'O backend não retornou salas ainda.' : 'Tente outro termo.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((room) => (
            <RoomCard key={room.id} room={room} onRefresh={fetchRooms} />
          ))}
        </div>
      )}
    </div>
  )
}
