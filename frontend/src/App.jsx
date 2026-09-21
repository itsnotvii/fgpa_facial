import { useCallback, useEffect, useState } from 'react'
import Viewport from './components/Viewport.jsx'
import EnrollPanel from './components/EnrollPanel'
import RosterPanel from './components/RosterPanel'

export default function App() {
  const [roster, setRoster] = useState({})
  const [status, setStatus] = useState({ enrolled_people: 0, last_match: null, threshold: 0.4 })

  const refreshRoster = useCallback(async () => {
    const res = await fetch('/api/roster')
    setRoster(await res.json())
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status')
      setStatus(await res.json())
    } catch {
      // camera/backend still warming up, ignore and retry next tick
    }
  }, [])

  const deletePerson = useCallback(async (name) => {
    await fetch(`/api/roster/${encodeURIComponent(name)}`, { method: 'DELETE' })
    refreshRoster()
  }, [refreshRoster])

  useEffect(() => {
    refreshRoster()
    refreshStatus()
    const rosterTimer = setInterval(refreshRoster, 4000)
    const statusTimer = setInterval(refreshStatus, 1500)
    return () => {
      clearInterval(rosterTimer)
      clearInterval(statusTimer)
    }
  }, [refreshRoster, refreshStatus])

  return (
    <div className="app">
      <h1 className="title">Face Recognition</h1>
      <main className="grid">
        <Viewport lastMatch={status.last_match} />
        <aside className="sidebar">
          <EnrollPanel onEnrolled={refreshRoster} />
          <RosterPanel roster={roster} onDelete={deletePerson} />
        </aside>
      </main>
    </div>
  )
}