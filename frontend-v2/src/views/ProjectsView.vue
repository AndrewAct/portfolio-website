<script setup lang="ts">
const features = [
  {
    label: 'Live market data ingestion',
    desc: 'Binance WebSocket streams real-time L2 order book data — 5M+ ticks/day across 50 trading pairs'
  },
  {
    label: 'Stateful stream processing',
    desc: 'Apache Flink computes spread, imbalance, microprice, and 1-minute OHLCV with sub-second latency'
  },
  {
    label: 'Replayable by design',
    desc: 'Apache Iceberg on MinIO + Redpanda/Kafka — full event history is immutable and replayable at any point in time'
  },
  {
    label: 'Analytics modeling with dbt',
    desc: 'Layered transformations over Trino from raw ticks to API-ready marts — <30s end-to-end freshness'
  },
  {
    label: 'Production observability',
    desc: 'Prometheus metrics, Grafana dashboards, and Postgres CDC via Debezium for full pipeline visibility'
  }
]

const stack = ['Kafka', 'PyFlink', 'Iceberg', 'dbt', 'Trino', 'FastAPI', 'Grafana', 'Debezium', 'MinIO']
</script>

<template>
  <div class="page">
    <img class="bg" src="/assets/images/homepage_image.jpg" alt="" />
    <div class="overlay" />

    <a href="/" class="back-btn">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      Home
    </a>

    <div class="stage">
      <div class="card">
        <div class="badge">
          <span class="live-dot" />
          Live &nbsp;·&nbsp; AI &nbsp;·&nbsp; Finance &nbsp;·&nbsp; Real-time
        </div>

        <h1 class="title">TickSense</h1>
        <p class="subtitle">Real-time crypto market lakehouse, built end-to-end</p>

        <div class="rule" />

        <ul class="features">
          <li v-for="f in features" :key="f.label" class="feat">
            <span class="feat-dot" />
            <p>
              <span class="feat-label">{{ f.label }}</span>
              <span class="feat-sep"> — </span>
              <span class="feat-desc">{{ f.desc }}</span>
            </p>
          </li>
        </ul>

        <div class="stack">
          <span v-for="s in stack" :key="s" class="chip">{{ s }}</span>
        </div>

        <a href="https://ticksense.ai" target="_blank" rel="noopener noreferrer" class="cta">
          Visit Project
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  width: 100vw;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-x: hidden;
}

.bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  pointer-events: none;
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(6, 8, 18, 0.54);
  z-index: 1;
  pointer-events: none;
}

.back-btn {
  position: fixed;
  top: 1.6rem;
  left: 1.6rem;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 1.1rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 100px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
  letter-spacing: 0.01em;

  &:hover {
    background: rgba(255, 255, 255, 0.18);
    color: #fff;
  }
}

.stage {
  position: relative;
  z-index: 2;
  padding: 7rem 1.5rem 4rem;
  width: 100%;
  display: flex;
  justify-content: center;
}

/* ── Glass Card ─────────────────────────────────── */
.card {
  width: 100%;
  max-width: 640px;
  padding: 3rem 3.2rem;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.09);
  backdrop-filter: blur(32px) saturate(190%);
  -webkit-backdrop-filter: blur(32px) saturate(190%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow:
    0 40px 80px rgba(0, 0, 0, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 -1px 0 rgba(0, 0, 0, 0.08);
  animation: rise 0.72s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(28px) scale(0.99); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Badge ──────────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 5px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.17);
  border-radius: 100px;
  font-size: 0.77rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.72);
  letter-spacing: 0.03em;
  margin-bottom: 1.3rem;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 8px #4ade8088;
  animation: glow 2.5s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px #4ade8088; }
  50%       { opacity: 0.55; box-shadow: 0 0 18px #4ade80cc; }
}

/* ── Title / Subtitle ───────────────────────────── */
.title {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: clamp(3.2rem, 8vw, 5rem);
  font-weight: 700;
  font-style: italic;
  color: #fff;
  letter-spacing: 0.01em;
  line-height: 1.0;
  margin: 0 0 0.55rem;
}

.subtitle {
  font-size: 1.05rem;
  color: rgba(255, 255, 255, 0.58);
  line-height: 1.5;
  margin: 0;
}

/* ── Rule ───────────────────────────────────────── */
.rule {
  height: 1px;
  background: rgba(255, 255, 255, 0.11);
  margin: 1.8rem 0;
}

/* ── Features ───────────────────────────────────── */
.features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.feat {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.feat-dot {
  flex-shrink: 0;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
  margin-top: 0.48rem;
}

.feat p { margin: 0; line-height: 1.55; }

.feat-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
}

.feat-sep {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.3);
}

.feat-desc {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.52);
}

/* ── Stack chips ────────────────────────────────── */
.stack {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 2rem;
}

.chip {
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 100px;
  font-size: 0.77rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.68);
  letter-spacing: 0.02em;
}

/* ── CTA ────────────────────────────────────────── */
.cta {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.8rem;
  background: rgba(255, 255, 255, 0.92);
  color: #111;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 100px;
  text-decoration: none;
  transition: background 0.18s, box-shadow 0.18s, transform 0.18s;

  svg { transition: transform 0.18s; }

  &:hover {
    background: #fff;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.42);
    transform: translateY(-1px);

    svg { transform: translateX(4px); }
  }
}

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 640px) {
  .card { padding: 2rem 1.6rem; border-radius: 20px; }
  .title { letter-spacing: -1px; }
}
</style>
