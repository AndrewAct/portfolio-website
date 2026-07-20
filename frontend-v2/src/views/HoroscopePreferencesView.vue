<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  getPreferences,
  updatePreferences,
  extractErrorMessage,
  type SubscriptionPreferences
} from '../services/horoscopeSubscriptions'

const route = useRoute()
const token = typeof route.query.token === 'string' ? route.query.token : ''

type LoadState = 'loading' | 'ready' | 'error'
const loadState = ref<LoadState>('loading')
const loadError = ref('')

const email = ref('')
const birthdate = ref('')
const gender = ref('female')
const language = ref('en')
const sendTime = ref('08:00')
const timezone = ref('')

const genders = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' }
]
const languages = [
  { value: 'en', label: 'English' },
  { value: 'zh', label: 'Chinese' }
]

const saving = ref(false)
const saveError = ref('')
const saveResult = ref<'updated' | 'confirmation_sent' | null>(null)

onMounted(async () => {
  if (!token) {
    loadState.value = 'error'
    loadError.value = 'This link is missing its token.'
    return
  }
  try {
    const prefs = await getPreferences(token)
    email.value = prefs.email
    birthdate.value = prefs.birthdate
    gender.value = prefs.gender
    language.value = prefs.language
    sendTime.value = prefs.send_time_local.slice(0, 5)
    timezone.value = prefs.timezone
    loadState.value = 'ready'
  } catch (e) {
    loadState.value = 'error'
    loadError.value = extractErrorMessage(e, 'This link is invalid or has expired.')
  }
})

async function onSave() {
  saveError.value = ''
  saveResult.value = null
  saving.value = true
  try {
    const payload: SubscriptionPreferences = {
      email: email.value,
      birthdate: birthdate.value,
      gender: gender.value,
      language: language.value,
      timezone: timezone.value,
      send_time_local: sendTime.value
    }
    const result = await updatePreferences(token, payload)
    saveResult.value = result.status
  } catch (e) {
    saveError.value = extractErrorMessage(e, 'Failed to save preferences. Please try again.')
  } finally {
    saving.value = false
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
          <p class="panel-subtitle">Manage your daily email preferences</p>
        </div>

        <div class="status-body" v-if="loadState === 'loading'">
          <p>Loading your preferences…</p>
        </div>

        <div class="status-body" v-else-if="loadState === 'error'">
          <p class="status-error">{{ loadError }}</p>
        </div>

        <div class="status-body" v-else>
          <template v-if="!saveResult">
            <form @submit.prevent="onSave" class="preferences-form">
              <div class="form-group">
                <label for="pref-email">Email</label>
                <input type="email" id="pref-email" v-model="email" class="form-control" required>
              </div>

              <div class="form-group">
                <label for="pref-birthdate">Birthdate</label>
                <input type="date" id="pref-birthdate" v-model="birthdate" class="form-control" required>
              </div>

              <div class="form-group">
                <label for="pref-gender">Gender</label>
                <select id="pref-gender" v-model="gender" class="form-control">
                  <option v-for="g in genders" :key="g.value" :value="g.value">{{ g.label }}</option>
                </select>
              </div>

              <div class="form-group">
                <label for="pref-language">Language</label>
                <select id="pref-language" v-model="language" class="form-control">
                  <option v-for="l in languages" :key="l.value" :value="l.value">{{ l.label }}</option>
                </select>
              </div>

              <div class="form-group">
                <label for="pref-time">Daily send time</label>
                <input type="time" id="pref-time" v-model="sendTime" class="form-control" required>
                <p class="timezone-hint">Timezone: {{ timezone }}</p>
              </div>

              <div class="status-actions">
                <button type="submit" class="submit-btn" :disabled="saving">
                  <span v-if="!saving">Save changes</span>
                  <span v-else class="loading-spinner"></span>
                </button>
              </div>
            </form>

            <div class="error-container" v-if="saveError">
              <div class="error-message">{{ saveError }}</div>
            </div>
          </template>

          <p v-else-if="saveResult === 'updated'" class="status-success">
            Your preferences have been updated.
          </p>
          <p v-else class="status-success">
            We sent a confirmation link to <span class="status-email">{{ email }}</span> — click it
            to activate your new email address.
          </p>
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
