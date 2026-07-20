<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { confirmSubscription, extractErrorMessage } from '../services/horoscopeSubscriptions'

const route = useRoute()
const token = typeof route.query.token === 'string' ? route.query.token : ''

type Status = 'loading' | 'confirmed' | 'error'
const status = ref<Status>('loading')
const errorMessage = ref('')

onMounted(async () => {
  if (!token) {
    status.value = 'error'
    errorMessage.value = 'This confirmation link is missing its token.'
    return
  }
  try {
    await confirmSubscription(token)
    status.value = 'confirmed'
  } catch (e) {
    status.value = 'error'
    errorMessage.value = extractErrorMessage(e, 'This confirmation link is invalid or has expired.')
  }
})
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
          <p class="panel-subtitle">Daily email confirmation</p>
        </div>

        <div class="status-body">
          <p v-if="status === 'loading'">Confirming your subscription…</p>
          <p v-else-if="status === 'confirmed'" class="status-success">
            You're all set! Your daily horoscope will start arriving at the time you chose.
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
</style>
