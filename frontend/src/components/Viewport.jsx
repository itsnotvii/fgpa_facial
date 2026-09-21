export default function Viewport({ lastMatch }) {
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
      <img src="/video_feed" alt="Live annotated camera feed" />
      <div className={`chip ${state}`}>{label}</div>
    </section>
  )
}
