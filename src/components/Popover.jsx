import { useEffect, useRef, useState } from 'react'

/**
 * Generic positioned popover.
 * anchorRef — ref to the button that triggered it
 * onClose   — called when clicking outside
 */
export default function Popover({ anchorRef, onClose, children }) {
  const popRef = useRef(null)
  const [style, setStyle] = useState({ left: 0, top: 0 })

  useEffect(() => {
    if (!anchorRef.current || !popRef.current) return
    const r = anchorRef.current.getBoundingClientRect()
    const pw = popRef.current.offsetWidth
    const ph = popRef.current.offsetHeight
    let left = r.right - pw
    if (left < 8) left = 8
    let top = r.bottom + 6
    if (top + ph > window.innerHeight - 8) top = r.top - ph - 6
    setStyle({ left, top })
  }, [anchorRef])

  useEffect(() => {
    function handler(e) {
      if (popRef.current && !popRef.current.contains(e.target) &&
          anchorRef.current && !anchorRef.current.contains(e.target)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    document.addEventListener('scroll', onClose, true)
    window.addEventListener('resize', onClose)
    return () => {
      document.removeEventListener('mousedown', handler)
      document.removeEventListener('scroll', onClose, true)
      window.removeEventListener('resize', onClose)
    }
  }, [onClose, anchorRef])

  return (
    <div ref={popRef} className="popover" style={style}>
      {children}
    </div>
  )
}
