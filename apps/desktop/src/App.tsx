import { useState } from "react";
import "./App.css";

type Page = "Overview" | "All jobs" | "Saved" | "Applied" | "Sources" | "Activity" | "Settings";

const navigation: { label: Page; icon: string }[] = [
  { label: "Overview", icon: "◫" },
  { label: "All jobs", icon: "▤" },
  { label: "Saved", icon: "♡" },
  { label: "Applied", icon: "✓" },
  { label: "Sources", icon: "⌁" },
  { label: "Activity", icon: "◷" },
];

const steps = ["Your goals", "Your sources", "Your workspace"];
const pageEmptyState: Record<Exclude<Page, "Overview">, { title: string; message: string; next: string }> = {
  "All jobs": { title: "Your next opportunity will show up here.", message: "Approve a source to start finding roles. Every recognized post stays available, including uncertain and lower-match opportunities.", next: "Set up a source" },
  Saved: { title: "Keep the roles you want close.", message: "Save a job when it feels worth a second look. Your saved list will stay separate from match scores and application status.", next: "Browse all jobs" },
  Applied: { title: "Your progress, in your hands.", message: "When you decide to apply, confirm it here. Opening a link never marks a job as applied automatically.", next: "Browse all jobs" },
  Sources: { title: "You decide what enters your radar.", message: "Connect Telegram, review the chats available to your account, and approve only the ones you want Job Radar to process.", next: "Review setup" },
  Activity: { title: "A clear record of what changed.", message: "Source sync, profile updates, and privacy actions will be easy to review here once connected.", next: "Go to overview" },
  Settings: { title: "Preferences that can grow with you.", message: "Update the role, location, and work style you want to prioritize. Profile changes will trigger a fresh, explainable review of saved jobs.", next: "Review your preferences" },
};

function Brand() {
  return (
    <div className="brand" aria-label="Job Radar">
      <span className="brand__mark" aria-hidden="true"><i /><i /><i /></span>
      <span className="brand__name">job radar<span className="brand__period">.</span></span>
    </div>
  );
}

function Arrow({ diagonal = false }: { diagonal?: boolean }) {
  return <span aria-hidden="true" className="arrow">{diagonal ? "↗" : "→"}</span>;
}

