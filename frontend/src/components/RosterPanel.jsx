export default function RosterPanel({ roster, onDelete }) {
  const names = Object.keys(roster)

  return (
    <div className="panel roster">
      <h2>Roster</h2>
      <ul>
        {names.length === 0 && <li className="empty">No one enrolled yet</li>}
        {names.map((name) => (
          <li key={name}>
            <span>{name}</span>
            <span className="count">{roster[name]} shot{roster[name] > 1 ? 's' : ''}</span>
            <button className="del" aria-label={`Remove ${name}`} onClick={() => onDelete(name)}>&times;</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
