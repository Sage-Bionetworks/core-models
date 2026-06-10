import { useState, useEffect } from 'react'
import SchemaTable from './components/SchemaTable.jsx'
import DCCTable from './components/DCCTable.jsx'
import StatsPage from './components/StatsPage.jsx'
import sageLogo from './assets/sage-logo.svg'

const TABS = [
  { id: 'schemas', label: 'Registered Schemas' },
  { id: 'dcc',     label: 'DCC Links', count: 8 },
  { id: 'stats',   label: 'Insights' },
]

export default function App() {
  const [tab, setTab] = useState(() => {
    const hash = window.location.hash.slice(1)
    return TABS.find(t => t.id === hash)?.id ?? 'schemas'
  })

  // ── Data loading ───────────────────────────────────────────
  const [loadState, setLoadState] = useState('loading') // loading | ok | error
  const [errorMsg, setErrorMsg] = useState('')
  const [data, setData] = useState([])
  const [stagingResults, setStagingResults] = useState({})
  const [checksDate, setChecksDate] = useState('')

  async function loadData() {
    setLoadState('loading')
    try {
      const r = await fetch('./data.json')
      if (!r.ok) throw new Error('HTTP ' + r.status)
      const json = await r.json()
      setData(json)

      // Staging checks — non-fatal
      try {
        const sr = await fetch('./staging_checks.json')
        if (sr.ok) {
          const c = await sr.json()
          setChecksDate(c.checked_at || '')
          if (c.results) {
            setStagingResults(c.results)
          } else {
            // Legacy format: {passed: [...], failed: [...]}
            const results = {}
            for (const uri of (c.passed || [])) results[uri] = { ok: true }
            for (const uri of (c.failed || [])) results[uri] = { ok: false, error: 'Failed' }
            setStagingResults(results)
          }
        }
      } catch { /* staging check optional */ }

      setLoadState('ok')
    } catch (err) {
      setErrorMsg('Could not load data.json: ' + err.message)
      setLoadState('error')
    }
  }

  useEffect(() => { loadData() }, [])

  // ── Tab keyboard nav ───────────────────────────────────────
  function handleTabKey(e, id) {
    const ids = TABS.map(t => t.id)
    const idx = ids.indexOf(id)
    if (e.key === 'ArrowRight') { e.preventDefault(); setTab(ids[(idx + 1) % ids.length]) }
    if (e.key === 'ArrowLeft')  { e.preventDefault(); setTab(ids[(idx - 1 + ids.length) % ids.length]) }
  }

  function switchTab(id) {
    setTab(id)
    try { history.replaceState(null, null, '#' + id) } catch { /* ignore */ }
  }

  return (
    <div className="container">
      {/* ── Header ── */}
      <div className="top">
        <div className="title">
          <h1>Index of Data Models</h1>
          <div className="sage-byline">
            <img src={sageLogo} alt="Sage Bionetworks logo" className="sage-logo" />
            <span>Sage Bionetworks</span>
          </div>
          <p>
            Browse registered Synapse JSON schemas across Sage and jump directly to DCC data models,
            documentation, and portals.
            <br />
            <span className="muted" style={{ fontSize: 12 }}>
              Tip: Start with search or filter by organization, schema name, or version.
            </span>
          </p>
        </div>
        <div className="meta">
          <div className="badge">
            <span className="dot" />
            GitHub Pages · /docs · main
          </div>
          <div className="badge badge-count">
            {loadState === 'loading' && 'Loading…'}
            {loadState === 'ok' && `${data.length.toLocaleString()} rows loaded`}
            {loadState === 'error' && 'Error loading data'}
          </div>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="tabs" role="tablist" aria-label="Dashboard sections">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn${tab === t.id ? ' active' : ''}`}
            role="tab"
            aria-selected={tab === t.id}
            aria-controls={`tab-${t.id}`}
            tabIndex={tab === t.id ? 0 : -1}
            onClick={() => switchTab(t.id)}
            onKeyDown={e => handleTabKey(e, t.id)}
          >
            {t.label}
            {t.count !== undefined || t.id === 'schemas' ? (
              <span className="tab-badge">
                {t.id === 'schemas' ? (loadState === 'ok' ? data.length.toLocaleString() : '—') : t.count}
              </span>
            ) : null}
          </button>
        ))}
      </div>

      {/* ── Tab panels ── */}
      <div id="tab-schemas" role="tabpanel" aria-labelledby="tab-schemas" style={{ display: tab === 'schemas' ? 'block' : 'none' }}>
        {loadState === 'loading' && (
          <div className="panel">
            <div className="panel-body">
              <div className="state-overlay">
                <div className="spinner" /><p>Loading schema data…</p>
              </div>
            </div>
          </div>
        )}
        {loadState === 'error' && (
          <div className="panel">
            <div className="panel-body">
              <div className="state-overlay">
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <p>{errorMsg}</p>
                <button className="btn" onClick={loadData} type="button">↻ Retry</button>
              </div>
            </div>
          </div>
        )}
        {loadState === 'ok' && data.length === 0 && (
          <div className="panel">
            <div className="panel-body">
              <div className="state-overlay">
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <rect x="3" y="3" width="18" height="18" rx="3" /><line x1="9" y1="9" x2="15" y2="15" /><line x1="15" y1="9" x2="9" y2="15" />
                </svg>
                <p>No schema versions found. The data file is empty.</p>
              </div>
            </div>
          </div>
        )}
        {loadState === 'ok' && data.length > 0 && (
          <SchemaTable data={data} stagingResults={stagingResults} checksDate={checksDate} />
        )}
      </div>

      <div id="tab-dcc" role="tabpanel" aria-labelledby="tab-dcc" style={{ display: tab === 'dcc' ? 'block' : 'none' }}>
        <DCCTable />
      </div>

      <div id="tab-stats" role="tabpanel" aria-labelledby="tab-stats" style={{ display: tab === 'stats' ? 'block' : 'none' }}>
        <StatsPage data={data} loadState={loadState} />
      </div>
    </div>
  )
}
