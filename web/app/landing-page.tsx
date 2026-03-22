"use client";

import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  Bird,
  BookOpen,
  Brain,
  Database,
  Github,
  Layers,
  Scale,
  ShieldCheck,
  Sparkles,
  Trash2,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

type Phase = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export default function LandingPage() {
  const [phase, setPhase] = useState<Phase>(0);

  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.1 },
    );
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const selectPhase = useCallback((p: Phase) => {
    setPhase(p);
  }, []);

  return (
    <>
      <nav>
        <div className="nav-left">
          <a href="#" className="logo" aria-label="MemComp home">
            <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="2" y="2" width="24" height="24" rx="6" stroke="#3c6e71" strokeWidth="2" />
              <path
                d="M9 9h2v2H9zM13 9h2v2h-2zM17 9h2v2h-2zM9 13h2v2H9zM13 13h2v2h-2zM17 13h2v2h-2zM11 17h6v2h-6z"
                fill="#6dafb4"
              />
              <circle cx="14" cy="14" r="1" fill="#ffffff" />
            </svg>
            MemComp
          </a>
          <ul className="nav-links">
            <li>
              <a href="#walkthrough">How it Works</a>
            </li>
            <li>
              <a href="#features">Features</a>
            </li>
            <li>
              <a href="#" className="nav-link-icon">
                GitHub
              </a>
            </li>
          </ul>
        </div>
      </nav>

      <section className="hero">
        <div className="floating-memories">
          <div className="floating-card">user prefers dark mode for all editors</div>
          <div className="floating-card">Paris is the capital of France</div>
          <div className="floating-card">meeting scheduled for Thursday 3pm</div>
          <div className="floating-card">API key stored in .env file</div>
          <div className="floating-card">user&apos;s favorite language is Python</div>
          <div className="floating-card">the Eiffel Tower was built in 1889</div>
          <div className="floating-card">project deadline is end of Q2</div>
          <div className="floating-card">database uses PostgreSQL 15</div>
        </div>
        <div className="hero-badge">
          <Sparkles size={14} strokeWidth={2} aria-hidden />
          Open Source · Built for AI Agents
        </div>
        <h1>
          <span className="gradient-text">
            Vector DBs are finite —
            <br />
            what should the agent forget?
          </span>
        </h1>
        <p>
          MemComp automatically merges similar memories, deletes low-value ones, and summarizes clusters —
          keeping your agent&apos;s memory lean, fast, and intelligent.
        </p>
        <div className="hero-ctas">
          <a href="#" className="btn-ghost">
            <Github size={18} strokeWidth={2} aria-hidden />
            View on GitHub
          </a>
        </div>
      </section>

      <section className="problem reveal">
        <h2 className="section-title">The Problem with Agent Memory</h2>
        <div className="problem-grid">
          <div className="problem-card">
            <div className="card-icon">
              <Layers size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Unbounded Growth</h3>
            <p>
              Vector DBs fill up with redundant, low-signal memories. Retrieval gets slower and noisier over
              time.
            </p>
          </div>
          <div className="problem-card">
            <div className="card-icon">
              <Trash2 size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>No Garbage Collection</h3>
            <p>
              Agents store everything but forget nothing intentionally. There&apos;s no mechanism to prune what
              no longer matters.
            </p>
          </div>
          <div className="problem-card">
            <div className="card-icon">
              <AlertCircle size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Catastrophic Forgetting</h3>
            <p>Naive deletion destroys critical context. You need compression that preserves what matters.</p>
          </div>
        </div>
      </section>

      <section className="walkthrough reveal" id="walkthrough">
        <div className="section-label">How It Works</div>
        <h2 className="section-title">A Complete Compression Pipeline</h2>
        <p className="section-subtitle" style={{ margin: "0 auto 0" }}>
          Seven phases, each independently testable
        </p>
        <div className="walkthrough-container">
          <div className="stepper" role="tablist" aria-label="Pipeline phases">
            {(
              [
                "Store & Retrieve",
                "Importance Scoring",
                "Deletion",
                "Merging",
                "Summarization",
                "Evaluation",
                "Tuning",
              ] as const
            ).map((label, i) => (
              <div
                key={label}
                role="tab"
                aria-selected={phase === i}
                className={`stepper-item${phase === i ? " active" : ""}`}
                onClick={() => selectPhase(i as Phase)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    selectPhase(i as Phase);
                  }
                }}
                tabIndex={0}
              >
                <span className="stepper-number">{i + 1}</span>
                <span className="stepper-label">{label}</span>
              </div>
            ))}
          </div>
          <div className="phase-panel" role="tabpanel">
            <div className={`phase-content${phase === 0 ? " active" : ""}`} data-phase="0">
              <span className="phase-badge">Phase 1</span>
              <h3>Store & Retrieve</h3>
              <p className="phase-desc">
                Embed memories with sentence-transformers, store in ChromaDB, retrieve by semantic similarity.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="cm"># Store a memory with tags</span>
<span class="hi">writer</span>.<span class="fn">store</span>(<span class="str">"User prefers Python"</span>, tags=[<span class="str">"pref"</span>])

