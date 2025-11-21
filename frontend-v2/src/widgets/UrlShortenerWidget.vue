<script setup lang="ts">
import { ref } from 'vue'
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
        <button class="copy-btn" @click="copyToClipboard(shortenedUrl)">Copy</button>
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
          <button class="copy-btn" @click="copyToClipboard(url.shortened_url)">Copy</button>
          <button class="delete-btn" @click="removeUrl(url)">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.url-shortener-container { 
  display: flex; 
  flex-direction: column; 
  gap: 1.5rem; 
}

.url-shortener-container h2 {
  color: #1a1a1a;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.input-container { 
  display: flex; 
  gap: .75rem; 
}

.input-container input { 
  flex: 1; 
  padding: .875rem 1rem; 
  border: 2px solid #e0e0e0; 
  border-radius: 8px; 
  font-size: 1rem;
  background: #fafafa;
  transition: all 0.3s ease;
}

.input-container input:focus {
  outline: none;
  border-color: #E8D5B7;
  box-shadow: 0 0 0 3px rgba(232, 213, 183, 0.15);
  background: #fff;
}

.input-container button { 
  padding: .875rem 1.5rem; 
  background: linear-gradient(135deg, #F5E8D6, #E8D5B7); 
  color: #4a4a4a; 
  border: 1px solid #E8D5B7; 
  border-radius: 8px; 
  cursor: pointer; 
  font-weight: 600;
  transition: all 0.3s ease;
}

.input-container button:hover {
  background: linear-gradient(135deg, #E8D5B7, #DDC9B0);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(232, 213, 183, 0.3);
}

.input-container button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message { 
  color: #dc2626; 
  background: #fef2f2; 
  padding: .875rem 1rem; 
  border-radius: 8px; 
  border: 1px solid #fecaca;
}

.result-container { 
  background: #fafafa; 
  padding: 1.25rem; 
  border-radius: 12px; 
  border: 1px solid #f0f0f0;
}

.url-display { 
  display: flex; 
  gap: .75rem; 
  align-items: center; 
  flex-wrap: wrap; 
}

.url-display span {
  font-weight: 500;
  color: #374151;
}

.url-display a {
  color: #B8947A;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.url-display a:hover {
  color: #A6856F;
  text-decoration: underline;
}

.recent-urls { 
  margin-top: 1.5rem; 
}

.recent-urls h3 {
  color: #1a1a1a;
  margin-bottom: 1rem;
  font-size: 1.125rem;
  font-weight: 600;
}

.url-item { 
  display: flex; 
  justify-content: space-between; 
  gap: 1rem; 
  padding: 1rem; 
  background: #fff; 
  border: 1px solid #f0f0f0; 
  border-radius: 10px; 
  margin-top: .75rem;
  transition: all 0.3s ease;
}

.url-item:hover {
  box-shadow: 0 2px 8px rgba(232, 213, 183, 0.15);
  border-color: #E8D5B7;
}

.url-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: .5rem;
}

.original-url {
  color: #6b7280;
  font-size: .875rem;
  word-break: break-all;
}

.url-details a {
  color: #B8947A;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.url-details a:hover {
  color: #A6856F;
  text-decoration: underline;
}

.url-actions { 
  display: flex; 
  flex-direction: column; 
  gap: .5rem; 
}

.url-actions button { 
  background: #fafafa; 
  border: 1px solid #e0e0e0; 
  padding: .5rem .875rem; 
  border-radius: 6px; 
  cursor: pointer; 
  font-size: .875rem;
  font-weight: 500;
  color: #475569;
  transition: all 0.3s ease;
  min-width: 70px;
}

.url-actions button:hover {
  background: #f0f0f0;
  transform: translateY(-1px);
}

.copy-btn {
  background: linear-gradient(135deg, #F5E8D6, #E8D5B7) !important;
  color: #4a4a4a !important;
  border-color: #E8D5B7 !important;
  font-weight: 600 !important;
}

.copy-btn:hover {
  background: linear-gradient(135deg, #E8D5B7, #DDC9B0) !important;
  border-color: #DDC9B0 !important;
}

.delete-btn { 
  background: #fef2f2 !important; 
  color: #dc2626 !important; 
  border-color: #fecaca !important;
}

.delete-btn:hover {
  background: #fee2e2 !important;
  border-color: #fca5a5 !important;
}
</style>
