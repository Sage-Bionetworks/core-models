import { useMemo } from 'react'

const PUBLISHED_ORGS = [
  { id: 'MC2Center',          label: 'MC2' },
  { id: 'org.synapse.nf',     label: 'NF' },
  { id: 'HTAN2Organization',  label: 'HTAN2' },
  { id: 'sage.schemas.ad',    label: 'ADKP' },
  { id: 'sage.schemas.elite', label: 'ELITE' },
  { id: 'NAMhub',             label: 'NAMHub' },
]

// One accent colour per bar — cycles through a curated palette
const BAR_COLORS = [
  '#6366f1', // indigo
  '#06b6d4', // cyan
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ec4899', // pink
  '#8b5cf6', // violet
]

export default function StatsPage({ data, loadState }) {
  const counts = useMemo(() => {
    const map = {}
    for (const row of data) {
      if (map[row.organization_name] === undefined) map[row.organization_name] = 0
      map[row.organization_name]++
    }
    return PUBLISHED_ORGS.map(org => ({ ...org, count: map[org.id] ?? 0 }))
  }, [data])

  const maxCount = Math.max(...counts.map(o => o.count), 1)
  const total    = counts.reduce((s, o) => s + o.count, 0)

  if (loadState === 'loading') {
    return (
      <div className="panel">
        <div className="panel-body">
          <div className="state-overlay">
            <div className="spinner" /><p>Loading schema data…</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="panel-body stats-page">

        {/* ── Header ── */}
        <div className="stats-header">
          <div>
            <div className="stats-title">Published Schema Statistics</div>
            <div className="stats-subtitle">
              Schema counts per published organization · {total.toLocaleString()} total schemas
            </div>
          </div>
        </div>

        {/* ── Bar chart ── */}
        <div className="stats-chart-wrap">
          <div className="stats-chart">
            {counts.map((org, i) => {
              const pct = maxCount > 0 ? (org.count / maxCount) * 100 : 0
              return (
                <div key={org.id} className="stats-bar-group">
                  {/* Count label above bar */}
                  <div className="stats-bar-value">{org.count.toLocaleString()}</div>

                  {/* Bar */}
                  <div className="stats-bar-track">
                    <div
                      className="stats-bar-fill"
                      style={{ height: `${pct}%`, background: BAR_COLORS[i % BAR_COLORS.length] }}
                      title={`${org.label}: ${org.count} schemas`}
                    />
                  </div>

                  {/* X-axis label */}
                  <div className="stats-bar-label">{org.label}</div>
                </div>
              )
            })}
          </div>

          {/* Y-axis guide lines */}
          <div className="stats-gridlines" aria-hidden="true">
            {[100, 75, 50, 25, 0].map(p => (
              <div key={p} className="stats-gridline" style={{ bottom: `${p}%` }}>
                <span className="stats-gridline-label">
                  {p === 0 ? 0 : Math.round((p / 100) * maxCount)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Summary cards ── */}
        <div className="stats-cards">
          {counts.map((org, i) => (
            <div key={org.id} className="stats-card">
              <div
                className="stats-card-bar"
                style={{ background: BAR_COLORS[i % BAR_COLORS.length] }}
              />
              <div className="stats-card-body">
                <div className="stats-card-label">{org.label}</div>
                <div className="stats-card-id">{org.id}</div>
                <div className="stats-card-count">{org.count.toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}
