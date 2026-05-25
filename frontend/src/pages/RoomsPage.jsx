import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getRooms, getDevices, controlDevice, createRoom } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

// ── Toast ──────────────────────────────────────────────────────────────────
function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t) }, [onClose])
  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-medium border
      ${type === 'success'
        ? 'bg-green-900/60 text-green-200 border-green-700/60 backdrop-blur-sm'
        : 'bg-red-900/60 text-red-200 border-red-700/60 backdrop-blur-sm'}`}>
      {type === 'success'
        ? <span className="material-symbols-outlined text-[18px] text-green-400">check_circle</span>
        : <span className="material-symbols-outlined text-[18px] text-red-400">error</span>}
      {message}
    </div>
  )
}

// ── New Room Modal ─────────────────────────────────────────────────────────
function NewRoomModal({ onClose, onSave }) {
  const [form, setForm] = useState({ name: '', building: 'Edifício Principal', floor: 1, area_m2: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name) { setError('Nome da sala é obrigatório.'); return }
    setLoading(true)
    try {
      await createRoom({ ...form, floor: Number(form.floor), area_m2: form.area_m2 ? Number(form.area_m2) : null })
      onSave(); onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar sala.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-sb-card border border-sb-border rounded-2xl w-full max-w-md p-6 m-4 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sb-on-surface font-semibold text-lg">Nova Sala</h3>
          <button onClick={onClose} className="text-sb-outline hover:text-sb-on-surface p-1 rounded-lg hover:bg-sb-card-high">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-sb-on-muted mb-1">Nome da Sala *</label>
            <input className="input-field" placeholder="Ex: Sala 101 - TI"
              value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-sm text-sb-on-muted mb-1">Prédio</label>
            <input className="input-field" value={form.building}
              onChange={(e) => setForm((f) => ({ ...f, building: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-sb-on-muted mb-1">Andar</label>
              <input className="input-field" type="number" min={0} value={form.floor}
                onChange={(e) => setForm((f) => ({ ...f, floor: e.target.value }))} />
            </div>
            <div>
              <label className="block text-sm text-sb-on-muted mb-1">Área (m²)</label>
              <input className="input-field" type="number" min={1} placeholder="45"
                value={form.area_m2} onChange={(e) => setForm((f) => ({ ...f, area_m2: e.target.value }))} />
            </div>
          </div>
          {error && <p className="text-sb-error text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 btn-secondary">Cancelar</button>
            <button type="submit" disabled={loading} className="flex-1 btn-primary disabled:opacity-50">
              {loading ? 'Criando...' : 'Criar Sala'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── AC Control block (inline in card) ─────────────────────────────────────
function ACControl({ device }) {
  const [loading, setLoading] = useState('')
  // C3 fix: API returns power_on (boolean) and setpoint_celsius (number)
  const [setpoint, setSetpoint] = useState(device.setpoint_celsius ?? device.setpoint ?? 22)
  const [isPoweredOn, setIsPoweredOn] = useState(device.power_on === true)

  const sendControl = async (action, value) => {
    setLoading(action)
    try {
      await controlDevice(device.id, { action, value })
      if (action === 'on') setIsPoweredOn(true)
      if (action === 'off') setIsPoweredOn(false)
      if (action === 'setpoint') setSetpoint(value)
    } catch { /* silent */ }
    finally { setLoading('') }
  }

  return (
    <div className="border-t border-sb-border pt-4 mt-auto">
      {/* Label + segmented toggle */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className={`material-symbols-outlined text-[20px] ${isPoweredOn ? 'text-sb-primary' : 'text-sb-outline'}`}>
            mode_fan
          </span>
          <span className="text-sm font-medium text-sb-on-surface">Ar Condicionado</span>
        </div>
        <div className="flex bg-sb-surface border border-sb-border rounded-lg overflow-hidden text-xs font-semibold">
          <button
            onClick={() => sendControl('on', null)}
            disabled={loading === 'on'}
            className={`px-3 py-1.5 transition-colors ${isPoweredOn
              ? 'bg-sb-primary text-sb-on-primary'
              : 'text-sb-outline hover:bg-sb-card-high'}`}
          >
            {loading === 'on' ? '…' : 'ON'}
          </button>
          <button
            onClick={() => sendControl('off', null)}
            disabled={loading === 'off'}
            className={`px-3 py-1.5 transition-colors ${!isPoweredOn
              ? 'bg-sb-card-highest text-sb-on-surface'
              : 'text-sb-outline hover:bg-sb-card-high'}`}
          >
            {loading === 'off' ? '…' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Setpoint row */}
      <div className={`flex items-center gap-3 ${!isPoweredOn ? 'opacity-40 pointer-events-none' : ''}`}>
        <span className="font-data text-xl text-sb-on-surface w-14 flex-shrink-0">
          {setpoint}°C
        </span>
        <div className="flex-1 flex items-center gap-2">
          <span className="text-xs text-sb-outline">16°</span>
          <input
            type="range" min={16} max={30} value={setpoint}
            onChange={(e) => setSetpoint(Number(e.target.value))}
            onMouseUp={(e) => sendControl('setpoint', Number(e.target.value))}
            onTouchEnd={(e) => sendControl('setpoint', Number(e.target.value))}
            className="flex-1"
          />
          <span className="text-xs text-sb-outline">30°</span>
        </div>
      </div>
    </div>
  )
}

// ── Room Card ──────────────────────────────────────────────────────────────
function RoomCard({ room }) {
  const [devices, setDevices] = useState([])
  const [devLoading, setDevLoading] = useState(true)

  useEffect(() => {
    getDevices({ room_id: room.id })
      .then((res) => {
        const arr = Array.isArray(res.data) ? res.data : res.data?.data || []
        setDevices(arr)
      })
      .catch(() => setDevices([]))
      .finally(() => setDevLoading(false))
  }, [room.id])

  const onlineCount = devices.filter((d) => d.status === 'online' || d.is_online).length
  const offlineCount = devices.length - onlineCount
  const acDevices = devices.filter((d) => {
    const t = (d.device_type || d.type || '').toLowerCase()
    return t.includes('ac') || t === ''
  })
  const isRoomOnline = onlineCount > 0

  return (
    <div className="bg-sb-card border border-sb-border rounded-xl p-4 flex flex-col hover:border-sb-outline transition-colors duration-200">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
              isRoomOnline
                ? 'bg-sb-primary shadow-[0_0_8px_rgba(173,198,255,0.5)]'
                : 'bg-sb-error shadow-[0_0_8px_rgba(255,180,171,0.3)]'
            }`} />
            <Link
              to={`/rooms/${room.id}`}
              className="font-semibold text-sb-on-surface hover:text-sb-primary transition-colors leading-tight"
            >
              {room.name}
            </Link>
          </div>
          <p className="text-xs text-sb-outline ml-[18px]">
            {[room.building, room.floor !== undefined && `${room.floor}º Andar`]
              .filter(Boolean).join(' • ')}
          </p>
        </div>
        <Link
          to={`/rooms/${room.id}`}
          className="text-sb-outline hover:text-sb-on-surface transition-colors p-0.5"
          title="Ver detalhes"
        >
          <span className="material-symbols-outlined text-[20px]">more_vert</span>
        </Link>
      </div>

      {/* Device count chips */}
      {devLoading ? (
        <div className="flex gap-2 mb-4">
          <div className="h-7 w-20 bg-sb-card-high rounded-md animate-pulse" />
          <div className="h-7 w-24 bg-sb-card-high rounded-md animate-pulse" />
        </div>
      ) : (
        <div className="flex gap-2 mb-4 flex-wrap">
          <div className="bg-sb-surface border border-sb-border rounded-md px-2 py-1 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px] text-sb-outline">router</span>
            <span className="font-data text-sm text-sb-on-surface">{devices.length} Disp.</span>
          </div>
          <div className="bg-sb-surface border border-sb-border rounded-md px-2 py-1 flex items-center gap-2">
            <span className="font-data text-sm text-sb-primary">{onlineCount} ON</span>
            {offlineCount > 0 && (
              <>
                <span className="w-px h-3 bg-sb-border" />
                <span className="font-data text-sm text-sb-error">{offlineCount} OFF</span>
              </>
            )}
            {offlineCount === 0 && onlineCount > 0 && (
              <>
                <span className="w-px h-3 bg-sb-border" />
                <span className="font-data text-sm text-sb-outline">0 OFF</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* AC control — always visible */}
      {!devLoading && acDevices.length > 0 && (
        <ACControl device={acDevices[0]} />
      )}

      {/* No AC — show "Ver detalhes" link instead */}
      {!devLoading && acDevices.length === 0 && (
        <div className="border-t border-sb-border pt-4 mt-auto">
          <Link
            to={`/rooms/${room.id}`}
            className="flex items-center justify-center gap-2 text-sm text-sb-primary hover:text-blue-300 transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">open_in_new</span>
            Ver detalhes da sala
          </Link>
        </div>
      )}
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function RoomsPage() {
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [floorFilter, setFloorFilter] = useState('all')
  const [showNewRoom, setShowNewRoom] = useState(false)
  const [toast, setToast] = useState(null)

  const fetchRooms = async () => {
    setLoading(true)
    try {
      const res = await getRooms()
      const arr = Array.isArray(res.data) ? res.data : res.data?.data || res.data?.items || []
      setRooms(arr)
    } catch {
      setRooms([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchRooms() }, [])

  const floors = [...new Set(rooms.map((r) => r.floor).filter((f) => f !== undefined))].sort()

  const filtered = rooms.filter((r) => {
    const matchSearch = (r.name || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.building || '').toLowerCase().includes(search.toLowerCase())
    const matchFloor = floorFilter === 'all' || String(r.floor) === floorFilter
    return matchSearch && matchFloor
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      {showNewRoom && (
        <NewRoomModal
          onClose={() => setShowNewRoom(false)}
          onSave={() => { fetchRooms(); setToast({ message: 'Sala criada com sucesso!', type: 'success' }) }}
        />
      )}

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          {/* Search */}
          <div className="relative sm:w-72">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-sb-outline">
              search
            </span>
            <input
              className="w-full bg-sb-card border border-sb-border text-sb-on-surface rounded-lg pl-10 pr-4 py-2 text-sm
                         placeholder:text-sb-outline focus:border-sb-primary focus:ring-1 focus:ring-sb-primary outline-none transition-colors"
              placeholder="Buscar sala ou dispositivo..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          {/* Floor filter */}
          <div className="relative sm:w-44">
            <select
              className="w-full bg-sb-card border border-sb-border text-sb-on-surface rounded-lg pl-4 pr-9 py-2 text-sm
                         appearance-none focus:border-sb-primary focus:ring-1 focus:ring-sb-primary outline-none cursor-pointer transition-colors"
              value={floorFilter}
              onChange={(e) => setFloorFilter(e.target.value)}
            >
              <option value="all">Todos os Andares</option>
              {floors.map((f) => <option key={f} value={String(f)}>{f}º Andar</option>)}
            </select>
            <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-[18px] text-sb-outline pointer-events-none">
              expand_more
            </span>
          </div>
        </div>

        <button
          onClick={() => setShowNewRoom(true)}
          className="w-full sm:w-auto bg-sb-secondary-c hover:bg-sb-primary-btn hover:text-white text-sb-on-surface
                     border border-sb-border hover:border-transparent rounded-lg px-4 py-2 flex items-center
                     justify-center gap-2 text-sm font-medium transition-all duration-150 shadow-sm"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          Nova Sala
        </button>
      </div>

      {/* Room count */}
      <p className="text-xs text-sb-outline">
        {filtered.length} sala{filtered.length !== 1 ? 's' : ''} encontrada{filtered.length !== 1 ? 's' : ''}
      </p>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="bg-sb-card border border-sb-border rounded-xl flex flex-col items-center justify-center py-20 text-sb-outline">
          <span className="material-symbols-outlined text-[56px] opacity-30 mb-4">meeting_room</span>
          <p className="text-base font-medium">
            {rooms.length === 0 ? 'Nenhuma sala encontrada' : 'Nenhum resultado para a busca'}
          </p>
          <p className="text-sm mt-1 opacity-60">
            {rooms.length === 0 ? 'Clique em "Nova Sala" para começar.' : 'Tente outro termo.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((room) => <RoomCard key={room.id} room={room} />)}
        </div>
      )}
    </div>
  )
}
