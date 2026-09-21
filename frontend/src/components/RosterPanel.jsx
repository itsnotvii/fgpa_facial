export default function RosterPanel({ roster, onDelete }) {
  const names = Object.keys(roster)

  return (
    <div className="panel roster">
      <h2>People</h2>
      <ul>
        {names.length === 0 && <li className="empty">No one yet</li>}
        {names.map((name) => (
          <li key={name}>
            <span>{name}</span>
            <span className="count">{roster[name]}</span>
            <button className="del" aria-label={`Remove ${name}`} onClick={() => onDelete(name)}>&times;</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
