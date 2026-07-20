<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { unsubscribe, extractErrorMessage } from '../services/horoscopeSubscriptions'

const route = useRoute()
const token = typeof route.query.token === 'string' ? route.query.token : ''

type Status = 'idle' | 'loading' | 'unsubscribed' | 'error'
const status = ref<Status>(token ? 'idle' : 'error')
const errorMessage = ref(token ? '' : 'This link is missing its token.')

async function onConfirm() {
  status.value = 'loading'
  try {
    await unsubscribe(token)
    status.value = 'unsubscribed'
  } catch (e) {
    status.value = 'error'
    errorMessage.value = extractErrorMessage(e, 'This link is invalid or has expired.')
  }
}
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
      <div class="glass-panel status-panel">
        <div class="panel-header">
          <h1 class="panel-title">Horoscope</h1>
          <p class="panel-subtitle">Unsubscribe from daily emails</p>
        </div>

        <div class="status-body">
          <template v-if="status === 'idle' || status === 'loading'">
            <p>Are you sure you want to stop receiving your daily horoscope emails?</p>
            <div class="status-actions">
              <button
                type="button"
                class="submit-btn"
                :disabled="status === 'loading'"
                @click="onConfirm"
              >
                <span v-if="status !== 'loading'">Confirm unsubscribe</span>
                <span v-else class="loading-spinner"></span>
              </button>
            </div>
          </template>

          <p v-else-if="status === 'unsubscribed'" class="status-success">
            You've been unsubscribed. You won't receive any more daily horoscope emails.
          </p>

          <p v-else class="status-error">{{ errorMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use './glass-page-styles.scss' as *;
@use './horoscope-status-styles.scss' as *;
@use './horoscope-styles.scss' as *;
</style>
