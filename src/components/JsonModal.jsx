import { useEffect, useState, useRef } from 'react'

export default function JsonModal({ url, name, onClose }) {
  const [state, setState] = useState('loading') // loading | ok | error
  const [json, setJson] = useState('')
  const [copied, setCopied] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    setState('loading')
    setJson('')
    fetch(url)
      .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json() })
      .then(data => { setJson(JSON.stringify(data, null, 2)); setState('ok') })
      .catch(err => { setJson(err.message); setState('error') })
  }, [url])

  // Keyboard close
  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  // Lock scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  function handleCopy() {
    if (!json) return
    navigator.clipboard.writeText(json).then(() => {
      setCopied(true)
      clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => setCopied(false), 1800)
    })
  }

  return (
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-header">
          <div className="modal-header-left">
            <div id="modal-title" className="modal-title">{name || 'Schema JSON'}</div>
            <div className="modal-url">
              <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>
            </div>
          </div>
          <div className="modal-actions">
            <button
              className={`modal-copy${copied ? ' copied' : ''}`}
              onClick={handleCopy}
              type="button"
            >
              {copied ? '✓ Copied!' : '⎘ Copy JSON'}
            </button>
            <button className="modal-close" onClick={onClose} type="button" aria-label="Close">✕</button>
          </div>
        </div>
        <div className="modal-body">
          {state === 'loading' && (
            <div className="modal-loading"><div className="spinner" /> Loading…</div>
          )}
          {state === 'error' && (
            <div className="modal-error">⚠ Could not load JSON: {json}</div>
          )}
          {state === 'ok' && (
            <pre className="json-pre">{json}</pre>
          )}
        </div>
      </div>
    </div>
  )
}
