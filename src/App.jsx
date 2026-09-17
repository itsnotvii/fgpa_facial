import { useCallback, useEffect, useState } from 'react'
import TopBar from './components/TopBar.jsx'
import Viewport from './components/Viewport.jsx'
import EnrollPanel from './components/EnrollPanel'
import RosterPanel from './components/RosterPanel'
import StatusBar from './components/StatusBar.jsx'

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

  
}