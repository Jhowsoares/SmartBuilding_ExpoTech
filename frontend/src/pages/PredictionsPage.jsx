import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { getPredictions24h } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div className="card p-3 text-sm">
      <p className="text-gray-400 mb-1">{label}</p>
      <p className="text-blue-400 font-semibold">{d?.predicted?.toFixed(2)} kWh</p>
      {d?.confidence != null && (
        <p className="text-gray-400 text-xs">Confiança: {(d.confidence * 100).toFixed(0)}%</p>
      )}
    </div>
  )
}

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100)
  const color = pct >= 75 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-bold text-white w-10 text-right">{pct}%</span>
    </div>
  )
}

export default function PredictionsPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [meta, setMeta] = useState({ avgConfidence: 0, totalKwh: 0, peakHour: null })
  const [usingMock, setUsingMock] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await getPredictions24h()
      const raw = res.data
      const arr = Array.isArray(raw) ? raw : raw?.predictions || raw?.data || raw?.items || []
      if (arr.length > 0) {
        processData(arr)
      } else {
        processData(generateMock())
        setUsingMock(true)
      }
    } catch (_) {
      processData(generateMock())
      setUsingMock(true)
    } finally {
      setLoading(false)
    }
  }

  const processData = (arr) => {
    const normalized = arr.map((d, i) => ({
      hour: d.hour || d.label || d.time || `${String(i).padStart(2, '0')}:00`,
      predicted: +(d.predicted || d.value || d.kwh || d.consumption || 0),
      confidence: d.confidence ?? d.confidence_score ?? 0.75,
    }))
    setData(normalized)

    const totalKwh = normalized.reduce((s, d) => s + d.predicted, 0)
    const avgConf = normalized.reduce((s, d) => s + d.confidence, 0) / (normalized.length || 1)
    const peak = normalized.reduce((a, b) => (b.predicted > a.predicted ? b : a), normalized[0])
    setMeta({ totalKwh, avgConfidence: avgConf, peakHour: peak?.hour || null })
  }

  useEffect(() => {
    fetchData()
  }, [])

  const recommendations = buildRecommendations(meta, data)

  return (
    <div className="space-y-6">
      {usingMock && (
        <div className="flex items-center gap-2 px-4 py-3 bg-yellow-900/30 border border-yellow-700 rounded-lg text-yellow-300 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Dados de demonstração — API de predições não disponível.
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-5">
          <p className="text-gray-400 text-sm">Consumo Previsto (24h)</p>
          <p className="text-3xl font-bold text-blue-400 mt-1">
            {meta.totalKwh.toFixed(1)} kWh
          </p>
        </div>
        <div className="card p-5">
          <p className="text-gray-400 text-sm mb-2">Confiança Média do Modelo</p>
          <ConfidenceBar value={meta.avgConfidence} />
        </div>
        <div className="card p-5">
          <p className="text-gray-400 text-sm">Pico Previsto</p>
          <p className="text-3xl font-bold text-yellow-400 mt-1">
            {meta.peakHour || '--'}
          </p>
          <p className="text-gray-500 text-xs mt-1">Hora de maior consumo</p>
        </div>
      </div>

      {/* Chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-white font-semibold">Previsão de Consumo — Próximas 24h</h2>
            <p className="text-gray-400 text-sm mt-0.5">Baseado em padrões históricos e condições atuais</p>
          </div>
          <button
            onClick={fetchData}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Atualizar
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-72">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="hour"
                stroke="#6B7280"
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                interval={2}
              />
              <YAxis
                stroke="#6B7280"
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                unit=" kWh"
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                y={meta.totalKwh / (data.length || 1)}
                stroke="#F59E0B"
                strokeDasharray="4 4"
                label={{ value: 'Média', fill: '#F59E0B', fontSize: 11 }}
              />
              <Bar dataKey="predicted" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Recommendations */}
      <div className="card p-6">
        <h2 className="text-white font-semibold mb-4">Recomendações</h2>
        {recommendations.length === 0 ? (
          <p className="text-gray-500 text-sm">Sem recomendações no momento.</p>
        ) : (
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <div
                key={i}
                className={`flex items-start gap-3 p-4 rounded-xl border ${
                  rec.type === 'warning'
                    ? 'bg-yellow-900/20 border-yellow-700'
                    : rec.type === 'success'
                    ? 'bg-green-900/20 border-green-700'
                    : 'bg-blue-900/20 border-blue-700'
                }`}
              >
                <div className={`mt-0.5 flex-shrink-0 ${
                  rec.type === 'warning' ? 'text-yellow-400'
                    : rec.type === 'success' ? 'text-green-400' : 'text-blue-400'
                }`}>
                  {rec.type === 'warning' ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : rec.type === 'success' ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  )}
                </div>
                <div>
                  <p className={`text-sm font-medium ${
                    rec.type === 'warning' ? 'text-yellow-300'
                      : rec.type === 'success' ? 'text-green-300' : 'text-blue-300'
                  }`}>{rec.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{rec.body}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function buildRecommendations(meta, data) {
  const recs = []
  if (!data.length) return recs

  if (meta.peakHour) {
    recs.push({
      type: 'warning',
      title: `Pico de consumo esperado às ${meta.peakHour}`,
      body: 'Considere reduzir o número de dispositivos ativos nesse período para economizar energia.',
    })
  }

  if (meta.avgConfidence < 0.6) {
    recs.push({
      type: 'info',
      title: 'Confiança do modelo abaixo do ideal',
      body: 'O modelo precisa de mais dados históricos para gerar previsões mais precisas.',
    })
  }

  const nightData = data.filter((d) => {
    const h = parseInt(d.hour?.split(':')[0] || '0', 10)
    return h >= 22 || h < 6
  })
  const nightAvg = nightData.length
    ? nightData.reduce((s, d) => s + d.predicted, 0) / nightData.length
    : 0
  const dayAvg = meta.totalKwh / (data.length || 1)
  if (nightAvg > dayAvg * 0.5) {
    recs.push({
      type: 'warning',
      title: 'Consumo noturno elevado',
      body: 'Verifique dispositivos em standby durante a madrugada — possível desperdício de energia.',
    })
  }

  if (meta.avgConfidence >= 0.75) {
    recs.push({
      type: 'success',
      title: 'Modelo operando com alta confiança',
      body: 'As previsões são confiáveis. Use-as para planejar a operação dos sistemas HVAC.',
    })
  }

  return recs
}

function generateMock() {
  return Array.from({ length: 24 }, (_, i) => {
    const isDay = i >= 7 && i <= 19
    const isPeak = (i >= 9 && i <= 11) || (i >= 14 && i <= 17)
    const base = isDay ? (isPeak ? 7 : 5) : 2
    return {
      hour: `${String(i).padStart(2, '0')}:00`,
      predicted: +(base + Math.random() * 2).toFixed(2),
      confidence: +(0.65 + Math.random() * 0.3).toFixed(2),
    }
  })
}
