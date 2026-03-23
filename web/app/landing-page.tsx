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
  Scale,
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
            Gilial
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
                Docs
              </a>
            </li>
          </ul>
        </div>
      </nav>

      <section className="hero" ref={heroRef}>
        <h1>
          <span className="gradient-text">
            <TextType
              text="What should your agent forget?"
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
          Gilial merges similar memories, deletes low-value ones, and summarizes clusters to
          keep your agent&apos;s memory lean and fast.
        </p>
      </section>

      <section className="problem reveal">
        <div className="section-label">The Challenge</div>
        <h2 className="section-title">The Problem with Agent Memory</h2>
        <div className="problem-grid">
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <Layers size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Unbounded Growth</h3>
            <p>
              Vector DBs fill up with redundant, low-signal memories. Retrieval gets slower and noisier over
              time.
            </p>
          </BorderGlow>
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <Trash2 size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>No Garbage Collection</h3>
            <p>
              Agents store everything but forget nothing intentionally. There&apos;s no mechanism to prune what
              no longer matters.
            </p>
          </BorderGlow>
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <AlertCircle size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Catastrophic Forgetting</h3>
            <p>Naive deletion destroys critical context. You need compression that preserves what matters.</p>
          </BorderGlow>
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
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Brain size={26} strokeWidth={2} />
            </span>
            <h3>Local Embeddings</h3>
            <p>sentence-transformers running locally. No API key needed, no data leaves your machine.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Database size={26} strokeWidth={2} />
            </span>
            <h3>ChromaDB Vector Store</h3>
            <p>Persistent, cosine similarity search with metadata filtering and collection management.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <ShieldCheck size={26} strokeWidth={2} />
            </span>
            <h3>Dry-Run by Default</h3>
            <p>Preview every compression operation before committing. No surprises, no lost memories.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <BarChart3 size={26} strokeWidth={2} />
            </span>
            <h3>Composite Scoring</h3>
            <p>Weighted combination of recency, access frequency, retrieval rank, and semantic uniqueness.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Zap size={26} strokeWidth={2} />
            </span>
            <h3>Background Scheduler</h3>
            <p>Runs compression async on a configurable interval. Never blocks the agent&apos;s main loop.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Bird size={26} strokeWidth={2} />
            </span>
            <h3>Canary Protection</h3>
            <p>Inject test memories and verify they survive compression. Catch regressions before they matter.</p>
          </BorderGlow>
        </div>
      </section>
    </>
  );
}