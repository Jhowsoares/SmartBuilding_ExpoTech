import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { getConsumption } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const PERIODS = [
  { value: '24h', label: 'Últimas 24h' },
  { value: '7d', label: 'Últimos 7 dias' },
  { value: '30d', label: 'Últimos 30 dias' },
]

const COST_KWH = 0.85 // R$ per kWh (example tariff)

function StatCard({ label, value, sub, color = 'blue' }) {
  const colors = {
    blue: 'text-sb-primary',
    green: 'text-green-400',
    yellow: 'text-sb-tertiary',
  }
  return (
    <div className="card p-5">
      <p className="text-sb-outline text-sm">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${colors[color]}`}>{value}</p>
      {sub && <p className="text-xs text-sb-outline opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card p-3 text-sm border border-sb-border">
      <p className="text-sb-outline mb-1">{label}</p>
      <p className="text-sb-primary font-semibold">{payload[0]?.value?.toFixed(2)} kWh</p>
    </div>
  )
}

function downloadCSV(data, period) {
  if (!data.length) return
  const keys = Object.keys(data[0])
  const header = keys.join(',')
  const rows = data.map((row) => keys.map((k) => row[k] ?? '').join(',')).join('\n')
  const csv = `${header}\n${rows}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `consumo_${period}_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function ReportsPage() {
  const [period, setPeriod] = useState('24h')
  const [data, setData] = useState([])
  const [apiTotals, setApiTotals] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getConsumption(period)
      const raw = res.data
      // API returns { data: { total_kwh, custo_brl, breakdown_by_hour: [...] } }
      const inner = raw?.data ?? raw
      const breakdown = Array.isArray(inner?.breakdown_by_hour)
        ? inner.breakdown_by_hour
        : Array.isArray(inner)
          ? inner
          : []

      if (breakdown.length > 0) {
        // Use real data — map breakdown_by_hour into chart-friendly format
        const mapped = breakdown.map((h) => ({
          label: h.hora
            ? new Date(h.hora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
            : (h.label || h.time || ''),
          kwh: +(h.kwh_estimado ?? h.kwh ?? h.value ?? 0),
          avg_temp: h.avg_temp_celsius ?? null,
        }))
        setData(mapped)
        // Prefer backend totals when available
        if (inner?.total_kwh != null) {
          setApiTotals({ totalKwh: inner.total_kwh, costBrl: inner.custo_brl ?? 0 })
        }
      } else {
        setData(generateMockData(period))
        setApiTotals(null)
        setError('Sem dados reais — exibindo estimativa.')
      }
    } catch (_) {
      setData(generateMockData(period))
      setApiTotals(null)
      setError('Usando dados de exemplo — API não disponível.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [period])

  const totalKwh = apiTotals?.totalKwh ?? data.reduce((sum, d) => sum + (d.kwh || 0), 0)
  const totalCost = apiTotals?.costBrl ?? (totalKwh * COST_KWH)
  const avgKwh = data.length > 0 ? totalKwh / data.length : 0

  const chartData = data.map((d) => ({
    label: d.label || '',
    kWh: +(d.kwh || 0).toFixed ? +(d.kwh || 0) : 0,
  }))

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex rounded-lg overflow-hidden border border-sb-border">
          {PERIODS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setPeriod(value)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                period === value
                  ? 'bg-sb-primary-btn text-white'
                  : 'bg-sb-card text-sb-outline hover:text-sb-on-surface hover:bg-sb-card-high'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={() => downloadCSV(data, period)}
          disabled={data.length === 0}
          className="btn-secondary flex items-center gap-2 text-sm disabled:opacity-50"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Exportar CSV
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-yellow-900/30 border border-yellow-700 rounded-lg text-yellow-300 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Consumo Total"
          value={`${totalKwh.toFixed(2)} kWh`}
          sub={PERIODS.find((p) => p.value === period)?.label}
          color="blue"
        />
        <StatCard
          label="Custo Estimado"
          value={`R$ ${totalCost.toFixed(2)}`}
          sub={`Tarifa: R$ ${COST_KWH}/kWh`}
          color="green"
        />
        <StatCard
          label="Média por Período"
          value={`${avgKwh.toFixed(2)} kWh`}
          sub="por intervalo"
          color="yellow"
        />
      </div>

      {/* Chart */}
      <div className="card p-6">
        <h2 className="text-sb-on-surface font-semibold mb-6">Consumo de Energia</h2>
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-sb-outline">
            <p>Sem dados de consumo disponíveis</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#424754" />
              <XAxis
                dataKey="label"
                stroke="#8c909f"
                tick={{ fill: '#c2c6d6', fontSize: 11 }}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#8c909f"
                tick={{ fill: '#c2c6d6', fontSize: 11 }}
                unit=" kWh"
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="kWh" fill="#4d8eff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function generateMockData(period) {
  const now = new Date()
  if (period === '24h') {
    return Array.from({ length: 24 }, (_, i) => ({
      label: `${String(i).padStart(2, '0')}:00`,
      kwh: +(3 + Math.random() * 5).toFixed(2),
    }))
  }
  if (period === '7d') {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(now)
      d.setDate(d.getDate() - (6 - i))
      return {
        label: d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric' }),
        kwh: +(50 + Math.random() * 40).toFixed(2),
      }
    })
  }
  return Array.from({ length: 30 }, (_, i) => {
    const d = new Date(now)
    d.setDate(d.getDate() - (29 - i))
    return {
      label: d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' }),
      kwh: +(40 + Math.random() * 60).toFixed(2),
    }
  })
}
