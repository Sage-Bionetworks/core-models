import { useState, useRef, useCallback, useEffect } from 'react'
import StatusBadge from './StatusBadge.jsx'
import JsonModal from './JsonModal.jsx'
import Popover from './Popover.jsx'
import FilterChips from './FilterChips.jsx'
import SchemaDetailPanel from './SchemaDetailPanel.jsx'
import usePinnedSchemas from '../hooks/usePinnedSchemas.js'
import { relDate, fmtDate } from '../utils/dates.js'
import { exportListToExcel } from '../utils/exportExcel.js'

const PROD_BASE = 'https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/'
const PAGE_SIZES = [10, 25, 50, 100]

// ─── SHA cell ────────────────────────────────────────────────
function ShaCell({ hex }) {
  const [copied, setCopied] = useState(false)
  if (!hex) return <span className="muted">—</span>
  function copy() {
    navigator.clipboard.writeText(hex).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }
  return (
    <div className="sha-wrap">
      <span className="sha-text" title={hex}>{hex.substring(0, 10)}…</span>
      <button className={`sha-copy${copied ? ' copied' : ''}`} onClick={copy} type="button">
        {copied ? 'Copied!' : 'Copy'}
      </button>
    </div>
  )
}

// ─── Staging popover content ──────────────────────────────────
function StagingPopoverContent({ result, checksDate }) {
  return (
    <>
      <div className="popover-row">
        <span className="popover-label">Staging check</span>
        {result.ok
          ? <span style={{ color: 'rgba(22,163,74,0.95)', fontWeight: 700 }}>✓ Passed</span>
          : <span style={{ color: 'rgba(185,28,28,0.92)', fontWeight: 700 }}>✗ Failed</span>
        }
      </div>
      {!result.ok && (
        <div className="popover-row">
          <span className="popover-label">Error</span>
          <span className="popover-val" style={{ maxWidth: 240, whiteSpace: 'normal', wordBreak: 'break-word', textAlign: 'left' }}>
            {result.error || 'Unknown error'}
          </span>
        </div>
      )}
      {checksDate && (
        <div className="popover-row">
          <span className="popover-label">Checked</span>
          <span className="popover-val">{relDate(checksDate)}</span>
        </div>
      )}
    </>
  )
}

// ─── A single row ─────────────────────────────────────────────
function SchemaRow({ row, stagingResults, checksDate, isPinned, onTogglePin, isFocused, rowRef, onRowClick }) {
  const [stagingOpen, setStagingOpen] = useState(false)
  const [modal, setModal] = useState(false)
  const stagingBtnRef = useRef(null)

  const uri = `${row.organization_name}-${row.schema_name}`
  const url = PROD_BASE + uri
  const sr = stagingResults[uri]
  const pinned = isPinned(uri)

  return (
    <tr
      ref={rowRef}
      className={`schema-row${isFocused ? ' focused' : ''}`}
      tabIndex={isFocused ? 0 : -1}
      onClick={() => onRowClick(row)}
    >
      {/* Pin cell */}
      <td className="pin-cell" onClick={e => { e.stopPropagation(); onTogglePin(uri) }}>
        <button
          className={`pin-btn${pinned ? ' pinned' : ''}`}
          type="button"
          title={pinned ? 'Unpin' : 'Pin this schema'}
          tabIndex={-1}
        >
          {pinned ? '★' : '☆'}
        </button>
      </td>
      <td title={row.organization_name}>{row.organization_name}</td>
      <td title={row.schema_name}>{row.schema_name}</td>
      <td><StatusBadge status={row.status} /></td>
      <td>{row.semantic_version}</td>
      <td data-order={row.created_on ? new Date(row.created_on).getTime() : 0}>
        <span className="date-cell">
          {relDate(row.created_on)}
          <span className="date-abs">{fmtDate(row.created_on)}</span>
        </span>
      </td>
      {/* Staging check */}
      <td style={{ overflow: 'visible' }} onClick={e => e.stopPropagation()}>
        {sr !== undefined && (
          <>
            <button
              ref={stagingBtnRef}
              className={sr.ok ? 'staging-ok' : 'staging-fail'}
              type="button"
              title={sr.ok ? 'Passed staging check' : 'Failed — click for details'}
              onClick={() => setStagingOpen(v => !v)}
            >
              {sr.ok ? '✓' : '✗'}
            </button>
            {stagingOpen && (
              <Popover anchorRef={stagingBtnRef} onClose={() => setStagingOpen(false)}>
                <StagingPopoverContent result={sr} checksDate={checksDate} />
              </Popover>
            )}
          </>
        )}
      </td>
      {/* JSON viewer */}
      <td onClick={e => e.stopPropagation()}>
        <button
          className="schema-link"
          type="button"
          title="View schema JSON"
          onClick={() => setModal(true)}
        >
          {'{ }'}
        </button>
        {modal && <JsonModal url={url} name={row.schema_name} onClose={() => setModal(false)} />}
      </td>
    </tr>
  )
}

