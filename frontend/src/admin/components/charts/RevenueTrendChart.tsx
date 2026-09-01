import { useRef, useState } from 'react'
import { niceTicks } from './niceTicks'
import { formatMoney } from '../../../utils/formatMoney'
import type { RevenueTrendPoint, TrendGroupBy } from '../../types'
import './charts.css'

interface RevenueTrendChartProps {
  data: RevenueTrendPoint[]
  groupBy: TrendGroupBy
}

const WIDTH = 720
const HEIGHT = 260
const PADDING = { top: 16, right: 16, bottom: 32, left: 64 }

function parseLocalDate(period: string): Date {
  return new Date(`${period}T00:00:00`)
}

function formatPeriodLabel(period: string, groupBy: TrendGroupBy): string {
  const date = parseLocalDate(period)
  if (groupBy === 'month') {
    return new Intl.DateTimeFormat('es-HN', { month: 'short', year: '2-digit' }).format(date)
  }
  return new Intl.DateTimeFormat('es-HN', { day: 'numeric', month: 'short' }).format(date)
}

export default function RevenueTrendChart({ data, groupBy }: RevenueTrendChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)
  const [showTable, setShowTable] = useState(false)
  const svgRef = useRef<SVGSVGElement>(null)

  if (data.length === 0) {
    return <p className="admin-status">No hay ingresos registrados en este periodo.</p>
  }

  const values = data.map((point) => Number(point.revenue))
  const maxValue = Math.max(...values, 0)
  const ticks = niceTicks(maxValue)
  const yMax = ticks[ticks.length - 1]

  const plotWidth = WIDTH - PADDING.left - PADDING.right
  const plotHeight = HEIGHT - PADDING.top - PADDING.bottom

  const xFor = (index: number) =>
    data.length === 1 ? PADDING.left + plotWidth / 2 : PADDING.left + (index / (data.length - 1)) * plotWidth
  const yFor = (value: number) => PADDING.top + plotHeight - (value / yMax) * plotHeight

  const linePath = data
    .map((point, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i)} ${yFor(Number(point.revenue))}`)
    .join(' ')
  const areaPath = `${linePath} L ${xFor(data.length - 1)} ${PADDING.top + plotHeight} L ${xFor(0)} ${PADDING.top + plotHeight} Z`

  function handleMouseMove(event: React.MouseEvent<SVGSVGElement>) {
    const svg = svgRef.current
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const relativeX = ((event.clientX - rect.left) / rect.width) * WIDTH
    let nearest = 0
    let nearestDistance = Infinity
    for (let i = 0; i < data.length; i++) {
      const distance = Math.abs(xFor(i) - relativeX)
      if (distance < nearestDistance) {
        nearestDistance = distance
        nearest = i
      }
    }
    setHoverIndex(nearest)
  }

  const hovered = hoverIndex !== null ? data[hoverIndex] : null
  const labelStep = Math.max(1, Math.ceil(data.length / 6))

  return (
    <div className="chart">
      <button type="button" className="chart__table-toggle" onClick={() => setShowTable((v) => !v)}>
        {showTable ? 'Ver gráfico' : 'Ver como tabla'}
      </button>

      {showTable ? (
        <table className="chart__table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th>Ingresos</th>
            </tr>
          </thead>
          <tbody>
            {data.map((point) => (
              <tr key={point.period}>
                <td>{formatPeriodLabel(point.period, groupBy)}</td>
                <td>{formatMoney(point.revenue)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <svg
          ref={svgRef}
          className="chart__svg"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverIndex(null)}
          role="img"
          aria-label="Tendencia de ingresos"
        >
          {ticks.map((tick) => (
            <g key={tick}>
              <line
                x1={PADDING.left}
                x2={WIDTH - PADDING.right}
                y1={yFor(tick)}
                y2={yFor(tick)}
                className="chart__gridline"
              />
              <text x={PADDING.left - 10} y={yFor(tick)} className="chart__axis-label" textAnchor="end" dy="0.32em">
                {formatMoney(String(tick))}
              </text>
            </g>
          ))}

          {data.map((point, i) =>
            i % labelStep === 0 || i === data.length - 1 ? (
              <text
                key={point.period}
                x={xFor(i)}
                y={HEIGHT - PADDING.bottom + 20}
                className="chart__axis-label"
                textAnchor="middle"
              >
                {formatPeriodLabel(point.period, groupBy)}
              </text>
            ) : null,
          )}

          <path d={areaPath} className="chart__area" />
          <path d={linePath} className="chart__line" />

          {data.map((point, i) => (
            <circle key={point.period} cx={xFor(i)} cy={yFor(Number(point.revenue))} r={4} className="chart__dot" />
          ))}

          {hoverIndex !== null && (
            <line
              x1={xFor(hoverIndex)}
              x2={xFor(hoverIndex)}
              y1={PADDING.top}
              y2={PADDING.top + plotHeight}
              className="chart__crosshair"
            />
          )}
        </svg>
      )}

      {hovered && (
        <div className="chart__tooltip">
          <strong>{formatMoney(hovered.revenue)}</strong>
          <span>{formatPeriodLabel(hovered.period, groupBy)}</span>
        </div>
      )}
    </div>
  )
}
