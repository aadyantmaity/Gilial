"use client";

import {
  AlertCircle,
  BarChart3,
  Bird,
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

type Phase = 0 | 1 | 2;


export default function LandingPage() {
  const [phase, setPhase] = useState<Phase>(0);
  const [showNav, setShowNav] = useState(true);
  const heroRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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
      // Hide navbar while scrolling
      setShowNav(false);

      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Show navbar after scrolling stops (800ms idle)
      scrollTimeoutRef.current = setTimeout(() => {
        setShowNav(true);
      }, 100);

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
    return () => {
      window.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  const selectPhase = useCallback((p: Phase) => {
    setPhase(p);
  }, []);

  return (
    <>
      <nav className={!showNav ? "hidden" : ""}>
        <div className="nav-links">
          <button
            onClick={() => document.querySelector(".walkthrough")?.scrollIntoView({ behavior: "smooth" })}
            className="nav-text-link"
          >
            Walkthrough
          </button>
          <button
            onClick={() => document.querySelector(".features")?.scrollIntoView({ behavior: "smooth" })}
            className="nav-text-link"
          >
            Features
          </button>
          <a href="https://github.com/aadyantmaity/Gilial" className="nav-text-link" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
          <a href="https://gilial-docs.vercel.app/" className="nav-text-link" target="_blank" rel="noopener noreferrer">
            Docs
          </a>
        </div>
      </nav>

      <section className="hero" ref={heroRef}>
        <h1>
          <span className="gradient-text">
            <TextType
              text="Compress your vector database"
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
          Reduce storage costs while maintaining search quality. Remove low-scoring vectors, optimize index size, and keep your Pinecone database performant.
        </p>
      </section>

      <section className="problem reveal">
        <div className="section-label">The Problem</div>
        <h2 className="section-title">Why Vector Compression Matters</h2>
        <div className="problem-grid">
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <Layers size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Rising Storage Costs</h3>
            <p>
              Vector indexes grow unbounded. Low-scoring vectors consume storage and slow down queries without adding value.
            </p>
          </BorderGlow>
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <Trash2 size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Query Performance Degradation</h3>
            <p>
              As indexes grow, search latency increases. Larger datasets mean slower nearest-neighbor lookups and higher API costs.
            </p>
          </BorderGlow>
          <BorderGlow className="problem-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <div className="card-icon">
              <AlertCircle size={24} strokeWidth={2} aria-hidden />
            </div>
            <h3>Selective Removal Risk</h3>
            <p>Deleting vectors is risky. You need a smart approach that removes noise while preserving search quality.</p>
          </BorderGlow>
        </div>
      </section>

      <section className="walkthrough reveal" id="walkthrough">
        <div className="section-label">How It Works</div>
        <h2 className="section-title">The Compression Pipeline</h2>
        <p className="section-subtitle" style={{ margin: "0 auto 0" }}>
          Simple three-step vector compression process
        </p>
        <div className="walkthrough-container">
          <div className="stepper" role="tablist" aria-label="Pipeline phases">
            {(
              [
                "Sample Vectors",
                "Score & Analyze",
                "Delete Low-Scoring",
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
              <h3>Sample Vectors</h3>
              <p className="phase-desc">
                Connect to your Pinecone index and sample vectors to analyze compression impact.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="fn">client</span> = <span class="fn">PineconeCompressionClient</span>(
    api_key=<span class="str">"your-key"</span>,
    index_name=<span class="str">"your-index"</span>
)

<span class="cm"># Estimate compression savings</span>
<span class="hi">savings</span> = <span class="hi">client</span>.<span class="fn">estimate_savings</span>()
<span class="cm"># Sampled 100 vectors from index</span>
<span class="cm"># Analysis complete</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 1 ? " active" : ""}`} data-phase="1">
              <h3>Score & Analyze</h3>
              <p className="phase-desc">
                Calculate L2 norm for each vector. Low-scoring vectors are identified as candidates for deletion.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="cm"># Calculate vector norms (L2)</span>
<span class="hi">score: <span class="num">0.945</span></span> <span class="kw">████████████████</span> ← high quality
<span class="hi">score: <span class="num">0.672</span></span> <span class="kw">███████████</span>      ← medium quality

<span class="hi">score: <span class="num">0.156</span></span> <span class="kw">██</span>                 ← low quality (delete)
<span class="hi">score: <span class="num">0.089</span></span> <span class="kw">█</span>                  ← low quality (delete)

<span class="cm">Deletion threshold: 0.34</span>
<span class="cm">Vectors to delete: 261 / 10,000</span>`,
                }}
              />
            </div>

            <div className={`phase-content${phase === 2 ? " active" : ""}`} data-phase="2">
              <h3>Delete Low-Scoring</h3>
              <p className="phase-desc">
                Apply compression with your choice of strategy. Dry-run mode previews impact before committing.
              </p>
              <div
                className="code-block"
                dangerouslySetInnerHTML={{
                  __html: `<span class="cm"># Preview compression (dry-run)</span>
<span class="hi">result</span> = <span class="hi">client</span>.<span class="fn">compress</span>(
    strategy=<span class="str">"balanced"</span>,
    dry_run=<span class="kw">True</span>
)

<span class="cm">──────────────────────────────────</span>
<span class="hi">Compression Results</span>
<span class="cm">──────────────────────────────────</span>
  Original vectors:    <span class="num">10,000</span>
  Vectors to delete:   <span class="num">261</span>
  Final vectors:       <span class="num">9,739</span>
  Storage savings:     <span class="num">2.62%</span>
  Strategy:            <span class="str">balanced</span>
<span class="cm">──────────────────────────────────</span>`,
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
            <h3>Pinecone Integration</h3>
            <p>Native support for Pinecone indexes with simple API client and REST endpoints.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <ShieldCheck size={26} strokeWidth={2} />
            </span>
            <h3>Dry-Run Mode</h3>
            <p>Preview compression impact before applying changes. See exact storage savings and vector reduction estimates.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Brain size={26} strokeWidth={2} />
            </span>
            <h3>L2 Norm Scoring</h3>
            <p>Score vectors using L2 norm (Euclidean magnitude). Simple, deterministic, and fast to calculate.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <BarChart3 size={26} strokeWidth={2} />
            </span>
            <h3>Multiple Strategies</h3>
            <p>Choose between Balanced (default) and Aggressive compression strategies to match your needs.</p>
          </BorderGlow>
          <BorderGlow className="feature-card" borderRadius={16} glowRadius={30} backgroundColor="linear-gradient(135deg, rgba(23, 40, 43, 0.8) 0%, rgba(31, 56, 60, 0.6) 100%)">
            <span className="feature-icon" aria-hidden="true">
              <Zap size={26} strokeWidth={2} />
            </span>
            <h3>Simple API</h3>
            <p>Clean Python client and REST endpoints. Estimate savings, compress, and monitor all from one interface.</p>
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