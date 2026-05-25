import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { createDevice, getRooms } from '../services/api'

const DEVICE_TYPES = [
  { value: 'ac_unit', label: 'Ar Condicionado (AC)' },
  { value: 'temperature_sensor', label: 'Sensor de Temperatura' },
  { value: 'humidity_sensor', label: 'Sensor de Umidade' },
  { value: 'presence_sensor', label: 'Sensor de Presença' },
  { value: 'co2_sensor', label: 'Sensor de CO₂' },
]

const TOPIC_SUFFIX = {
  ac_unit: 'ac',
  temperature_sensor: 'temperature',
  humidity_sensor: 'humidity',
  presence_sensor: 'motion',
  co2_sensor: 'co2',
}

function StepIndicator({ step }) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {[
        { num: 1, label: 'Informações' },
        { num: 2, label: 'Localização' },
        { num: 3, label: 'Configuração' },
      ].map(({ num, label }, i) => (
        <div key={num} className="flex items-center flex-1">
          <div className="flex flex-col items-center">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all
              ${step === num ? 'bg-blue-600 border-blue-600 text-white'
              : step > num ? 'bg-green-600 border-green-600 text-white'
              : 'bg-gray-800 border-gray-600 text-gray-400'}`}>
              {step > num ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : num}
            </div>
            <span className={`text-xs mt-1.5 font-medium ${step >= num ? 'text-white' : 'text-gray-500'}`}>{label}</span>
          </div>
          {i < 2 && (
            <div className={`flex-1 h-0.5 mx-2 mt-[-16px] transition-all ${step > num ? 'bg-green-600' : 'bg-gray-700'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

function generateTopic(roomId, deviceType) {
  if (!roomId || !deviceType) return 'sensors/room/{uuid-da-sala}/{tipo}'
  const suffix = TOPIC_SUFFIX[deviceType] || deviceType
  const prefix = deviceType === 'ac_unit' ? 'actuators' : 'sensors'
  return `${prefix}/room/${roomId}/${suffix}`
}

export default function AddDevicePage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const [form, setForm] = useState({
    device_type: '',
    model: '',
    serial_number: '',
    room_id: '',
    notes: '',
    mqtt_topic: '',
  })

  useEffect(() => {
    getRooms().then((res) => {
      const arr = Array.isArray(res.data) ? res.data : res.data?.data || []
      setRooms(arr)
    }).catch(() => {})
  }, [])

  const generatedTopic = generateTopic(form.room_id, form.device_type)

  const update = (field, value) => setForm((f) => ({ ...f, [field]: value }))

  const handleNext = () => {
    if (step === 1) {
      if (!form.device_type) { setError('Selecione o tipo de dispositivo.'); return }
      setError('')
    }
    if (step === 2) {
      if (!form.room_id) { setError('Selecione uma sala.'); return }
      setError('')
      update('mqtt_topic', generatedTopic)
    }
    setStep((s) => s + 1)
  }

  const handleBack = () => setStep((s) => s - 1)

  const handleCopy = () => {
    navigator.clipboard.writeText(form.mqtt_topic || generatedTopic)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      const roomObj = rooms.find((r) => r.id === form.room_id)
      const name = `${DEVICE_TYPES.find((t) => t.value === form.device_type)?.label} — ${roomObj?.name || ''}`
      await createDevice({
        name,
        device_type: form.device_type,
        model: form.model || null,
        serial_number: form.serial_number || null,
        room_id: form.room_id,
        notes: form.notes || null,
        mqtt_topic: form.mqtt_topic || generatedTopic,
      })
      navigate('/rooms')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao cadastrar dispositivo.')
      setLoading(false)
    }
  }

  const selectedRoom = rooms.find((r) => r.id === form.room_id)

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/rooms')} className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-gray-800 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h2 className="text-white font-semibold text-lg">Novo Dispositivo</h2>
          <p className="text-gray-400 text-sm">Cadastre um sensor, ESP32 ou atuador</p>
        </div>
      </div>

      <div className="card p-6">
        <StepIndicator step={step} />

        {/* Step 1 — Device Info */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <p className="text-white font-medium mb-1">Dados do Equipamento</p>
              <p className="text-gray-400 text-sm mb-4">Identifique o tipo e modelo do sensor a ser integrado.</p>
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Tipo de Dispositivo *</label>
              <select className="input-field" value={form.device_type}
                onChange={(e) => update('device_type', e.target.value)}>
                <option value="">Selecione o tipo...</option>
                {DEVICE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Modelo</label>
              <input className="input-field" placeholder="Ex: DHT22, Mitsubishi Heavy, PIR AM312"
                value={form.model} onChange={(e) => update('model', e.target.value)} />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Número de Série (S/N)</label>
              <input className="input-field" placeholder="Ex: ESP32-A1B2C3D4"
                value={form.serial_number} onChange={(e) => update('serial_number', e.target.value)} />
            </div>
          </div>
        )}

        {/* Step 2 — Location */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <p className="text-white font-medium mb-1">Localização</p>
              <p className="text-gray-400 text-sm mb-4">Selecione a sala onde este dispositivo será instalado.</p>
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Sala *</label>
              <select className="input-field" value={form.room_id}
                onChange={(e) => update('room_id', e.target.value)}>
                <option value="">Selecione uma sala...</option>
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>{r.name} — {r.building || 'Prédio Principal'}</option>
                ))}
              </select>
            </div>
            {selectedRoom && (
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-white text-sm font-medium mb-2">{selectedRoom.name}</p>
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                  {selectedRoom.building && <span>Prédio: {selectedRoom.building}</span>}
                  {selectedRoom.floor !== undefined && <span>Andar: {selectedRoom.floor}</span>}
                  {selectedRoom.area_m2 && <span>Área: {selectedRoom.area_m2} m²</span>}
                </div>
              </div>
            )}
            {form.room_id && form.device_type && (
              <div className="bg-blue-900/20 border border-blue-700/50 rounded-xl p-4">
                <p className="text-blue-400 text-xs font-medium mb-1">Preview do tópico MQTT que será gerado:</p>
                <code className="text-blue-300 text-sm font-mono">{generatedTopic}</code>
              </div>
            )}
          </div>
        )}

        {/* Step 3 — MQTT Config */}
        {step === 3 && (
          <div className="space-y-4">
            <div>
              <p className="text-white font-medium mb-1">Configuração MQTT</p>
              <p className="text-gray-400 text-sm mb-4">Confirme o tópico MQTT e configure o firmware do seu dispositivo.</p>
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Tópico MQTT</label>
              <div className="flex gap-2">
                <input className="input-field flex-1 font-mono text-sm" value={form.mqtt_topic || generatedTopic}
                  onChange={(e) => update('mqtt_topic', e.target.value)} />
                <button onClick={handleCopy}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${copied ? 'bg-green-700 text-green-100' : 'btn-secondary'}`}>
                  {copied ? 'Copiado!' : 'Copiar'}
                </button>
              </div>
              <p className="text-gray-500 text-xs mt-2">
                Use este tópico no firmware do seu ESP32. Payload esperado: {'{"value": 23.5, "tick": 1, "timestamp": "2026-05-24T..."}'}
              </p>
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Observações</label>
              <textarea className="input-field resize-none h-24" placeholder="Localização física, observações de instalação..."
                value={form.notes} onChange={(e) => update('notes', e.target.value)} />
            </div>
            {/* Summary */}
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 space-y-2">
              <p className="text-white text-sm font-medium">Resumo</p>
              {[
                ['Tipo', DEVICE_TYPES.find((t) => t.value === form.device_type)?.label],
                ['Modelo', form.model || '—'],
                ['S/N', form.serial_number || '—'],
                ['Sala', selectedRoom?.name || '—'],
                ['Tópico', form.mqtt_topic || generatedTopic],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs">
                  <span className="text-gray-400">{k}</span>
                  <span className="text-gray-200 font-mono">{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-red-400 text-sm mt-4">{error}</p>}

        {/* Navigation */}
        <div className="flex gap-3 mt-6 pt-6 border-t border-gray-700">
          {step === 1 ? (
            <button onClick={() => navigate('/rooms')} className="flex-1 btn-secondary">Cancelar</button>
          ) : (
            <button onClick={handleBack} className="flex-1 btn-secondary">Anterior</button>
          )}
          {step < 3 ? (
            <button onClick={handleNext} className="flex-1 btn-primary">Próximo Passo</button>
          ) : (
            <button onClick={handleSubmit} disabled={loading} className="flex-1 btn-primary disabled:opacity-50">
              {loading ? 'Cadastrando...' : 'Cadastrar Dispositivo'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
