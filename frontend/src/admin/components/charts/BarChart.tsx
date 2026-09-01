import { useState } from 'react'
import { niceTicks } from './niceTicks'
import './charts.css'

interface BarChartDatum {
  label: string
  value: number
}

interface BarChartProps {
  data: BarChartDatum[]
  colorVar: string
  formatValue: (value: number) => string
  emptyMessage: string
}

export default function BarChart({ data, colorVar, formatValue, emptyMessage }: BarChartProps) {
  const [hoverLabel, setHoverLabel] = useState<string | null>(null)
  const [showTable, setShowTable] = useState(false)

  if (data.length === 0) {
    return <p className="admin-status">{emptyMessage}</p>
  }

  const maxValue = Math.max(...data.map((d) => d.value), 0)
  const ticks = niceTicks(maxValue)
  const scaleMax = ticks[ticks.length - 1] || 1

  return (
    <div className="chart">
      <button type="button" className="chart__table-toggle" onClick={() => setShowTable((v) => !v)}>
        {showTable ? 'Ver gráfico' : 'Ver como tabla'}
      </button>

      {showTable ? (
        <table className="chart__table">
          <thead>
            <tr>
              <th>Servicio</th>
              <th>Valor</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.label}>
                <td>{row.label}</td>
                <td>{formatValue(row.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="bar-chart">
          {data.map((row) => {
            const widthPercent = (row.value / scaleMax) * 100
            const isHovered = hoverLabel === row.label
            return (
              <div
                key={row.label}
                className="bar-chart__row"
                onMouseEnter={() => setHoverLabel(row.label)}
                onMouseLeave={() => setHoverLabel(null)}
                onFocus={() => setHoverLabel(row.label)}
                onBlur={() => setHoverLabel(null)}
                tabIndex={0}
              >
                <span className="bar-chart__label" title={row.label}>
                  {row.label}
                </span>
                <div className="bar-chart__track">
                  <div
                    className={`bar-chart__fill${isHovered ? ' bar-chart__fill--hover' : ''}`}
                    style={{ width: `${widthPercent}%`, background: colorVar }}
                  />
                </div>
                <span className="bar-chart__value">{formatValue(row.value)}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
