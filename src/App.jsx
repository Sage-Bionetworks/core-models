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
          <a
            href="https://go.coremodels.io/app/9beb8916977c46149f7a0180b50d41ba"
            target="_blank"
            rel="noopener noreferrer"
            className="coremodels-btn"
          >
            <svg className="coremodels-btn-logo" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <defs>
                <linearGradient id="cm-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2e6fa3" />
                  <stop offset="100%" stopColor="#6ab54e" />
                </linearGradient>
              </defs>
              <path fill="url(#cm-grad)" d="M146.208,141.577c-2.973,5.16-9.712,9.054-15.674,9.054h-37.56c-5.963,0-12.703-3.894-15.677-9.057 l-18.773-32.525c-2.979-5.157-2.983-12.937-0.009-18.096l18.784-32.531c2.977-5.156,9.716-9.045,15.675-9.045h37.56 c5.958,0,12.697,3.889,15.674,9.045L158.5,79.5l-6.954,12.89L135.38,64.748c-0.786-1.362-3.314-2.829-4.846-2.829h-37.56 c-1.502,0-4.063,1.476-4.806,2.77L69.382,97.223c-0.751,1.298-0.75,4.257,0,5.556l18.784,32.528 c0.766,1.325,3.283,2.782,4.809,2.782h37.56c1.529,0,4.05-1.457,4.816-2.783l18.754-32.484l1.72-3.19l-0.003-0.004l0.867-1.649 l3.635-6.703l17.363-32.196c1.333-2.477,1.29-5.408-0.116-7.839l-13.893-24.063c-2.625-4.558-9.546-8.553-14.812-8.553H74.649 c-5.265,0-12.186,3.993-14.811,8.544L22.729,91.451c-2.631,4.558-2.631,12.547-0.001,17.098l37.11,64.28 c2.625,4.554,9.546,8.547,14.811,8.547h74.217c5.259,0,12.18-3.994,14.812-8.548l13.834-23.966l0.544-1.183 c1.546-2.679,1.548-7.947,0.004-10.637l-11.265-19.15L173.75,105l15.15,25.739c3.742,6.477,3.824,16.262,0.221,22.853l-0.563,1.222 L174.544,179.1c-4.891,8.449-15.929,14.818-25.678,14.818H74.649c-9.766,0-20.802-6.371-25.671-14.819L11.864,114.82 c-4.876-8.444-4.877-21.187,0-29.64l37.116-64.273c4.865-8.45,15.901-14.825,25.67-14.825h74.217 c9.756,0,20.795,6.373,25.677,14.825l13.885,24.061c3.6,6.228,3.711,13.729,0.297,20.064l-20.234,35.677" />
            </svg>
            Open in CoreModels
          </a>
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