<span class="cm"># Retrieve by semantic similarity</span>
<span class="hi">results</span> = <span class="hi">writer</span>.<span class="fn">retrieve</span>(<span class="str">"coding preferences"</span>, n=<span class="num">3</span>)

<span class="cm"># Results:</span>
<span class="cm"># [0] 0.94  "User prefers Python"</span>
<span class="cm"># [1] 0.81  "Use snake_case for variables"</span>
<span class="cm"># [2] 0.73  "IDE: VS Code with vim keys"</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 1 ? " active" : ""}`} data-phase="1">
              <span className="phase-badge">Phase 2</span>
              <h3>Importance Scoring</h3>
              <p className="phase-desc">
                Composite score: recency (25%) + access frequency (30%) + retrieval rank (20%) + semantic
                uniqueness (25%).
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="hi">score: <span class="num">0.824</span></span> <span class="kw">||||||||||||||||</span>  acc=<span class="num">7</span>
  <span class="str">"The capital of France is Paris"</span>

<span class="hi">score: <span class="num">0.612</span></span> <span class="kw">||||||||||||</span>      acc=<span class="num">3</span>
  <span class="str">"Python was created by Guido"</span>

<span class="hi">score: <span class="num">0.203</span></span> <span class="kw">||||</span>              acc=<span class="num">0</span>
  <span class="str">"Weather was nice on Tuesday"</span>   <span class="cm">← low value</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 2 ? " active" : ""}`} data-phase="2">
              <span className="phase-badge">Phase 3</span>
              <h3>Deletion</h3>
              <p className="phase-desc">
                Threshold-based: drop below score floor, protect top N%. Dry-run mode previews changes before
                committing.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="fn">compress</span>(dry_run=<span class="kw">True</span>)

<span class="cm">──────────────────────────────────</span>
  <span class="hi">[DRY RUN] Compression Preview</span>
<span class="cm">──────────────────────────────────</span>
  Total memories:     <span class="num">25</span>
  Protected (top 20%):<span class="num"> 5</span>
  Below threshold:    <span class="num"> 3</span>
  <span class="kw">Would delete:</span>       <span class="num"> 3</span>
  Remaining:          <span class="num">22</span>
<span class="cm">──────────────────────────────────</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 3 ? " active" : ""}`} data-phase="3">
              <span className="phase-badge">Phase 4</span>
              <h3>Merging</h3>
              <p className="phase-desc">
                HDBSCAN clustering + cosine similarity. Near-duplicates (&gt;0.92) merged into one, metadata
                preserved.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="cm"># Detected merge group (similarity: 0.96)</span>
<span class="hi">Group:</span>
  <span class="str">"Paris is the capital of France"</span>
  <span class="str">"The capital of France is Paris"</span>
  <span class="str">"France's capital city is Paris"</span>

<span class="kw">→ Merged into 1 memory:</span>
  <span class="str">"Paris is the capital of France"</span>
  <span class="cm">  tags: merged | sources: 3 | acc: 12</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 4 ? " active" : ""}`} data-phase="4">
              <span className="phase-badge">Phase 5</span>
              <h3>Summarization</h3>
              <p className="phase-desc">
                Related clusters (0.75–0.92 similarity) sent to LLM, replaced with a concise summary memory.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="cm"># Cluster: "France" (4 memories, avg sim: 0.83)</span>
<span class="hi">Input:</span>
  <span class="str">"Paris is the capital of France"</span>
  <span class="str">"The Eiffel Tower is in Paris"</span>
  <span class="str">"France hosted the 1900 Olympics"</span>
  <span class="str">"The 1924 Olympics were in Paris"</span>

<span class="kw">→ Summary:</span>
  <span class="str">"Paris is France's capital, hosting the Eiffel Tower</span>
   <span class="str">and the 1900 &amp; 1924 Olympic Games"</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 5 ? " active" : ""}`} data-phase="5">
              <span className="phase-badge">Phase 6</span>
              <h3>Evaluation</h3>
              <p className="phase-desc">
                NDCG, MRR, false deletion rate, semantic coverage. Quantify compression quality with a suite of
                metrics.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="hi">Evaluation Results</span>
<span class="cm">──────────────────────────────────</span>
  NDCG@5:          <span class="num">0.824</span>  <span class="str">✓</span>
  MRR:             <span class="num">0.750</span>  <span class="str">✓</span>
  False Deletions: <span class="num">0.000</span>  <span class="str">✓</span>
  Sem. Coverage:   <span class="num">1.000</span>  <span class="str">✓</span>
