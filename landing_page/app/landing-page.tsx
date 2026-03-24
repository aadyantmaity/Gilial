"use client";

import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  Bird,
  BookOpen,
  Brain,
  Database,
  Layers,
  ShieldCheck,
  Trash2,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState, useRef } from "react";
import TextType from "@/components/TextType";
import BorderGlow from "@/components/BorderGlow";

type Phase = 0 | 1 | 2 | 3 | 4 | 5 | 6;


export default function LandingPage() {
  const [phase, setPhase] = useState<Phase>(0);
  const heroRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const handleScroll = () => {
      // Apply 3D effects to cards
      const problemCards = document.querySelectorAll(".problem-card");
      const featureCards = document.querySelectorAll(".feature-card");
      const allCards = [...Array.from(problemCards), ...Array.from(featureCards)];

      allCards.forEach((card, index) => {
        const rect = (card as HTMLElement).getBoundingClientRect();
        const cardCenter = rect.top + rect.height / 2;
        const viewportCenter = window.innerHeight / 2;
        const distance = cardCenter - viewportCenter;
        const maxDistance = window.innerHeight;

        // Clamp the rotation to reasonable values
        const rotationX = Math.max(-20, Math.min(20, (distance / maxDistance) * 25));
        const rotationY = (index % 2 === 0 ? -1 : 1) * 12;
        const scale = 1 - Math.abs(distance) / (maxDistance * 2) * 0.05;

        (card as HTMLElement).style.transform = `perspective(1200px) rotateX(${rotationX}deg) rotateY(${rotationY}deg) scale(${scale})`;
      });
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll(); // Call once on mount
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const selectPhase = useCallback((p: Phase) => {
    setPhase(p);
  }, []);

  return (
    <>
      <nav>
        <div className="nav-left">
          <a href="#" className="logo" aria-label="Gilial home">
            <span className="logo-text">Gilial</span>
          </a>
          <ul className="nav-links">
            <li>
              <a href="#walkthrough" className="nav-link">How it Works</a>
            </li>
            <li>
              <a href="#features" className="nav-link">Features</a>
            </li>
          </ul>
        </div>
        <div className="nav-right">
          <a href="#" className="nav-icon-link" aria-label="GitHub" title="GitHub">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 -.5-3 .5s-4.4.5-5.8 0c-1.9-1-3-0.5-3-0.5-.6 1.1-.9 2.35-.9 3.5 0 3.5 3 5.5 6 5.5-.5.5-.9 1.1-1 1.5-.9 0-1.7-.5-2.3-1s-1.1-1.5-1.9-1.5c-.9 0-1.7.5-1.9 1.5-.2 1 .1 1.5.9 2s1.2 1 2 1 1.6.5 2.6.5V22"/>
            </svg>
          </a>
          <a href="#" className="nav-icon-link" aria-label="Documentation" title="Documentation">
            <BookOpen size={18} />
          </a>
        </div>
      </nav>

      <section className="hero" ref={heroRef}>
        <h1>
          <span className="gradient-text">
            <TextType
              text="Clean up your agent's memory"
              as="span"
              typingSpeed={75}
              pauseDuration={3000}
              deletingSpeed={50}
              loop={false}
              showCursor
              cursorCharacter="_"
              className="gradient-text"
            />
          </span>
        </h1>
        <p className="hero-subtitle-fade">
          Connect your vector database and automatically compress memories. Merge duplicates, delete noise, and summarize clusters to keep retrieval fast and relevant.
        </p>
        <div className="hero-ctas">
          <BorderGlow
            className="btn-primary-glow"
            borderRadius={50}
            glowRadius={30}
            backgroundColor="var(--primary)"
          >
            <a href="#" className="btn-primary-inner">
              Get Started
              <ArrowRight size={16} />
            </a>
          </BorderGlow>
        </div>
      </section>

      <section className="problem reveal">
        <div className="section-label">The Problem</div>
        <h2 className="section-title">Why Memory Compression Matters</h2>
        <div className="problem-grid">
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <Layers size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Unbounded Growth</h3>
            <p>
              Vector DBs fill up with redundant, low-signal memories. Retrieval gets slower and noisier as your agent learns.
            </p>
          </BorderGlow>
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <Trash2 size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Manual Management</h3>
            <p>
              No built-in way to prune or consolidate memories. You&apos;re managing noise manually or just ignoring the problem.
            </p>
          </BorderGlow>
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <AlertCircle size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Context Loss</h3>
            <p>Deleting memories is risky. You need compression that keeps what matters while removing the junk.</p>
          </BorderGlow>
        </div>
      </section>

      <section className="walkthrough reveal" id="walkthrough">
        <div className="section-label">How It Works</div>
        <h2 className="section-title">The Compression Pipeline</h2>
        <p className="section-subtitle" style={{ margin: "0 auto 0" }}>
          Seven phases of memory optimization
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
              <h3>Importance Scoring</h3>
              <p className="phase-desc">
                Total score: recency (25%) + access frequency (30%) + retrieval rank (20%) + semantic uniqueness (25%).
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
              <h3>Tuning</h3>
              <p className="phase-desc">
                A/B test compression configs. Compare balanced vs aggressive strategies.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="hi">Strategy Comparison</span>
<span class="cm">──────────────────────────────────────────</span>
  <span class="hi">balanced</span>      NDCG: <span class="num">0.810</span>  Reduction: <span class="num">0.32</span>
  aggressive    NDCG: <span class="num">0.695</span>  Reduction: <span class="num">0.54</span>
<span class="cm">──────────────────────────────────────────</span>

  <span class="kw">Best (balanced):</span> <span class="str">balanced</span>
  <span class="cm">Highest NDCG with meaningful compression</span>`,
                }}
              />
            </div>
          </div>
        </div>
      </section>

      <section className="features reveal" id="features">
        <div className="section-label">Features</div>
        <h2 className="section-title">Built for Developers</h2>
        <div className="features-grid">
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Database size={26} strokeWidth={2} />
            </span>
            <h3>Multi-DB Support</h3>
            <p>Works with Pinecone, Weaviate, Milvus, and any OpenAI-compatible vector database.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <ShieldCheck size={26} strokeWidth={2} />
            </span>
            <h3>Dry-Run First</h3>
            <p>Preview every operation before committing. See exactly what will be merged, summarized, and deleted.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Brain size={26} strokeWidth={2} />
            </span>
            <h3>Smart Clustering</h3>
            <p>HDBSCAN-powered similarity detection. Automatically identifies and merges near-duplicate memories.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <BarChart3 size={26} strokeWidth={2} />
            </span>
            <h3>Scoring Metrics</h3>
            <p>Recency, access frequency, retrieval rank, and semantic uniqueness combined for smart pruning.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Zap size={26} strokeWidth={2} />
            </span>
            <h3>REST API</h3>
            <p>Simple HTTP endpoints to trigger compression, check status, and manage your memory pipeline.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Bird size={26} strokeWidth={2} />
            </span>
            <h3>Open Source</h3>
            <p>Self-hosted or use our managed service. Full transparency, no vendor lock-in.</p>
          </BorderGlow>
        </div>
      </section>
    </>
  );
}