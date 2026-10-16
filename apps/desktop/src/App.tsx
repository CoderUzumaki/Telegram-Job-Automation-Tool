import "./App.css";

function App() {
  return (
    <main className="welcome" aria-labelledby="welcome-title">
      <div className="welcome__brand" aria-label="Job Radar">
        <span className="welcome__mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span>JOB RADAR</span>
      </div>

      <section className="welcome__content">
        <p className="welcome__eyebrow">YOUR LOCAL JOB WORKSPACE</p>
        <h1 id="welcome-title">
          <span>Find the roles</span>{" "}
          <br aria-hidden="true" />
          <span>worth your attention.</span>
        </h1>
        <p className="welcome__description">
          Job Radar brings opportunities from sources you choose into one clear,
          private workspace.
        </p>
        <div className="welcome__status" role="status">
          <span className="welcome__status-dot" aria-hidden="true" />
          <span>Ready for setup</span>
        </div>
      </section>

      <footer className="welcome__footer">
        <span>LOCAL BY DEFAULT</span>
        <span>YOUR SOURCES. YOUR CHOICE.</span>
      </footer>
    </main>
  );
}

export default App;