<span class="cm">──────────────────────────────────</span>
  <span class="kw">Passed:</span> <span class="str">✓ All metrics above threshold</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 6 ? " active" : ""}`} data-phase="6">
              <span className="phase-badge">Phase 7</span>
              <h3>Tuning</h3>
              <p className="phase-desc">
                A/B test compression configs. Compare conservative vs aggressive vs balanced strategies.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="hi">Strategy Comparison</span>
<span class="cm">──────────────────────────────────────────</span>
  <span class="kw">conservative</span>  NDCG: <span class="num">0.824</span>  Reduction: <span class="num">0.18</span>
  <span class="hi">balanced</span>      NDCG: <span class="num">0.810</span>  Reduction: <span class="num">0.32</span>
  aggressive    NDCG: <span class="num">0.695</span>  Reduction: <span class="num">0.54</span>
<span class="cm">──────────────────────────────────────────</span>

  <span class="kw">Best (balanced):</span> <span class="str">conservative</span>
  <span class="cm">Highest NDCG with meaningful compression</span>`,
                }}
              />
            </div>
          </div>
        </div>
      </section>

      <section className="features reveal" id="features">
        <div className="section-label">Capabilities</div>
        <h2 className="section-title">Everything You Need</h2>
        <div className="features-grid">
          <div className="feature-card">
            <span className="feature-icon" aria-hidden="true">
              <Brain size={26} strokeWidth={2} />
            </span>
            <h3>Local Embeddings</h3>
            <p>sentence-transformers running locally. No API key needed, no data leaves your machine.</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon" aria-hidden="true">
              <Database size={26} strokeWidth={2} />
            </span>
            <h3>ChromaDB Vector Store</h3>
            <p>Persistent, cosine similarity search with metadata filtering and collection management.</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon" aria-hidden="true">
              <ShieldCheck size={26} strokeWidth={2} />
            </span>
            <h3>Dry-Run by Default</h3>
            <p>Preview every compression operation before committing. No surprises, no lost memories.</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon" aria-hidden="true">
              <BarChart3 size={26} strokeWidth={2} />
            </span>
            <h3>Composite Scoring</h3>
            <p>Weighted combination of recency, access frequency, retrieval rank, and semantic uniqueness.</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon" aria-hidden="true">
              <Zap size={26} strokeWidth={2} />
            </span>
            <h3>Background Scheduler</h3>
            <p>Runs compression async on a configurable interval. Never blocks the agent&apos;s main loop.</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon" aria-hidden="true">
              <Bird size={26} strokeWidth={2} />
            </span>
            <h3>Canary Protection</h3>
            <p>Inject test memories and verify they survive compression. Catch regressions before they matter.</p>
          </div>
        </div>
      </section>

      <section className="architecture reveal">
        <div className="section-label">System Design</div>
        <h2 className="section-title">How the System Fits Together</h2>
        <div className="arch-diagram">
          <div className="arch-vert-container">
            <div className="arch-row">
              <div className="arch-box">Agent</div>
              <span className="arch-arrow" aria-hidden>
                <ArrowRight strokeWidth={2} />
              </span>
              <div className="arch-box primary">MemoryWriter</div>
              <span className="arch-arrow" aria-hidden>
                <ArrowRight strokeWidth={2} />
              </span>
              <div className="arch-box">ChromaDB</div>
            </div>
            <div className="arch-divider" />
            <div className="arch-row">
              <div className="arch-box">Telemetry</div>
              <span className="arch-arrow" aria-hidden>
                <ArrowRight strokeWidth={2} />
              </span>
              <div className="arch-box primary">Scheduler</div>
            </div>
            <div className="arch-divider" />
            <div className="arch-row">
              <div className="arch-group">
                <div className="arch-box">Deletion</div>
                <div className="arch-box">Merging</div>
                <div className="arch-box">Summarization</div>
              </div>
            </div>
            <div className="arch-divider" />
            <div className="arch-row">
              <div className="arch-box primary">Evaluator</div>
              <span className="arch-arrow" aria-hidden>
                <ArrowRight strokeWidth={2} />
              </span>
              <div className="arch-box primary">Tuner</div>
            </div>
          </div>
        </div>
      </section>

      <footer>
        <div className="footer-inner">
          <div className="footer-brand">
            <a href="#" className="logo" aria-label="MemComp home">
              <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" width="22" height="22">
                <rect x="2" y="2" width="24" height="24" rx="6" stroke="#3c6e71" strokeWidth="2" />
                <path
                  d="M9 9h2v2H9zM13 9h2v2h-2zM17 9h2v2h-2zM9 13h2v2H9zM13 13h2v2h-2zM17 13h2v2h-2zM11 17h6v2h-6z"
                  fill="#6dafb4"
                />
                <circle cx="14" cy="14" r="1" fill="#ffffff" />
              </svg>
              MemComp
            </a>
            <span className="footer-tagline">Agent Memory Compression System</span>
          </div>
          <ul className="footer-links">
            <li>
              <a href="#" className="nav-link-icon">
                <Github size={15} strokeWidth={2} aria-hidden />
                GitHub
              </a>
            </li>
            <li>
              <a href="#" className="nav-link-icon">
                <BookOpen size={15} strokeWidth={2} aria-hidden />
                Docs
              </a>
            </li>
            <li>
              <a href="#" className="nav-link-icon">
                <Scale size={15} strokeWidth={2} aria-hidden />
                MIT License
              </a>
            </li>
          </ul>
          <span className="footer-built">Built with Claude Code</span>
        </div>
      </footer>
    </>
  );
}
