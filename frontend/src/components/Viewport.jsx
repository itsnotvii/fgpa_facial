export default function Viewport() {
  return (
    <section className="viewport" aria-label="Live camera feed">
      <img src="/video_feed" alt="Live annotated camera feed" />
      <div className="face-guide" aria-hidden="true">
        <div className="frame">
          <span className="corner tl"></span>
          <span className="corner tr"></span>
          <span className="corner bl"></span>
          <span className="corner br"></span>
        </div>
        <span className="face-guide-hint">Center your face in the frame</span>
      </div>
    </section>
  )
}