// ─── Column resize handle ─────────────────────────────────────
function ResizeHandle({ thRef }) {
  function onMouseDown(e) {
    e.stopPropagation()
    const th = thRef.current
    if (!th) return
    const startX = e.pageX
    const startW = th.offsetWidth
    th.querySelector('.col-resize-handle')?.classList.add('dragging')
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    function onMove(e) {
      const newW = Math.max(40, startW + (e.pageX - startX))
      th.style.width = newW + 'px'
      th.style.minWidth = newW + 'px'
    }
    function onUp() {
      th.querySelector('.col-resize-handle')?.classList.remove('dragging')
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }
  return <div className="col-resize-handle" onMouseDown={onMouseDown} />
}

// ─── Column sort header ───────────────────────────────────────
function SortTh({ col, label, sortCol, sortDir, onSort, style }) {
  const active = sortCol === col
  const arrow = active ? (sortDir === 'asc' ? '↑' : '↓') : '↕'
  const thRef = useRef(null)
  return (
    <th
      ref={thRef}
      className={`sortable${active ? ` sort-${sortDir}` : ''}`}
      style={style}
      onClick={() => onSort(col)}
    >
      {label}<span className="sort-arrow">{arrow}</span>
      <ResizeHandle thRef={thRef} />
    </th>
  )
}

// ─── CSV export ───────────────────────────────────────────────
function exportCSV(rows, stagingResults) {
  const headers = ['Org Name', 'Schema Name', 'Status', 'Version', 'Created', 'Staging', 'Org ID', 'Schema ID', 'Version ID', 'Created By', 'SHA256']
  const lines = [headers.map(h => `"${h}"`).join(',')]
  for (const row of rows) {
    const uri = `${row.organization_name}-${row.schema_name}`
    const sr = stagingResults[uri]
    const staging = sr === undefined ? '' : sr.ok ? 'pass' : 'fail'
    const cells = [
      row.organization_name,
      row.schema_name,
      row.status,
      row.semantic_version,
      row.created_on ? new Date(row.created_on).toISOString() : '',
      staging,
      row.organization_id,
      row.schema_id,
      row.version_id,
      row.created_by,
      row.json_sha256_hex,
    ].map(v => `"${(v || '').toString().replace(/"/g, '""')}"`)
    lines.push(cells.join(','))
  }
  const blob = new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'schemas-export.csv'; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

// ─── Main table component ─────────────────────────────────────
export default function SchemaTable({ data, stagingResults, checksDate }) {
  // URL-initialised state
  const [search, setSearch] = useState(() => new URLSearchParams(window.location.search).get('q') || '')
  const [colFilters, setColFilters] = useState(() => {
    const p = new URLSearchParams(window.location.search)
    return {
      org: p.get('org') || '',
      schema: p.get('schema') || '',
      status: p.get('status') || '',
      version: p.get('ver') || '',
    }
  })
  const [hideDrafts, setHideDrafts] = useState(() => {
    const p = new URLSearchParams(window.location.search)
    // drafts=1 means SHOW drafts (i.e. hideDrafts=false)
    return p.get('drafts') !== '1'
  })

  const [showFilters, setShowFilters] = useState(false)
  const [sortCol, setSortCol] = useState('created_on')
  const [sortDir, setSortDir] = useState('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [focusedIdx, setFocusedIdx] = useState(-1)
  const [detailRow, setDetailRow] = useState(null)

  const searchRef = useRef(null)
  const tableRef = useRef(null)
  const rowRefs = useRef([])

  const { pinned, togglePin, isPinned } = usePinnedSchemas()

  // ── URL sync ─────────────────────────────────────────────
  useEffect(() => {
    const p = new URLSearchParams(window.location.search)
    // Write our params
    if (search) p.set('q', search); else p.delete('q')
    if (colFilters.org) p.set('org', colFilters.org); else p.delete('org')
    if (colFilters.schema) p.set('schema', colFilters.schema); else p.delete('schema')
    if (colFilters.status) p.set('status', colFilters.status); else p.delete('status')
    if (colFilters.version) p.set('ver', colFilters.version); else p.delete('ver')
    if (!hideDrafts) p.set('drafts', '1'); else p.delete('drafts')
    const qs = p.toString()
    history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname)
  }, [search, colFilters, hideDrafts])

  // ── "/" shortcut focuses search ───────────────────────────
  useEffect(() => {
    const handler = e => {
      if (e.key === '/' &&
          document.activeElement.tagName !== 'INPUT' &&
          document.activeElement.tagName !== 'SELECT') {
        e.preventDefault()
        searchRef.current?.focus()
        searchRef.current?.select()
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  // ── Filtering ─────────────────────────────────────────────
  const q = search.toLowerCase()
  let filtered = data.filter(row => {
    if (hideDrafts && (row.status || '').toLowerCase() === 'draft') return false
    if (colFilters.org && row.organization_name !== colFilters.org) return false
    if (colFilters.schema && row.schema_name !== colFilters.schema) return false
    if (colFilters.status && (row.status || '').toLowerCase() !== colFilters.status) return false
    if (colFilters.version && row.semantic_version !== colFilters.version) return false
    if (q) {
      const hay = [row.organization_name, row.schema_name, row.status, row.semantic_version].join(' ').toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })

  // ── Sorting ───────────────────────────────────────────────
  filtered = [...filtered].sort((a, b) => {
    const aPin = isPinned(`${a.organization_name}-${a.schema_name}`)
    const bPin = isPinned(`${b.organization_name}-${b.schema_name}`)
    if (aPin && !bPin) return -1
    if (!aPin && bPin) return 1

    let av = a[sortCol] ?? ''
    let bv = b[sortCol] ?? ''
    if (sortCol === 'created_on') {
      av = av ? new Date(av).getTime() : 0
      bv = bv ? new Date(bv).getTime() : 0
      return sortDir === 'asc' ? av - bv : bv - av
    }
    av = String(av).toLowerCase()
    bv = String(bv).toLowerCase()
    const cmp = av.localeCompare(bv, undefined, { numeric: true, sensitivity: 'base' })
    return sortDir === 'asc' ? cmp : -cmp
  })

  // ── Pagination ────────────────────────────────────────────
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const pageRows = filtered.slice((safePage - 1) * pageSize, safePage * pageSize)

  const handleSort = useCallback((col) => {
    setSortCol(prev => {
      if (prev === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
      else { setSortDir('asc') }
      return col
    })
    setPage(1)
  }, [])

  const setColFilter = (key, val) => {
    setColFilters(prev => ({ ...prev, [key]: val }))
    setPage(1)
  }

  const activeFilterCount = Object.values(colFilters).filter(Boolean).length + (search ? 1 : 0)

  function clearAll() {
    setSearch('')
    setColFilters({ org: '', schema: '', status: '', version: '' })
    setPage(1)
  }

  // ── Chip removal ──────────────────────────────────────────
  function removeFilter(key) {
    if (key === 'search') { setSearch(''); setPage(1) }
    else if (key === 'drafts') { setHideDrafts(true); setPage(1) }
    else { setColFilter(key, '') }
  }

  // ── Keyboard navigation ───────────────────────────────────
  function handleTableKeyDown(e) {
    const len = pageRows.length
    if (len === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIdx(prev => {
        const next = prev < len - 1 ? prev + 1 : prev
        rowRefs.current[next]?.focus()
        rowRefs.current[next]?.scrollIntoView({ block: 'nearest' })
        return next
      })
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIdx(prev => {
        const next = prev > 0 ? prev - 1 : 0
        rowRefs.current[next]?.focus()
        rowRefs.current[next]?.scrollIntoView({ block: 'nearest' })
        return next
      })
    } else if (e.key === 'Enter') {
      if (focusedIdx >= 0 && focusedIdx < len) {
        setDetailRow(pageRows[focusedIdx])
      }
    } else if (e.key === 'p' || e.key === 'P') {
      if (focusedIdx >= 0 && focusedIdx < len) {
        const row = pageRows[focusedIdx]
        togglePin(`${row.organization_name}-${row.schema_name}`)
      }
    }
  }

  // Reset focused index when page/filters change
  useEffect(() => { setFocusedIdx(-1) }, [page, search, colFilters, hideDrafts, sortCol, sortDir])

  // ── Unique values for dropdowns ───────────────────────────
  const orgs = [...new Set(data.map(r => r.organization_name).filter(Boolean))].sort()
  const schemas = [...new Set(data.map(r => r.schema_name).filter(Boolean))].sort()
  const statuses = [...new Set(data.map(r => (r.status || '').toLowerCase()).filter(Boolean))].sort()
  const versions = [...new Set(data.map(r => r.semantic_version).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true })
  )

  // ── Pagination buttons ─────────────────────────────────────
  function pageNums() {
    const pages = []
    const delta = 2
    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= safePage - delta && i <= safePage + delta)) {
        pages.push(i)
      } else if (pages[pages.length - 1] !== '…') {
        pages.push('…')
      }
    }
    return pages
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-header-top">
          <div>
            <h2>Schema Versions</h2>
            <p>
              Search across all columns, or open column filters for per-column control.
              {checksDate && (
                <span style={{ color: 'var(--muted2)', fontSize: 11.5 }}>
                  {' '}· Staging validated {relDate(checksDate)}
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Toolbar */}
        <div className="toolbar">
          <div className="search-wrap">
            <span className="search-icon">⌕</span>
            <input
              ref={searchRef}
              type="text"
              className="global-search"
              placeholder="Search all columns… (press /)"
              aria-label="Search schemas"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
            <span className="search-count">{filtered.length.toLocaleString()} results</span>
          </div>

          <select
            className="btn length-sel"
            value={pageSize}
            onChange={e => { setPageSize(Number(e.target.value)); setPage(1) }}
            aria-label="Rows per page"
          >
            {PAGE_SIZES.map(n => (
              <option key={n} value={n}>{n} rows</option>
            ))}
          </select>

          <span className="toolbar-sep" />

          <button
            className={`btn${showFilters ? ' open' : ''}`}
            type="button"
            onClick={() => setShowFilters(v => !v)}
            aria-expanded={showFilters}
          >
            Filters <span className={`chev${showFilters ? ' open' : ''}`}>▾</span>
            {activeFilterCount > 0 && <span className="filter-count">{activeFilterCount}</span>}
          </button>

          <button
            className={`btn${hideDrafts ? ' active' : ''}`}
            type="button"
            onClick={() => { setHideDrafts(v => !v); setPage(1) }}
            aria-pressed={hideDrafts}
          >
            Hide drafts
          </button>

          <button
            className={`btn${activeFilterCount === 0 ? ' disabled' : ''}`}
            type="button"
            onClick={clearAll}
          >
            Clear
          </button>

          <span className="toolbar-sep" />

          <button
            className="btn"
            type="button"
            title="Export filtered rows as CSV"
            onClick={() => exportCSV(filtered, stagingResults)}
          >
            ↓ CSV
          </button>

          <button
            className="btn"
            type="button"
            title="Export filtered rows as Excel"
            onClick={() => exportListToExcel(filtered, stagingResults)}
          >
            ↓ Excel
          </button>
        </div>

        {/* Active filter chips */}
        <FilterChips
          search={search}
          colFilters={colFilters}
          hideDrafts={hideDrafts}
          onRemove={removeFilter}
          onClearAll={clearAll}
        />
      </div>

      <div className="panel-body">
        {filtered.length === 0 && data.length > 0 ? (
          <div className="state-overlay">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><line x1="8" y1="11" x2="14" y2="11" />
            </svg>
            <p>No schemas match the current filters.<br /><span style={{ fontSize: 12, color: 'var(--muted2)' }}>Try adjusting your search or clearing filters.</span></p>
            <button className="btn" type="button" onClick={clearAll}>Clear filters</button>
          </div>
        ) : (
          <>
            <div className="table-wrap">
              <table
                className="schema-table"
                ref={tableRef}
                onKeyDown={handleTableKeyDown}
              >
                <thead>
                  <tr>
                    <th style={{ width: 36 }} />
                    <SortTh col="organization_name" label="Org Name" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} style={{ width: 140 }} />
                    <SortTh col="schema_name" label="Schema Name" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} style={{ minWidth: 160 }} />
                    <SortTh col="status" label="Status" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} style={{ width: 96 }} />
                    <SortTh col="semantic_version" label="Version" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} style={{ width: 80 }} />
                    <SortTh col="created_on" label="Created" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} style={{ width: 108 }} />
                    <th style={{ width: 40 }} />
                    <th style={{ width: 48 }}>JSON</th>
                  </tr>
                  {/* Column filter row */}
                  {showFilters && (
                    <tr className="filters-row">
                      <th />
                      <th>
                        <select className={`col-filter${colFilters.org ? ' has-value' : ''}`} value={colFilters.org} onChange={e => setColFilter('org', e.target.value)}>
                          <option value="">All</option>
                          {orgs.map(v => <option key={v} value={v}>{v}</option>)}
                        </select>
                      </th>
                      <th>
                        <select className={`col-filter${colFilters.schema ? ' has-value' : ''}`} value={colFilters.schema} onChange={e => setColFilter('schema', e.target.value)}>
                          <option value="">All</option>
                          {schemas.map(v => <option key={v} value={v}>{v}</option>)}
                        </select>
                      </th>
                      <th>
                        <select className={`col-filter${colFilters.status ? ' has-value' : ''}`} value={colFilters.status} onChange={e => setColFilter('status', e.target.value)}>
                          <option value="">All</option>
                          {statuses.map(v => <option key={v} value={v}>{v}</option>)}
                        </select>
                      </th>
                      <th>
                        <select className={`col-filter${colFilters.version ? ' has-value' : ''}`} value={colFilters.version} onChange={e => setColFilter('version', e.target.value)}>
                          <option value="">All</option>
                          {versions.map(v => <option key={v} value={v}>{v}</option>)}
                        </select>
                      </th>
                      <th><span className="muted" style={{ fontSize: 11 }}>—</span></th>
                      <th><span className="muted" style={{ fontSize: 11 }}>—</span></th>
                      <th><span className="muted" style={{ fontSize: 11 }}>—</span></th>
                    </tr>
                  )}
                </thead>
                <tbody>
                  {pageRows.map((row, i) => (
                    <SchemaRow
                      key={`${row.organization_name}-${row.schema_name}-${row.version_id}`}
                      row={row}
                      stagingResults={stagingResults}
                      checksDate={checksDate}
                      isPinned={isPinned}
                      onTogglePin={togglePin}
                      isFocused={focusedIdx === i}
                      rowRef={el => { rowRefs.current[i] = el }}
                      onRowClick={row => { setDetailRow(row); setFocusedIdx(i) }}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <div className="pagination-info">
                {filtered.length.toLocaleString()} of {data.length.toLocaleString()} rows
              </div>
              <div className="pagination-btns">
                <button className="page-btn" disabled={safePage === 1} onClick={() => setPage(1)}>«</button>
                <button className="page-btn" disabled={safePage === 1} onClick={() => setPage(p => p - 1)}>‹</button>
                {pageNums().map((p, i) =>
                  p === '…'
                    ? <span key={`ellipsis-${i}`} className="page-btn" style={{ pointerEvents: 'none' }}>…</span>
                    : <button key={p} className={`page-btn${p === safePage ? ' current' : ''}`} onClick={() => setPage(p)}>{p}</button>
                )}
                <button className="page-btn" disabled={safePage === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
                <button className="page-btn" disabled={safePage === totalPages} onClick={() => setPage(totalPages)}>»</button>
              </div>
            </div>

            <div className="footer">
              <span style={{ opacity: 0.45, fontSize: 12 }}>ⓘ</span>
              Click any row to view details · ↑↓ to navigate · Enter to open · P to pin · / to search
            </div>
          </>
        )}
      </div>

      {/* Schema detail side panel */}
      {detailRow && (
        <SchemaDetailPanel
          row={detailRow}
          stagingResults={stagingResults}
          checksDate={checksDate}
          isPinned={isPinned}
          onTogglePin={togglePin}
          onClose={() => setDetailRow(null)}
        />
      )}
    </div>
  )
}
