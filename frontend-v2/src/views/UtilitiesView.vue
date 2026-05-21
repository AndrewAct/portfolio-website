<script setup lang="ts">
import { ref } from 'vue'
import HoroscopeWidget from '../widgets/HoroscopeWidget.vue'
import UrlShortenerWidget from '../widgets/UrlShortenerWidget.vue'

const active = ref<'horoscope' | 'shortener'>('horoscope')
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
      <div class="glass-panel">
        <div class="panel-header">
          <h1 class="panel-title">Utilities</h1>
          <p class="panel-subtitle">Tools for everyday curiosities</p>
        </div>

        <div class="tabs">
          <button
            class="tab"
            :class="{ active: active === 'horoscope' }"
            @click="active = 'horoscope'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            Horoscope
          </button>
          <button
            class="tab"
            :class="{ active: active === 'shortener' }"
            @click="active = 'shortener'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
            </svg>
            URL Shortener
          </button>
        </div>

        <div class="widget-area">
          <div v-if="active === 'horoscope'" class="widget-fade">
            <HoroscopeWidget />
          </div>
          <div v-else class="widget-fade">
            <UrlShortenerWidget />
          </div>
        </div>
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
  align-items: flex-start;
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
  background: rgba(6, 8, 18, 0.52);
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
  padding: 6rem 1.5rem 4rem;
  width: 100%;
  display: flex;
  justify-content: center;
}

/* ── Glass Panel ────────────────────────────────── */
.glass-panel {
  width: 100%;
  max-width: 780px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.09);
  backdrop-filter: blur(32px) saturate(190%);
  -webkit-backdrop-filter: blur(32px) saturate(190%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 40px 80px rgba(0, 0, 0, 0.36),
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    inset 0 -1px 0 rgba(0, 0, 0, 0.06);
  overflow: hidden;
  animation: rise 0.72s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(28px) scale(0.99); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Panel Header ───────────────────────────────── */
.panel-header {
  padding: 2.4rem 2.6rem 0;
}

.panel-title {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 2.8rem;
  font-weight: 700;
  font-style: italic;
  color: #fff;
  letter-spacing: 0.01em;
  line-height: 1.0;
  margin: 0 0 0.3rem;
}

.panel-subtitle {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.52);
  margin: 0 0 1.8rem;
}

/* ── Tabs ───────────────────────────────────────── */
.tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0 2.6rem 1.6rem;
}

.tab {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 1.25rem;
  font-size: 0.88rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 100px;
  color: rgba(255, 255, 255, 0.58);
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
  letter-spacing: 0.01em;

  svg { stroke: currentColor; }

  &:hover:not(.active) {
    background: rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.82);
    border-color: rgba(255, 255, 255, 0.22);
  }

  &.active {
    background: rgba(255, 255, 255, 0.18);
    border-color: rgba(255, 255, 255, 0.32);
    color: #fff;
    font-weight: 600;
  }
}

/* ── Widget Area ────────────────────────────────── */
.widget-area {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2rem 2.6rem 2.6rem;
}

.widget-fade {
  animation: fadeSlide 0.32s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes fadeSlide {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 640px) {
  .glass-panel { border-radius: 20px; }
  .panel-header { padding: 1.8rem 1.6rem 0; }
  .tabs { padding: 0 1.6rem 1.4rem; }
  .widget-area { padding: 1.6rem 1.6rem 2rem; }
  .panel-title { font-size: 2rem; }
}
</style>
