import { useState, useCallback } from 'react'

const STORAGE_KEY = 'core-models-pinned'

function loadPinned() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? new Set(JSON.parse(raw)) : new Set()
  } catch {
    return new Set()
  }
}

function savePinned(set) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]))
  } catch {}
}

export default function usePinnedSchemas() {
  const [pinned, setPinned] = useState(() => loadPinned())

  const togglePin = useCallback((id) => {
    setPinned(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      savePinned(next)
      return next
    })
  }, [])

  const isPinned = useCallback((id) => pinned.has(id), [pinned])

  return { pinned, togglePin, isPinned }
}
