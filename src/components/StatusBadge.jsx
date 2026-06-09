export default function StatusBadge({ status }) {
  if (!status) return <span className="muted">—</span>
  const s = status.toLowerCase()
  return <span className={`status-pill ${s}`}>{s}</span>
}
