export function relDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  const s = Math.floor(diff / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  const dy = Math.floor(h / 24)
  const mo = Math.floor(dy / 30)
  const yr = Math.floor(dy / 365)
  if (yr > 0) return yr === 1 ? '1 year ago' : `${yr} years ago`
  if (mo > 0) return mo === 1 ? '1 month ago' : `${mo} months ago`
  if (dy > 0) return dy === 1 ? '1 day ago' : `${dy} days ago`
  if (h > 0) return h === 1 ? '1 hour ago' : `${h} hours ago`
  if (m > 0) return m === 1 ? '1 min ago' : `${m} mins ago`
  return 'just now'
}

export function fmtDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}