function App() {
  const [page, setPage] = useState<Page>("Overview");
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [isSettingUp, setIsSettingUp] = useState(true);
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [workMode, setWorkMode] = useState("Any work mode");

  const finishSetup = () => {
    setIsSettingUp(false);
    setPage("Overview");
  };

  if (isSettingUp) {
    return (
      <main className="setup">
        <header className="setup__top"><Brand /><span className="setup__private"><span className="dot" /> Private on this device</span></header>
        <div className="setup__layout">
          <section className="setup__intro">
            <p className="eyebrow"><span className="eyebrow__line" /> A calmer way to find your next role</p>
            <h1>Your search.<br />Your <span className="accent-word">direction.</span></h1>
            <p className="setup__lead">Build a radar around the work you want. You choose the sources, the preferences, and what deserves your attention.</p>
            <div className="setup__promise"><span className="promise__icon">✳</span><div><strong>Made to fit your next move</strong><span>Your preferences shape every match and every explanation.</span></div></div>
            <div className="setup__swatches" aria-label="Job Radar color palette"><span /><span /><span /><span /><span /></div>
          </section>

          <section className="setup-card" aria-labelledby="setup-title">
            <div className="setup-card__top"><span className="step-count">0{onboardingStep + 1} <span>/ 03</span></span><span className="step-caption">YOUR RADAR, YOUR RULES</span></div>
            <div className="progress-track" aria-label={`Step ${onboardingStep + 1} of 3`}><span style={{ width: `${((onboardingStep + 1) / steps.length) * 100}%` }} /></div>
            <div className="step-labels">{steps.map((step, index) => <span className={index === onboardingStep ? "is-current" : index < onboardingStep ? "is-done" : ""} key={step}>{step}</span>)}</div>

            {onboardingStep === 0 && <div className="setup-card__body">
              <span className="section-kicker">FIRST, THE WORK YOU WANT</span>
              <h2 id="setup-title">What feels like your next step?</h2>
              <p className="form-intro">A few details help Job Radar understand what to look for. You can refine them any time.</p>
              <label className="field-label" htmlFor="target-role">Role or kind of work</label>
              <div className="input-wrap"><span aria-hidden="true">⌕</span><input id="target-role" autoComplete="off" placeholder="e.g. Product designer" value={role} onChange={(event) => setRole(event.target.value)} /></div>
              <label className="field-label" htmlFor="target-location">Where would you like to work?</label>
              <div className="input-wrap"><span aria-hidden="true">⌖</span><input id="target-location" autoComplete="off" placeholder="City, region, or anywhere" value={location} onChange={(event) => setLocation(event.target.value)} /></div>
              <label className="field-label" htmlFor="work-mode">Work style</label>
              <select id="work-mode" className="select-field" value={workMode} onChange={(event) => setWorkMode(event.target.value)}>
                <option>Any work mode</option><option>Remote</option><option>Hybrid</option><option>On-site</option>
              </select>
              <button className="button button--primary setup-next" onClick={() => setOnboardingStep(1)}>Continue <Arrow /></button>
              <p className="privacy-note"><span aria-hidden="true">◈</span> Your preferences stay on this device.</p>
            </div>}

            {onboardingStep === 1 && <div className="setup-card__body">
              <span className="section-kicker">YOU ARE IN CONTROL</span>
              <h2 id="setup-title">Choose where opportunities come from.</h2>
              <p className="form-intro">Job Radar only processes Telegram sources you explicitly approve. You can pause or remove a source whenever you like.</p>
              <div className="source-preview"><div className="source-preview__icon">◉</div><div><strong>Telegram sources</strong><span>Connect your account, review available chats, then approve the ones you want monitored.</span></div><span className="source-preview__tag">OPTIONAL</span></div>
              <div className="consent-card"><span className="consent-card__icon">✓</span><p><strong>Nothing is monitored by default.</strong><br />Your account is used only to discover source names. Message processing starts only after you approve a source.</p></div>
              <button className="button button--primary setup-next" onClick={() => setOnboardingStep(2)}>Continue <Arrow /></button>
              <button className="button button--text" onClick={() => setOnboardingStep(2)}>I’ll choose sources later</button>
              <button className="back-link" onClick={() => setOnboardingStep(0)}>← Back to your goals</button>
            </div>}

            {onboardingStep === 2 && <div className="setup-card__body setup-card__ready">
              <span className="ready-mark">✳</span>
              <span className="section-kicker">A GOOD PLACE TO BEGIN</span>
              <h2 id="setup-title">Your space is ready to take shape.</h2>
              <p className="form-intro">{role ? `We’ll keep “${role}” in focus` : "Your goals can be added whenever you’re ready"}{location ? ` around ${location}` : ""}. Your dashboard will stay clear until you connect a source and approve it.</p>
              <div className="ready-summary"><span>YOUR WORK STYLE</span><strong>{workMode}</strong><span>YOUR SOURCES</span><strong>None approved yet</strong></div>
              <button className="button button--primary setup-next" onClick={finishSetup}>Open my workspace <Arrow /></button>
              <button className="back-link" onClick={() => setOnboardingStep(1)}>← Review source choices</button>
            </div>}
          </section>
        </div>
        <footer className="setup__footer"><span>YOUR SEARCH, IN YOUR HANDS.</span><span>LOCAL BY DEFAULT <i /> NO AUTO-APPLY <i /> YOU DECIDE</span></footer>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="sidebar__label">YOUR SPACE</div>
        <nav className="nav" aria-label="Main navigation">{navigation.map((item) => <button key={item.label} className={`nav__item ${page === item.label ? "is-active" : ""}`} onClick={() => setPage(item.label)}><span className="nav__icon" aria-hidden="true">{item.icon}</span>{item.label}{page === item.label && <span className="nav__active-dot" />}</button>)}</nav>
        <div className="sidebar__bottom"><div className="sidebar__privacy"><span className="dot" /><div><strong>Private by default</strong><span>Data stays on this device</span></div></div><button className={`nav__item ${page === "Settings" ? "is-active" : ""}`} onClick={() => setPage("Settings")}><span className="nav__icon" aria-hidden="true">⚙</span>Settings</button><button className="help-link" onClick={() => setPage("Activity")}>? <span>Help & feedback</span></button></div>
      </aside>

      <section className="workspace">
        <header className="topbar"><div className="breadcrumbs"><span>YOUR WORKSPACE</span><b>/</b><strong>{page}</strong></div><div className="topbar__actions"><span className="connection-state"><span className="dot dot--muted" /> Not connected</span><button className="avatar" aria-label="Personalize your radar" onClick={() => { setOnboardingStep(0); setIsSettingUp(true); }}>JR</button></div></header>
        <div className="workspace__content">
          {page !== "Overview" ? <>
            <div className="page-heading"><div><p className="eyebrow"><span className="eyebrow__line" /> YOUR SEARCH, YOUR CHOICES</p><h1>{page}</h1><p className="page-subtitle">{page === "Sources" ? "Review and manage the places Job Radar can listen." : `A personal view of the opportunities that matter to you.`}</p></div><button className="button button--dark" onClick={() => setPage("Overview")}>Back to overview <Arrow /></button></div>
            <section className={`route-empty route-empty--${page.toLowerCase().replace(" ", "-")}`}><span className="route-empty__spark">✳</span><span className="section-kicker">{page === "Sources" ? "SOURCE PERMISSION" : page === "Applied" ? "APPLICATION TRACKING" : page === "Settings" ? "YOUR PROFILE" : "A SPACE FOR YOUR SEARCH"}</span><h2>{pageEmptyState[page].title}</h2><p>{pageEmptyState[page].message}</p><button className="button button--primary" onClick={() => page === "Sources" ? (setIsSettingUp(true), setOnboardingStep(1)) : page === "Settings" ? (setIsSettingUp(true), setOnboardingStep(0)) : page === "Saved" || page === "Applied" ? setPage("All jobs") : setPage("Overview")}>{pageEmptyState[page].next} <Arrow /></button><div className="route-empty__note"><span className="dot dot--muted" /> {page === "Sources" ? "No sources approved" : page === "Settings" ? "No saved profile yet" : "No jobs to show yet"}</div></section>
            <footer className="workspace-footer"><span>JOB RADAR <i /> BUILT AROUND YOUR CHOICES</span><span>LOCAL BY DEFAULT <span className="footer-mark">✳</span></span></footer>
          </> : <>
          <div className="page-heading"><div><p className="eyebrow"><span className="eyebrow__line" /> YOUR JOB SEARCH, IN ONE PLACE</p><h1>{role ? `Your ${role} radar.` : "A little more focus."}</h1><p className="page-subtitle">{role ? [location, workMode !== "Any work mode" ? workMode : ""].filter(Boolean).join(" · ") || "Your preferences are ready to refine." : "A thoughtful space for opportunities that fit your next move."}</p></div><button className="button button--dark" onClick={() => { setIsSettingUp(true); setOnboardingStep(0); }}>Personalize your radar <Arrow /></button></div>

          <section className="welcome-panel"><div className="welcome-panel__copy"><span className="panel-kicker">A SEARCH THAT FEELS LIKE YOURS</span><h2>Good opportunities.<br /><span>Less noise.</span></h2><p>Start with the work you want. Then bring in only the sources you trust.</p><button className="button button--white" onClick={() => { setIsSettingUp(true); setOnboardingStep(0); }}>Set up your preferences <Arrow /></button></div><div className="radar-art" aria-hidden="true"><div className="radar-art__halo" /><div className="radar-art__ring radar-art__ring--outer" /><div className="radar-art__ring radar-art__ring--inner" /><div className="radar-art__core"><span /><span /><span /></div><span className="radar-art__spark radar-art__spark--one">✳</span><span className="radar-art__spark radar-art__spark--two">✦</span><span className="radar-art__orbit orbit--one" /><span className="radar-art__orbit orbit--two" /></div><span className="welcome-panel__index">01 / YOUR RADAR</span></section>

          <div className="section-heading"><div><span className="section-kicker">YOUR NEXT STEPS</span><h2>Make it personal, one step at a time.</h2></div><button className="text-action" onClick={() => { setIsSettingUp(true); setOnboardingStep(0); }}>View setup <Arrow /></button></div>
          <section className="setup-grid" aria-label="Workspace setup steps">
            <article className="setup-tile setup-tile--purple"><span className="tile-number">01</span><span className="tile-icon">◌</span><h3>Set your direction</h3><p>Tell us what roles, places, and work styles matter to you.</p><button onClick={() => { setIsSettingUp(true); setOnboardingStep(0); }}>Add your preferences <Arrow /></button></article>
            <article className="setup-tile setup-tile--coral"><span className="tile-number">02</span><span className="tile-icon">⌁</span><h3>Choose your sources</h3><p>Review Telegram chats and approve only the sources you want.</p><button onClick={() => { setIsSettingUp(true); setOnboardingStep(1); }}>Review source setup <Arrow /></button></article>
            <article className="setup-tile setup-tile--teal"><span className="tile-number">03</span><span className="tile-icon">✳</span><h3>See the signal</h3><p>Get clear match reasons, then decide what to save or pursue.</p><button onClick={() => setPage("All jobs")}>Explore your workspace <Arrow /></button></article>
          </section>

          <section className="empty-jobs"><div className="empty-jobs__icon">✦</div><div><span className="section-kicker">YOUR OPPORTUNITY FEED</span><h2>Good things take a little setup.</h2><p>Connect and approve a source to see opportunities here. Until then, this space stays yours—clear and ready.</p></div><div className="empty-jobs__aside"><span className="empty-jobs__status"><span className="dot dot--muted" /> Waiting for an approved source</span><button className="text-action" onClick={() => setPage("Sources")}>Manage sources <Arrow /></button></div></section>

          <footer className="workspace-footer"><span>JOB RADAR <i /> BUILT AROUND YOUR CHOICES</span><span>LOCAL BY DEFAULT <span className="footer-mark">✳</span></span></footer>
          </>}
        </div>
      </section>
    </main>
  );
}

export default App;
