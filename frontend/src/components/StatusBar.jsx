export default function StatusBar({ lastMatch, threshold }) {
  let lastMatchText = '—'
  if (lastMatch && lastMatch.name) {
    lastMatchText = `${lastMatch.name} (${lastMatch.score.toFixed(2)})`
  } else if (lastMatch && lastMatch.score > 0) {
    lastMatchText = `unknown (${lastMatch.score.toFixed(2)})`
  }

  return (
    <footer className="statusbar">
      <span>Last match: <strong>{lastMatchText}</strong></span>
      <span>Threshold: <strong>{threshold.toFixed(2)}</strong></span>
    </footer>
  )
}
