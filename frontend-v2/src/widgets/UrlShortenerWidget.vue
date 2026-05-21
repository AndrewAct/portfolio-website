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
/* URL Shortener widget — dark/glass background context */

.url-shortener-container {
  display: flex;
  flex-direction: column;
  gap: 1.4rem;
  max-width: 560px;
  margin: 0 auto;
}

.url-shortener-container h2 {
  color: rgba(255, 255, 255, 0.92);
  font-weight: 600;
  font-size: 1.2rem;
  margin: 0 0 0.25rem;
}

.input-container {
  display: flex;
  gap: 0.6rem;
}

.input-container input {
  flex: 1;
  padding: 0.78rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.88);
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}

.input-container input::placeholder { color: rgba(255, 255, 255, 0.35); }

.input-container input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.42);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.07);
}

.input-container button {
  padding: 0.78rem 1.4rem;
  background: rgba(255, 255, 255, 0.92);
  color: #111;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: background 0.18s, box-shadow 0.18s, transform 0.18s;
  white-space: nowrap;
}

.input-container button:hover:not(:disabled) {
  background: #fff;
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
}

.input-container button:disabled {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.35);
  cursor: not-allowed;
  transform: none;
}

.error-message {
  background: rgba(220, 38, 38, 0.14);
  border: 1px solid rgba(220, 38, 38, 0.32);
  color: #fca5a5;
  padding: 0.85rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
}

.result-container {
  background: rgba(255, 255, 255, 0.07);
  padding: 1.1rem 1.2rem;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.13);
}

.url-display {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-wrap: wrap;
}

.url-display span {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.65);
  font-size: 0.88rem;
}

.url-display a {
  color: rgba(180, 210, 255, 0.85);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.url-display a:hover { color: rgba(180, 210, 255, 1); text-decoration: underline; }

.recent-urls { margin-top: 0.5rem; }

.recent-urls h3 {
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
}

.url-item {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 8px;
  margin-top: 0.55rem;
  transition: border-color 0.2s, background 0.2s;
}

.url-item:hover {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(255, 255, 255, 0.18);
}

.url-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-width: 0;
}

.original-url {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.82rem;
  word-break: break-all;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.url-details a {
  color: rgba(180, 210, 255, 0.85);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.88rem;
  transition: color 0.2s;
}

.url-details a:hover { color: rgba(180, 210, 255, 1); }

.url-actions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex-shrink: 0;
}

.url-actions button {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  padding: 0.42rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  transition: background 0.18s, color 0.18s;
  min-width: 64px;
}

.url-actions button:hover { background: rgba(255, 255, 255, 0.14); color: #fff; }

.copy-btn {
  background: rgba(255, 255, 255, 0.14) !important;
  border-color: rgba(255, 255, 255, 0.26) !important;
  color: rgba(255, 255, 255, 0.88) !important;
  font-weight: 600 !important;
}

.copy-btn:hover { background: rgba(255, 255, 255, 0.22) !important; }

.delete-btn {
  background: rgba(220, 38, 38, 0.12) !important;
  border-color: rgba(220, 38, 38, 0.28) !important;
  color: #fca5a5 !important;
}

.delete-btn:hover { background: rgba(220, 38, 38, 0.2) !important; }
</style>
