import { useEffect, useRef } from 'react';

// ── Spec cards data ──────────────────────────────────────────────────────────
const SPECS = [
  { value: '8 Channels',  label: 'Simultaneous EEG acquisition' },
  { value: '24-bit ADC',  label: 'Medical-grade signal resolution' },
  { value: '250 SPS',     label: 'Real-time sampling rate' },
  { value: '< 1µV',       label: 'Input-referred noise' },
];

// ── Comparison table data ────────────────────────────────────────────────────
const COMPARISON_ROWS = [
  { feature: 'Invasiveness', ego: 'Non-invasive', neuralink: 'Invasive',      openbci: 'Non-invasive' },
  { feature: 'Cost',         ego: '$500',          neuralink: '$10k+',         openbci: '$2k'          },
  { feature: 'Channels',     ego: '8',             neuralink: '1,024',         openbci: '8 – 16'       },
  { feature: 'Form Factor',  ego: 'Ear-mounted',   neuralink: 'Implant',       openbci: 'Headset'      },
  { feature: 'FDA Status',   ego: 'Pending',       neuralink: 'Approved',      openbci: 'Research'     },
];

// ── Roadmap phases ───────────────────────────────────────────────────────────
const ROADMAP = [
  { phase: 'Phase 1', title: 'Software Prototype',    date: 'April 2026',  done: true  },
  { phase: 'Phase 2', title: 'Hardware Prototype',    date: 'Q3 2026',     done: false },
  { phase: 'Phase 3', title: 'Clinical Validation',   date: 'Q1 2027',     done: false },
  { phase: 'Phase 4', title: 'Consumer Launch',       date: 'Q4 2027',     done: false },
];

// ── BOM items ────────────────────────────────────────────────────────────────
const BOM = [
  { item: 'ADS1299 EEG chip',   price: '$50'  },
  { item: 'Custom ear molds',   price: '$30'  },
  { item: 'Bluetooth module',   price: '$15'  },
  { item: 'Flex PCB',           price: '$20'  },
  { item: 'Assembly & testing', price: '$50'  },
];

// ── Hook: trigger .slide-up on each .spec-section when it enters viewport ───
function useScrollReveal(containerRef) {
  useEffect(() => {
    const sections = containerRef.current?.querySelectorAll('.spec-section');
    if (!sections?.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('slide-up');
            observer.unobserve(entry.target); // animate once
          }
        });
      },
      { threshold: 0.1 }
    );

    sections.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [containerRef]);
}

/**
 * HardwareSpecs — Static concept & vision page for the E.G.O. Ear device.
 *
 * Sections:
 *   1. Hero with 3D concept render placeholder
 *   2. ADS1299 chip spec cards
 *   3. Competitor comparison table
 *   4. Development roadmap timeline
 *   5. Estimated Bill of Materials
 */
export default function HardwareSpecs() {
  const wrapperRef = useRef(null);
  useScrollReveal(wrapperRef);

  return (
    <main className="hardware-wrapper" ref={wrapperRef}>

      {/* ── Section 1: Hero ──────────────────────────────────────────────── */}
      <section className="spec-section" aria-labelledby="hero-heading">
        <p className="spec-section-title">Concept Device</p>
        <h1 id="hero-heading">The E.G.O. Ear</h1>
        <p style={{ marginTop: '8px', marginBottom: '32px', maxWidth: '560px' }}>
          Next-generation ear-mounted EEG neural interface — bringing medical-grade
          brain-computer interaction to everyday form factors.
        </p>

        {/* 3D Concept Render placeholder */}
        <div className="concept-render" role="img" aria-label="3D concept render placeholder">
          <div className="render-icon" aria-hidden="true">🦻</div>
          <span>3D Concept Render</span>
          <span style={{ fontSize: '0.7rem', letterSpacing: '1px', opacity: 0.5 }}>
            HARDWARE PROTOTYPE — Q3 2026
          </span>
          {/* Decorative scan line */}
          <div style={{
            position:   'absolute',
            left:       0,
            right:      0,
            height:     '1px',
            background: 'linear-gradient(to right, transparent, rgba(0,212,255,0.4), transparent)',
            animation:  'scanLine 3s linear infinite',
          }} aria-hidden="true" />
        </div>
      </section>

      {/* ── Section 2: Chip Specs ─────────────────────────────────────────── */}
      <section className="spec-section" aria-labelledby="chip-heading">
        <p className="spec-section-title">Core Silicon</p>
        <h2 id="chip-heading">ADS1299 — The Heart of E.G.O.</h2>
        <p style={{ marginBottom: '24px' }}>
          Texas Instruments' gold-standard EEG front-end, used in clinical
          research and consumer BCIs alike.
        </p>

        <div className="spec-grid">
          {SPECS.map(({ value, label }) => (
            <div key={value} className="spec-card">
              <div className="spec-value">{value}</div>
              <div className="spec-label">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Section 3: Comparison Table ───────────────────────────────────── */}
      <section className="spec-section" aria-labelledby="compare-heading">
        <p className="spec-section-title">Market Position</p>
        <h2 id="compare-heading">How We Compare</h2>
        <p style={{ marginBottom: '24px' }}>
          E.G.O. targets the gap between expensive research rigs and inaccessible
          implanted devices — a wearable, affordable BCI for the real world.
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table className="comparison-table" aria-label="Competitor comparison">
            <thead>
              <tr>
                <th>Feature</th>
                <th className="our-col">E.G.O. ✦</th>
                <th>Neuralink</th>
                <th>OpenBCI</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map(({ feature, ego, neuralink, openbci }) => (
                <tr key={feature}>
                  <td>{feature}</td>
                  <td className="our-val">{ego}</td>
                  <td>{neuralink}</td>
                  <td>{openbci}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Section 4: Roadmap ────────────────────────────────────────────── */}
      <section className="spec-section" aria-labelledby="roadmap-heading">
        <p className="spec-section-title">Timeline</p>
        <h2 id="roadmap-heading">Development Roadmap</h2>

        <ol className="roadmap-list" aria-label="Development phases">
          {ROADMAP.map(({ phase, title, date, done }) => (
            <li key={phase} className={`roadmap-item${done ? ' done' : ''}`}>
              <div>
                <p className="phase-number">{phase}</p>
                <p className="phase-title">
                  {title}{done && <span aria-label="completed"> ✅</span>}
                </p>
                <p className="phase-date">{date}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* ── Section 5: BOM ────────────────────────────────────────────────── */}
      <section className="spec-section" aria-labelledby="bom-heading">
        <p className="spec-section-title">Bill of Materials</p>
        <h2 id="bom-heading">Estimated Build Cost</h2>
        <p style={{ marginBottom: '24px' }}>
          Per-unit estimate at prototype quantities. Target retail price: ~$500.
        </p>

        <div className="bom-list">
          {BOM.map(({ item, price }) => (
            <div key={item} className="bom-row">
              <span className="bom-item">{item}</span>
              <span className="bom-price">{price}</span>
            </div>
          ))}

          {/* Total row */}
          <div className="bom-row bom-total">
            <span className="bom-item">
              Total cost per prototype unit
            </span>
            <span className="bom-price">~$165</span>
          </div>
        </div>

        <p style={{
          marginTop:   '16px',
          fontSize:    '0.78rem',
          color:       'var(--text-muted)',
          fontFamily:  'var(--font-heading)',
          letterSpacing: '0.3px',
        }}>
          * Prices are indicative. Final BOM will vary with supplier negotiations
          and production volume. Retail target remains $500 to cover R&amp;D and certification.
        </p>
      </section>

    </main>
  );
}
