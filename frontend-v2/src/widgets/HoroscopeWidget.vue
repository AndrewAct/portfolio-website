<script setup lang="ts">
import { ref } from 'vue'
import { getHoroscopeByBirthdate, type HoroscopeResponse } from '../services/horoscope'
import html2canvas from 'html2canvas'

const today = new Date()
const maxDate = today.toISOString().split('T')[0]

const loading = ref(false)
const error = ref<string | null>(null)
const horoscope = ref<HoroscopeResponse | null>(null)

const birthdate = ref('')
const gender = ref('female')
const language = ref('en')

const cardRef = ref<HTMLElement | null>(null)

const genders = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' }
]
const languages = [
  { value: 'en', label: 'English' },
  { value: 'zh', label: 'Chinese' },
]

async function onSubmit() {
  error.value = null
  horoscope.value = null
  loading.value = true
  try {
    horoscope.value = await getHoroscopeByBirthdate({ birthdate: birthdate.value, gender: gender.value, language: language.value })
  } catch (e: any) {
    error.value = e?.message ?? 'Failed to fetch horoscope'
  } finally {
    loading.value = false
  }
}

async function downloadHoroscope() {
  if (!cardRef.value) return
  const canvas = await html2canvas(cardRef.value, { backgroundColor: '#ffffff', scale: 2 })
  const dataUrl = canvas.toDataURL('image/png')
  const link = document.createElement('a')
  const sign = horoscope.value?.zodiac_sign ?? 'horoscope'
  link.download = `${sign}-${new Date().toISOString().slice(0,10)}.png`
  link.href = dataUrl
  link.click()
}
</script>

<template>
  <div class="horoscope-container">
    <div class="horoscope-form-card">
      <h2>Daily Horoscope</h2>
      <p class="subtitle">Find out what the stars have in store for you today!</p>

      <form @submit.prevent="onSubmit">
        <div class="form-group">
          <label for="birthdate">Birthdate</label>
          <input type="date" id="birthdate" v-model="birthdate" :max="maxDate" class="form-control" required>
        </div>

        <div class="form-group">
          <label for="gender">Gender</label>
          <select id="gender" v-model="gender" class="form-control">
            <option v-for="g in genders" :key="g.value" :value="g.value">{{ g.label }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="language">Language</label>
          <select id="language" v-model="language" class="form-control">
            <option v-for="l in languages" :key="l.value" :value="l.value">{{ l.label }}</option>
          </select>
        </div>

        <button type="submit" class="submit-btn" :disabled="!birthdate || loading">
          <span v-if="!loading">Get Horoscope</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </form>
    </div>

    <div class="horoscope-result" v-if="horoscope">
      <div class="horoscope-card" ref="cardRef">
        <button class="download-btn" @click="downloadHoroscope" data-tooltip="Download your horoscope card for today">
          ⬇
        </button>
        <div class="horoscope-header">
          <h3>{{ horoscope.zodiac_sign }}</h3>
          <p v-if="horoscope.zodiac_sign_chinese" class="chinese-sign">{{ horoscope.zodiac_sign_chinese }}</p>
          <p class="date">{{ new Date().toLocaleDateString() }}</p>
        </div>
        <div class="horoscope-content">
          <h2>{{ horoscope.zodiac_sign }}</h2>
          <h3 v-if="horoscope.zodiac_sign_chinese">{{ horoscope.zodiac_sign_chinese }}</h3>
          <p>{{ horoscope.daily_horoscope }}</p>

          <div class="horoscope-details" v-if="horoscope.lucky_number || horoscope.compatibility || horoscope.mood">
            <p v-if="horoscope.lucky_number">Lucky Number: {{ horoscope.lucky_number }}</p>
            <p v-if="horoscope.compatibility">Compatibility: {{ horoscope.compatibility }}</p>
            <p v-if="horoscope.mood">Mood: {{ horoscope.mood }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="error-container" v-if="error">
      <div class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../views/horoscope-styles.scss' as *;
</style>
