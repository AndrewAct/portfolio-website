<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getMediumPosts, type MediumPost } from '../services/history'
const loading = ref(true)
const error = ref<string | null>(null)
const mediumPosts = ref<MediumPost[]>([])

function getExcerpt(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  const text = div.textContent || div.innerText || ''
  return text.length > 240 ? text.slice(0, 240) + '…' : text
}

onMounted(async () => {
  try {
    mediumPosts.value = await getMediumPosts('andrewact')
  } catch (e: any) {
    error.value = e?.message ?? 'Failed to load posts'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="history-container">
    <a href="/" class="back-button">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      <span>Home</span>
    </a>

    <img src="/assets/images/homepage_image.jpg" alt="Background" />

    <div class="content-container">
      <h1 class="text-4xl font-bold mb-8 text-white text-center">My Blog Posts</h1>

      <div v-if="loading" class="text-center py-8">
        <div class="loading-spinner"></div>
        <p class="mt-4 text-white">Loading posts...</p>
      </div>

      <div v-if="error" class="text-center py-8 text-red-400">
        {{ error }}
      </div>

      <div v-if="!loading && !error" class="posts-grid">
        <div v-for="post in mediumPosts" :key="post.link" class="post-card">
          <div class="post-content">
            <h2 class="post-title">{{ post.title }}</h2>

            <div class="post-metadata">
              <span class="mr-4">{{ new Date(post.published_date).toLocaleDateString() }}</span>
            </div>

            <div class="post-excerpt">{{ getExcerpt(post.content) }}</div>

            <a :href="post.link" target="_blank" class="read-more-btn">
              Read More
            </a>
          </div>
        </div>
      </div>

      <div class="medium-link">
        <a href="https://medium.com/@andrewact" target="_blank" class="text-blue-300 hover:text-blue-400 transition-colors text-lg">
          Learn more about my articles on Medium
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.history-container {
  position: relative;
  width: 100vw;
  min-height: 100vh;
  overflow: hidden;
  display: flex;
}

img {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  min-width: 100%;
  min-height: 100%;
}

.content-container {
  position: relative;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  min-height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;

  h1 {
    margin-bottom: 2rem;
  }
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 0 auto;
  width: 100%;
  flex-grow: 1;
}

.post-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 1rem;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
  }
}

.post-content {
  padding: 1.5rem;
}

.post-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.post-metadata {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1rem;
}

.post-excerpt {
  color: #4a4a4a;
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.read-more-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  background-color: #3b82f6;
  color: white;
  border-radius: 0.375rem;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #2563eb;
  }
}

.loading-spinner {
  width: 3rem;
  height: 3rem;
  margin: 0 auto;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.medium-link {
  text-align: center;
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 0.5rem;

  a {
    color: white;
    font-weight: 500;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;

    &:hover {
      color: rgba(255, 255, 255, 0.9);
      text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
      transform: translateY(-1px);
    }

    &::after {
      content: ' →';
      display: inline-block;
      transition: transform 0.3s ease;
    }

    &:hover::after {
      transform: translateX(4px);
    }
  }
}

@media (max-width: 768px) {
  .posts-grid {
    grid-template-columns: 1fr;
  }

  .content-container {
    padding: 1rem;
  }
}

.back-button {
  position: fixed;
  top: 2rem;
  left: 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  color: #1a1a1a;
  z-index: 10;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);

  svg {
    width: 20px;
    height: 20px;
    transition: transform 0.3s ease;
  }

  span {
    font-weight: 500;
  }

  &:hover {
    background: rgba(255, 255, 255, 0.9);
    transform: translateX(-5px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);

    svg {
      transform: translateX(-3px);
    }
  }
}
</style>
