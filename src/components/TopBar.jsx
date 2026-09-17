export default function TopBar({ enrolledCount }) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2 3 6v6c0 5 3.8 8.7 9 10 5.2-1.3 9-5 9-10V6l-9-4Z" fill="#000" />
          </svg>
        </span>
        <div className="brand-text">
          <h1>AI & FGPA Take Home Project</h1>
          <p>Facial recognition console</p>
        </div>
      </div>
      <div className="status-line">
        <span className="dot" aria-hidden="true"></span>
        <span>{enrolledCount}</span>&nbsp;enrolled
      </div>
    </header>
  )
}
