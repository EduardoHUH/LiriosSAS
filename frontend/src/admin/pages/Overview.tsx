import { useEffect, useState } from 'react'
import { getOverview } from '../api/dashboard'
import { getErrorMessage } from '../../api/errors'
import { formatMoney } from '../../utils/formatMoney'
import type { DashboardOverview } from '../types'
import '../admin-shared.css'

type LoadState = 'loading' | 'loaded' | 'error'

export default function Overview() {
  const [data, setData] = useState<DashboardOverview | null>(null)
  const [state, setState] = useState<LoadState>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    getOverview()
      .then((overview) => {
        setData(overview)
        setState('loaded')
      })
      .catch((err: unknown) => {
        setError(getErrorMessage(err))
        setState('error')
      })
  }, [])

  if (state === 'loading') {
    return <p className="admin-status">Cargando…</p>
  }

  if (state === 'error' || !data) {
    return <p className="admin-status admin-status--error">{error}</p>
  }

  const tiles: { label: string; value: string | number }[] = [
    { label: 'Citas hoy', value: data.appointments_today },
    { label: 'Próximas 7 días', value: data.upcoming_appointments_next_7_days },
    { label: 'Ingresos este mes', value: formatMoney(data.revenue_this_month) },
    { label: 'Completadas este mes', value: data.completed_appointments_this_month },
    { label: 'Canceladas este mes', value: data.cancellations_this_month },
    { label: 'Pagos pendientes', value: data.pending_payments },
    { label: 'Reembolsos pendientes', value: data.refund_pending_payments },
  ]

  return (
    <div>
      <h1 className="admin-page-title">Resumen</h1>
      <div className="admin-stat-grid">
        {tiles.map((tile) => (
          <div key={tile.label} className="admin-stat-tile">
            <span className="admin-stat-tile__label">{tile.label}</span>
            <span className="admin-stat-tile__value">{tile.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
