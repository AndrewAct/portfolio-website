<script setup lang="ts">
import { computed, ref } from 'vue'

import { projects } from '../data/projects'

const currentIndex = ref(0)

const project = computed(() => projects[currentIndex.value]!)
const projectNumber = computed(() => String(currentIndex.value + 1).padStart(2, '0'))
const projectTotal = String(projects.length).padStart(2, '0')
const previousProjectName = computed(
  () => projects[(currentIndex.value - 1 + projects.length) % projects.length]!.name
)
const nextProjectName = computed(
  () => projects[(currentIndex.value + 1) % projects.length]!.name
)

function changeProject(direction: number) {
  currentIndex.value = (currentIndex.value + direction + projects.length) % projects.length
}
</script>

<template>
  <div class="page">
    <img class="bg" src="/assets/images/homepage_image.jpg" alt="" />
    <div class="overlay" />

    <a href="/" class="back-btn">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M19 12H5M12 19l-7-7 7-7" />
      </svg>
      Home
    </a>

    <main class="stage">
      <article :key="project.id" class="card">
        <nav class="project-nav" aria-label="Project navigation">
          <span class="project-count" aria-live="polite">{{ projectNumber }} / {{ projectTotal }}</span>
          <button type="button" class="nav-btn" :aria-label="`Previous project: ${previousProjectName}`" @click="changeProject(-1)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <button type="button" class="nav-btn" :aria-label="`Next project: ${nextProjectName}`" @click="changeProject(1)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </nav>

        <div class="badge">
          <span class="live-dot" />
          {{ project.categories.join(' · ') }}
        </div>

        <div class="name-row">
          <h1 class="title">{{ project.name }}</h1>
          <span v-if="project.nameZh" class="name-zh">{{ project.nameZh }}</span>
        </div>

        <div v-if="project.pronunciation" class="dictionary-entry">
          <span>{{ project.pronunciation }}</span>
          <span class="word-divider">·</span>
          <em>{{ project.partOfSpeech }}</em>
        </div>
        <div v-if="project.originalMeaning || project.modernMeaning" class="definitions">
          <p v-if="project.originalMeaning">
            <span class="sense-label">Originally</span>
            {{ project.originalMeaning }}
          </p>
          <p v-if="project.modernMeaning">
            <span class="sense-label">Now</span>
            {{ project.modernMeaning }}
          </p>
        </div>
        <p class="subtitle">{{ project.subtitle }}</p>

        <div class="rule" />

        <ul class="features">
          <li v-for="feature in project.features" :key="feature.label" class="feature">
            <span class="feature-dot" />
            <p>
              <span class="feature-label">{{ feature.label }}</span>
              <span class="feature-separator"> — </span>
              <span class="feature-description">{{ feature.description }}</span>
            </p>
          </li>
        </ul>

        <div class="stack" aria-label="Technology stack">
          <span v-for="technology in project.stack" :key="technology" class="chip">{{ technology }}</span>
        </div>

        <a :href="project.url" target="_blank" rel="noopener noreferrer" class="cta" :aria-label="`Visit ${project.name}`">
          Visit Project
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </a>
      </article>
    </main>
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

.card {
  position: relative;
  width: 100%;
  max-width: 720px;
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
  animation: rise 0.62s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(22px) scale(0.99); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.project-nav {
  position: absolute;
  top: 2.5rem;
  right: 3rem;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.project-count {
  margin-right: 0.25rem;
  color: rgba(255, 255, 255, 0.46);
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.08em;
}

.nav-btn {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  padding: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.17);
  color: rgba(255, 255, 255, 0.74);
  transition: background 0.18s, border-color 0.18s, color 0.18s, transform 0.18s;

  &:hover {
    background: rgba(255, 255, 255, 0.17);
    border-color: rgba(255, 255, 255, 0.28);
    color: #fff;
    transform: translateY(-1px);
  }

  &:focus-visible {
    outline: 2px solid rgba(255, 255, 255, 0.92);
    outline-offset: 3px;
  }
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  max-width: calc(100% - 12rem);
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
  flex: 0 0 auto;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 8px #4ade8088;
  animation: glow 2.5s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px #4ade8088; }
  50% { opacity: 0.55; box-shadow: 0 0 18px #4ade80cc; }
}

.name-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.9rem;
}

.title {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: clamp(3.2rem, 8vw, 5rem);
  font-weight: 700;
  font-style: italic;
  color: #fff;
  letter-spacing: 0.01em;
  line-height: 1;
  margin: 0 0 0.55rem;
}

.name-zh {
  font-family: 'Songti SC', 'STSong', serif;
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.45rem;
  letter-spacing: 0.12em;
}

.dictionary-entry {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin: -0.05rem 0 0.55rem;
  color: rgba(255, 255, 255, 0.68);
  font-size: 0.84rem;
  letter-spacing: 0.03em;
}

.dictionary-entry em { color: rgba(255, 255, 255, 0.46); }
.word-divider { color: rgba(255, 255, 255, 0.24); }

.definitions {
  max-width: 650px;
  margin: 0 0 0.7rem;
  color: rgba(255, 255, 255, 0.78);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.92rem;
  font-weight: 400;
  line-height: 1.55;
}

.definitions p { margin: 0; }
.definitions p + p { margin-top: 0.2rem; }

.sense-label {
  margin-right: 0.35rem;
  color: rgba(255, 255, 255, 0.45);
  font-family: system-ui, sans-serif;
  font-size: 0.68rem;
  font-style: normal;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subtitle {
  font-size: 1.02rem;
  color: rgba(255, 255, 255, 0.56);
  line-height: 1.5;
  margin: 0;
}

.rule {
  height: 1px;
  background: rgba(255, 255, 255, 0.11);
  margin: 1.65rem 0;
}

.features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.7rem;
  display: flex;
  flex-direction: column;
  gap: 0.76rem;
}

.feature {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.feature-dot {
  flex-shrink: 0;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
  margin-top: 0.48rem;
}

.feature p { margin: 0; line-height: 1.55; }

.feature-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
}

.feature-separator {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.3);
}

.feature-description {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.52);
}

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

  &:focus-visible {
    outline: 2px solid rgba(255, 255, 255, 0.92);
    outline-offset: 3px;
  }
}

@media (max-width: 640px) {
  .stage { padding: 6.2rem 1rem 2.5rem; }
  .card { padding: 5.3rem 1.5rem 2rem; border-radius: 20px; }
  .project-nav { top: 1.5rem; right: 1.5rem; }
  .badge { max-width: 100%; }
  .title { font-size: clamp(2.8rem, 15vw, 4rem); letter-spacing: -1px; }
  .name-zh { font-size: 1.2rem; }
}

@media (prefers-reduced-motion: reduce) {
  .card,
  .live-dot { animation: none; }
}
</style>
