import { useState } from 'react'

export default function EnrollPanel({ onEnrolled }) {
  const [name, setName] = useState('')
  const [msg, setMsg] = useState({ text: '', type: '' })

  async function capture() {
    const trimmed = name.trim()
    if (!trimmed) {
      setMsg({ text: 'Enter a name first.', type: 'error' })
      return
    }

    setMsg({ text: 'Capturing…', type: '' })

    try {
      const res = await fetch('/api/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed }),
      })
      const data = await res.json()

      if (!res.ok) {
        setMsg({ text: data.detail || 'Capture failed.', type: 'error' })
        return
      }

      setMsg({ text: `Saved shot #${data.count} for ${data.name}.`, type: 'success' })
      setName('')
      onEnrolled()
    } catch (err) {
      setMsg({ text: 'Could not reach the server.', type: 'error' })
    }
  }

  return (
    <div className="panel enroll">
      <h2>Enroll</h2>
      <input
        type="text"
        placeholder="Person's name"
        autoComplete="off"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button type="button" onClick={capture}>Capture from feed</button>
      <p className={`msg ${msg.type}`}>{msg.text}</p>
    </div>
  )
}
