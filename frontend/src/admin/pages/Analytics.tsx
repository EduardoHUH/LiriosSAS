import { useEffect, useState } from 'react'
import { getRevenueTrend, getServicePopularity } from '../api/dashboard'
import { getErrorMessage } from '../../api/errors'
import { formatMoney } from '../../utils/formatMoney'
import { toDateParam } from '../../utils/formatDateTime'
import RevenueTrendChart from '../components/charts/RevenueTrendChart'
import BarChart from '../components/charts/BarChart'
import type { RevenueTrendPoint, ServicePopularity, TrendGroupBy } from '../types'
import '../admin-shared.css'
import './Analytics.css'

type LoadState = 'loading' | 'loaded' | 'error'

const RANGE_PRESETS = [
  { label: 'Últimos 7 días', days: 7 },
  { label: 'Últimos 30 días', days: 30 },
  { label: 'Últimos 90 días', days: 90 },
]

function rangeFromDays(days: number): { date_from: string; date_to: string } {
  const today = new Date()
  const from = new Date(today)
  from.setDate(from.getDate() - (days - 1))
  return { date_from: toDateParam(from), date_to: toDateParam(today) }
}

export default function Analytics() {
  const [rangeDays, setRangeDays] = useState(30)
  const [groupBy, setGroupBy] = useState<TrendGroupBy>('day')
  const [revenueData, setRevenueData] = useState<RevenueTrendPoint[]>([])
  const [popularityData, setPopularityData] = useState<ServicePopularity[]>([])
  const [state, setState] = useState<LoadState>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setState('loading')
    const range = rangeFromDays(rangeDays)

    Promise.all([
      getRevenueTrend({ ...range, group_by: groupBy }),
      getServicePopularity(range),
    ])
      .then(([revenue, popularity]) => {
        if (cancelled) return
        setRevenueData(revenue)
        setPopularityData(popularity)
        setState('loaded')
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(getErrorMessage(err))
        setState('error')
      })

    return () => {
      cancelled = true
    }
  }, [rangeDays, groupBy])

  const totalRevenue = popularityData.reduce((sum, row) => sum + Number(row.revenue), 0)

  return (
    <div>
      <h1 className="admin-page-title">Analítica</h1>

      <div className="analytics__filters">
        <div className="admin-field">
          <label htmlFor="range">Periodo</label>
          <select id="range" value={rangeDays} onChange={(e) => setRangeDays(Number(e.target.value))}>
            {RANGE_PRESETS.map((preset) => (
              <option key={preset.days} value={preset.days}>
                {preset.label}
              </option>
            ))}
          </select>
        </div>
        <div className="admin-field">
          <label htmlFor="group_by">Agrupar por</label>
          <select id="group_by" value={groupBy} onChange={(e) => setGroupBy(e.target.value as TrendGroupBy)}>
            <option value="day">Día</option>
            <option value="week">Semana</option>
            <option value="month">Mes</option>
          </select>
        </div>
      </div>

      {state === 'error' && <p className="admin-status admin-status--error">{error}</p>}

      <div className="analytics__panels" style={{ opacity: state === 'loading' ? 0.5 : 1 }}>
        <section className="admin-panel">
          <h2 className="analytics__panel-title">Tendencia de ingresos</h2>
          <p className="analytics__panel-subtitle">Pagos confirmados, agrupados por {groupBy === 'day' ? 'día' : groupBy === 'week' ? 'semana' : 'mes'}.</p>
          <RevenueTrendChart data={revenueData} groupBy={groupBy} />
        </section>

        <section className="admin-panel">
          <h2 className="analytics__panel-title">Citas completadas por servicio</h2>
          <p className="analytics__panel-subtitle">Número de citas completadas en el periodo.</p>
          <BarChart
            data={popularityData.map((row) => ({ label: row.service_name, value: row.appointment_count }))}
            colorVar="var(--color-blush)"
            formatValue={(value) => String(value)}
            emptyMessage="No hay citas completadas en este periodo."
          />
        </section>

        <section className="admin-panel">
          <h2 className="analytics__panel-title">Ingresos por servicio</h2>
          <p className="analytics__panel-subtitle">
            Suma de precios de citas completadas (no solo pagos en línea) — total: {formatMoney(String(totalRevenue))}.
          </p>
          <BarChart
            data={popularityData.map((row) => ({ label: row.service_name, value: Number(row.revenue) }))}
            colorVar="var(--color-sage)"
            formatValue={(value) => formatMoney(String(value))}
            emptyMessage="No hay citas completadas en este periodo."
          />
        </section>
      </div>
    </div>
  )
}
