import { useEffect, useState } from 'react'

// Poll still frames instead of using an MJPEG <img>, which Safari won't paint.
export default function Viewport({ lastMatch }) {
  const [src, setSrc] = useState(null)

  useEffect(() => {
    let stopped = false
    let timer

    async function tick() {
      let delay = 500
      try {
        const res = await fetch('/snapshot.jpg', { cache: 'no-store' })
        if (res.ok) {
          const url = URL.createObjectURL(await res.blob())
          if (stopped) {
            URL.revokeObjectURL(url)
            return
          }
          setSrc((prev) => {
            if (prev) URL.revokeObjectURL(prev)
            return url
          })
          delay = 60
        }
      } catch {
        // server not reachable yet, retry below
      }
      if (!stopped) timer = setTimeout(tick, delay)
    }

    tick()
    return () => {
      stopped = true
      clearTimeout(timer)
    }
  }, [])

  let label = 'No face'
  let state = 'idle'
  if (lastMatch && lastMatch.name) {
    label = `${lastMatch.name} · ${lastMatch.score.toFixed(2)}`
    state = 'match'
  } else if (lastMatch && lastMatch.score > 0) {
    label = `Unknown · ${lastMatch.score.toFixed(2)}`
    state = 'unknown'
  }

  return (
    <section className="viewport" aria-label="Live camera feed">
      {src ? (
        <img src={src} alt="Live annotated camera feed" />
      ) : (
        <div className="placeholder">Starting camera…</div>
      )}
      <div className="guide" aria-hidden="true">
        <div className="guide-frame">
          <span className="tl"></span>
          <span className="tr"></span>
          <span className="bl"></span>
          <span className="br"></span>
        </div>
      </div>
      <div className={`chip ${state}`}>{label}</div>
    </section>
  )
}
