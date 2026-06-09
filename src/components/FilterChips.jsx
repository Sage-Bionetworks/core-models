export default function FilterChips({ search, colFilters, hideDrafts, onRemove, onClearAll }) {
  const chips = []

  if (search) {
    chips.push({ key: 'search', label: `Search: "${search}"`, onRemove: () => onRemove('search') })
  }
  if (colFilters.org) {
    chips.push({ key: 'org', label: `Org: ${colFilters.org}`, onRemove: () => onRemove('org') })
  }
  if (colFilters.schema) {
    chips.push({ key: 'schema', label: `Schema: ${colFilters.schema}`, onRemove: () => onRemove('schema') })
  }
  if (colFilters.status) {
    chips.push({ key: 'status', label: `Status: ${colFilters.status}`, onRemove: () => onRemove('status') })
  }
  if (colFilters.version) {
    chips.push({ key: 'version', label: `Version: ${colFilters.version}`, onRemove: () => onRemove('version') })
  }
  if (!hideDrafts) {
    chips.push({ key: 'drafts', label: 'Showing drafts', onRemove: () => onRemove('drafts') })
  }

  if (chips.length === 0) return null

  return (
    <div className="filter-chips">
      {chips.map(chip => (
        <span key={chip.key} className="filter-chip">
          {chip.label}
          <button
            className="filter-chip-remove"
            type="button"
            aria-label={`Remove filter: ${chip.label}`}
            onClick={chip.onRemove}
          >
            ✕
          </button>
        </span>
      ))}
      {chips.length > 1 && (
        <button className="filter-chip filter-chip--clear-all" type="button" onClick={onClearAll}>
          Clear all
        </button>
      )}
    </div>
  )
}
