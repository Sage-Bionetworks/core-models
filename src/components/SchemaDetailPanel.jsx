import { useState, useEffect } from 'react'
import StatusBadge from './StatusBadge.jsx'
import JsonModal from './JsonModal.jsx'
import { relDate, fmtDate } from '../utils/dates.js'
import { exportSchemaToExcel } from '../utils/exportExcel.js'

const PROD_BASE = 'https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/'
const SYNAPSE_BASE = 'https://www.synapse.org/#!Synapse:'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }
  return (
    <button className={`sha-copy${copied ? ' copied' : ''}`} type="button" onClick={copy}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

export default function SchemaDetailPanel({ row, stagingResults, checksDate, isPinned, onTogglePin, onClose }) {
  const [showJson, setShowJson] = useState(false)
  const [excelState, setExcelState] = useState('idle') // idle | loading | error
  const [propsState, setPropsState] = useState('idle') // idle | loading | loaded | error
  const [properties, setProperties] = useState(null)
  const [showProps, setShowProps] = useState(false)
  const [expandedEnums, setExpandedEnums] = useState(new Set())
  const [panelWidth, setPanelWidth] = useState(480)
  const resizeHandleRef = useRef(null)

  function onResizeMouseDown(e) {
    e.preventDefault()
    const startX = e.pageX
    const startW = panelWidth
    resizeHandleRef.current?.classList.add('dragging')
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    function onMove(e) {
      const newW = Math.max(300, Math.min(window.innerWidth * 0.9, startW - (e.pageX - startX)))
      setPanelWidth(newW)
    }
    function onUp() {
      resizeHandleRef.current?.classList.remove('dragging')
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }

  // Reset properties when a different row is selected
  useEffect(() => {
    setShowProps(false)
    setProperties(null)
    setPropsState('idle')
    setExpandedEnums(new Set())
  }, [row?.schema_id])

  // Close on Escape
  useEffect(() => {
    function handler(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  async function handleShowProps() {
    if (showProps) { setShowProps(false); return }
    setShowProps(true)
    if (properties) return // already loaded
    setPropsState('loading')
    try {
      const res = await fetch(PROD_BASE + `${row.organization_name}-${row.schema_name}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const schema = await res.json()
      const required = new Set(schema.required || [])
      const props = Object.entries(schema.properties || {}).map(([name, def]) => ({
        name,
        type: Array.isArray(def.type) ? def.type.join(' | ') : (def.type || ''),
        required: required.has(name),
        description: def.description || '',
        enumValues: def.enum || [],
      }))
      setProperties(props)
      setPropsState('loaded')
    } catch {
      setPropsState('error')
    }
  }

  if (!row) return null

  const uri = `${row.organization_name}-${row.schema_name}`
  const jsonUrl = PROD_BASE + uri
  const sr = stagingResults[uri]
  const pinned = isPinned(uri)

  return (
    <>
      <div className="panel-overlay" onClick={onClose} />
      <div className="detail-panel" role="dialog" aria-modal="true" aria-label="Schema details" style={{ width: panelWidth }}>
        <div className="panel-resize-handle" ref={resizeHandleRef} onMouseDown={onResizeMouseDown} />
        <div className="detail-panel-header">
          <div className="detail-panel-title">
            <span className="detail-schema-name" title={row.schema_name}>{row.schema_name}</span>
            <StatusBadge status={row.status} />
          </div>
          <div className="detail-panel-actions">
            <button
              className={`pin-btn${pinned ? ' pinned' : ''}`}
              type="button"
              title={pinned ? 'Unpin schema' : 'Pin schema'}
              onClick={() => onTogglePin(uri)}
            >
              {pinned ? '★' : '☆'}
            </button>
            <button className="btn" type="button" onClick={onClose} aria-label="Close panel">✕</button>
          </div>
        </div>

        <div className="detail-panel-body">
          <div className="detail-section">
            <div className="detail-section-title">Identity</div>
            <div className="detail-row">
              <span className="detail-label">Org Name</span>
              <span className="detail-value">{row.organization_name || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Org ID</span>
              <span className="detail-value">{row.organization_id || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Schema Name</span>
              <span className="detail-value">{row.schema_name || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Schema ID</span>
              <span className="detail-value">{row.schema_id || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Version</span>
              <span className="detail-value">{row.semantic_version || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Version ID</span>
              <span className="detail-value">{row.version_id || '—'}</span>
            </div>
          </div>

          <div className="detail-section">
            <div className="detail-section-title">Provenance</div>
            <div className="detail-row">
              <span className="detail-label">Created by</span>
              <span className="detail-value">{row.created_by || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Created on</span>
              <span className="detail-value">
                {row.created_on ? `${fmtDate(row.created_on)} (${relDate(row.created_on)})` : '—'}
              </span>
            </div>
            {row.json_sha256_hex && (
              <div className="detail-row">
                <span className="detail-label">SHA256</span>
                <span className="detail-value" style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>
                  {row.json_sha256_hex.substring(0, 16)}…
                  <CopyButton text={row.json_sha256_hex} />
                </span>
              </div>
            )}
          </div>

          {sr !== undefined && (
            <div className="detail-section">
              <div className="detail-section-title">
                Staging Check
                {checksDate && (
                  <span style={{ fontWeight: 400, color: 'var(--muted2)', fontSize: 11, marginLeft: 6 }}>
                    · checked {relDate(checksDate)}
                  </span>
                )}
              </div>
              <div className="detail-row">
                <span className="detail-label">Result</span>
                <span className="detail-value">
                  {sr.ok
                    ? <span style={{ color: 'rgba(22,163,74,0.95)', fontWeight: 700 }}>✓ Passed</span>
                    : <span style={{ color: 'rgba(185,28,28,0.92)', fontWeight: 700 }}>✗ Failed</span>
                  }
                </span>
              </div>
              {!sr.ok && sr.error && (
                <div className="detail-staging-error">{sr.error}</div>
              )}
            </div>
          )}

          <div className="detail-actions">
            <button
              className="btn btn--accent"
              type="button"
              onClick={() => setShowJson(true)}
            >
              View JSON
            </button>
            <button
              className={`btn btn--accent${showProps ? ' btn--active' : ''}`}
              type="button"
              onClick={handleShowProps}
            >
              {propsState === 'loading' ? '⏳ Loading…' : propsState === 'error' ? '⚠ Error' : 'View Properties'}
            </button>
            <button
              className={`btn btn--accent${excelState === 'loading' ? ' disabled' : ''}`}
              type="button"
              title="Export schema properties, enums, and validation rules to Excel"
              onClick={async () => {
                setExcelState('loading')
                try {
                  await exportSchemaToExcel(row.organization_name, row.schema_name)
                  setExcelState('idle')
                } catch (err) {
                  console.error('Excel export failed:', err)
                  setExcelState('error')
                  setTimeout(() => setExcelState('idle'), 3000)
                }
              }}
            >
              {excelState === 'loading' ? '⏳ Downloading…' : excelState === 'error' ? '⚠ Export failed' : '↓ Download Template (.xlsx)'}
            </button>
          </div>

          {showProps && propsState === 'loaded' && properties && (
            <div className="detail-section detail-props-table-wrap">
              <div className="detail-section-title">
                Properties
                <span style={{ fontWeight: 400, color: 'var(--muted2)', fontSize: 11, marginLeft: 6 }}>
                  · {properties.length} total, {properties.filter(p => p.required).length} required
                </span>
              </div>
              <table className="props-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Type</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {properties.map(p => {
                    const isExpanded = expandedEnums.has(p.name)
                    return (
                      <tr key={p.name} className={p.required ? 'prop-required' : ''}>
                        <td className="prop-name">
                          {p.name}
                          {p.required && <span className="prop-req-badge">req</span>}
                          {p.enumValues.length > 0 && (
                            <button
                              className={`prop-enum-badge prop-enum-btn${isExpanded ? ' expanded' : ''}`}
                              type="button"
                              title={isExpanded ? 'Hide options' : 'Show options'}
                              onClick={() => setExpandedEnums(prev => {
                                const next = new Set(prev)
                                next.has(p.name) ? next.delete(p.name) : next.add(p.name)
                                return next
                              })}
                            >
                              {p.enumValues.length} opts {isExpanded ? '▲' : '▼'}
                            </button>
                          )}
                          {isExpanded && (
                            <div className="prop-enum-list">
                              {p.enumValues.map(v => (
                                <span key={v} className="prop-enum-value">{String(v)}</span>
                              ))}
                            </div>
                          )}
                        </td>
                        <td className="prop-type">{p.type || '—'}</td>
                        <td className="prop-desc">{p.description || <span style={{ color: 'var(--muted2)' }}>—</span>}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {showJson && (
          <JsonModal url={jsonUrl} name={row.schema_name} onClose={() => setShowJson(false)} />
        )}
      </div>
    </>
  )
}
