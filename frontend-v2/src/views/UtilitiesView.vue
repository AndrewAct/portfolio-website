<script setup lang="ts">
import { ref } from 'vue'
import HoroscopeWidget from '../widgets/HoroscopeWidget.vue'
import UrlShortenerWidget from '../widgets/UrlShortenerWidget.vue'

const active = ref<'horoscope' | 'shortener'>('horoscope')
</script>

<template>
  <div class="utilities-container">
    <div class="decoration circle-1"></div>
    <div class="decoration circle-2"></div>

    <a href="/" class="back-button">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      <span>Home</span>
    </a>

    <div class="content-container">
      <h1 class="page-title">Utilities</h1>
      <p class="page-subtitle">Select a utility to get started</p>

      <div class="utility-tabs">
        <button class="tab-btn" :class="{ active: active === 'horoscope' }" @click="active = 'horoscope'">
          <span class="icon">♈</span>
          Horoscope
        </button>
        <button class="tab-btn" :class="{ active: active === 'shortener' }" @click="active = 'shortener'">
          <span class="icon">🔗</span>
          URL Shortener
        </button>
      </div>

      <div class="utility-panel">
        <div class="panel-content" v-if="active === 'shortener'">
          <UrlShortenerWidget />
        </div>
        <div class="panel-content" v-else>
          <HoroscopeWidget />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use './utilities-styles.scss' as *;
</style>
