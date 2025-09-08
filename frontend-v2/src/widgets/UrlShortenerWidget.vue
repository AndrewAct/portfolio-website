<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { createShortUrl, deleteUrl, type URLResponse } from '../services/urlShortener'

const urlInput = ref('')
const shortenedUrl = ref<string | null>(null)
const error = ref<string | null>(null)
const recentUrls = ref<URLResponse[]>([])

async function shortenUrl() {
  error.value = null
  shortenedUrl.value = null
  try {
    const res = await createShortUrl({ url: urlInput.value })
    shortenedUrl.value = res.shortened_url
    recentUrls.value = [res, ...recentUrls.value].slice(0, 5)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to shorten URL'
  }
}

async function copyToClipboard(text: string) {
  await navigator.clipboard.writeText(text)
}

async function removeUrl(item: URLResponse) {
  try {
    await deleteUrl(item.shortened_url)
    recentUrls.value = recentUrls.value.filter(u => u.shortened_url !== item.shortened_url)
  } catch (e: any) {
    error.value = e?.message ?? 'Failed to delete URL'
  }
}
</script>

<template>
  <div class="url-shortener-container">
    <h2>URL Shortener</h2>

    <div class="input-container">
      <input type="text" v-model="urlInput" placeholder="Enter your URL here" @keyup.enter="shortenUrl" />
      <button @click="shortenUrl" :disabled="!urlInput">Shorten URL</button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="shortenedUrl" class="result-container">
      <div class="url-display">
        <span>Shortened URL:</span>
        <a :href="shortenedUrl" target="_blank">{{ shortenedUrl }}</a>
        <button @click="copyToClipboard(shortenedUrl)">Copy</button>
      </div>
    </div>

    <div v-if="recentUrls.length > 0" class="recent-urls">
      <h3>Recent URLs</h3>
      <div v-for="url in recentUrls" :key="url.shortened_url" class="url-item">
        <div class="url-details">
          <span class="original-url">{{ url.original_url }}</span>
          <a :href="url.shortened_url" target="_blank">{{ url.shortened_url }}</a>
        </div>
        <div class="url-actions">
          <button @click="copyToClipboard(url.shortened_url)">Copy</button>
          <button class="delete-btn" @click="removeUrl(url)">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.url-shortener-container { display: flex; flex-direction: column; gap: 1rem; }
.input-container { display: flex; gap: .5rem; }
.input-container input { flex: 1; padding: .75rem; border: 1px solid #ddd; border-radius: 6px; }
.input-container button { padding: .75rem 1rem; background: #4263eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.error-message { color: #d33; background: #ffe6e6; padding: .75rem; border-radius: 6px; }
.result-container { background: #f8faff; padding: 1rem; border-radius: 8px; }
.url-display { display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; }
.recent-urls { margin-top: 1rem; }
.url-item { display: flex; justify-content: space-between; gap: 1rem; padding: .75rem; background: #fff; border: 1px solid #eee; border-radius: 8px; margin-top: .5rem; }
.url-actions button { background: #eee; border: none; padding: .5rem .75rem; border-radius: 6px; cursor: pointer; }
.delete-btn { background: #ffd6d6 !important; color: #a00; }
</style>
