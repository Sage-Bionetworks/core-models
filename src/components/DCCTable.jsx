import { useState } from 'react'
import { DCC_DATA } from '../data/dcc.js'

function Link({ item }) {
  if (!item) return <span className="muted">—</span>
  return <a href={item.url} target="_blank" rel="noopener noreferrer">{item.label}</a>
}

export default function DCCTable() {
  const [search, setSearch] = useState('')
  const q = search.toLowerCase()
  const rows = DCC_DATA.filter(d =>
    !q ||
    d.name.toLowerCase().includes(q) ||
    (d.repo?.label || '').toLowerCase().includes(q) ||
    (d.docs?.label || '').toLowerCase().includes(q) ||
    (d.portal?.label || '').toLowerCase().includes(q)
  )

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-header-top">
          <div>
            <h2>Data Coordinating Center Links</h2>
            <p>Quick links to DCC GitHub repositories and documentation sites.</p>
          </div>
        </div>
      </div>
      <div className="panel-body">
        <div className="dcc-search-wrap">
          <input
            type="text"
            className="dcc-search"
            placeholder="Filter DCCs…"
            aria-label="Filter DCC table"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <table className="dcc-table">
          <thead>
            <tr>
              <th style={{ width: 110 }}>DCC</th>
              <th>GitHub Repository</th>
              <th>JSON Schema Links</th>
              <th>Docs Link</th>
              <th>Portal Link</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(d => (
              <tr key={d.name}>
                <td>{d.name}</td>
                <td><Link item={d.repo} /></td>
                <td><Link item={d.schemas} /></td>
                <td><Link item={d.docs} /></td>
                <td><Link item={d.portal} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
