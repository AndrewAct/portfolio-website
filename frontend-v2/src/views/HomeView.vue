<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
function navigate(path: string) {
  router.push({ name: path })
}
</script>

<template>
  <div class="home-container">
    <img src="/assets/images/homepage_image.jpg" alt="Background" />
    <div class="button-container">
      <button @click="navigate('history')" class="tooltip-container">
        History
        <span class="tooltip">Feel free to check out my articles on Medium!</span>
      </button>
      <button @click="navigate('utilities')" class="tooltip-container">
        Utilities
        <span class="tooltip">Some utilities you might enjoy. Currently include: URL Shortener and Horoscope. More features will come in soon!</span>
      </button>
      <a href="https://andrewisgrinding.grafana.net/public-dashboards/c417bb15c3da45f2abefb1dcfd5076fe" target="_blank" class="button tooltip-container">
        Observability
        <span class="tooltip">Click this button to view the Grafana monitoring dashboard for my website</span>
      </a>
    </div>

    <div class="social-buttons">
      <a href="https://www.instagram.com/andrew3_chen/" target="_blank" class="social-button">
        <img src="/assets/images/instagram.svg" alt="Instagram">
      </a>
      <a href="https://www.linkedin.com/in/zhuo-chen-503890171/" target="_blank" class="social-button">
        <img src="/assets/images/linkedin.svg" alt="LinkedIn">
      </a>
      <a href="https://andrewact.medium.com/" target="_blank" class="social-button">
        <img src="/assets/images/medium.svg" alt="Medium">
      </a>
    </div>
  </div>
</template>

<style scoped lang="scss">
.home-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
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

.button-container {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 20px;
}

button, .button {
  padding: 12px 24px;
  font-size: 18px;
  border: 2px solid white;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  text-align: center;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.tooltip-container {
  position: relative;
  display: inline-block;

  padding: 12px 24px;
  font-size: 18px;
  border: 2px solid white;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  text-align: center;

  &:hover {
    background: rgba(255, 255, 255, 0.2);

    .tooltip {
      visibility: visible;
      opacity: 1;
    }
  }
}

.tooltip {
  visibility: hidden;
  position: absolute;
  bottom: -45px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 100;

  &::before {
    content: '';
    position: absolute;
    top: -5px;
    left: 50%;
    transform: translateX(-50%);
    border-width: 0 5px 5px 5px;
    border-style: solid;
    border-color: transparent transparent rgba(0, 0, 0, 0.8) transparent;
  }
}

.social-buttons {
  position: fixed;
  bottom: 2rem;
  left: 2rem;
  display: flex;
  gap: 1rem;
  z-index: 10;
}

.social-button {
  width: 28px;
  height: 28px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);

  img {
    width: 20px;
    height: 20px;
    position: static;
    object-fit: contain;
  }

  &:hover {
    transform: translateY(-3px);
    background: rgba(255, 255, 255, 1);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
}

@media (max-width: 768px) {
  .social-buttons {
    bottom: 1rem;
    left: 1rem;
  }

  .social-button {
    width: 28px;
    height: 28px;

    img {
      width: 16px;
      height: 16px;
    }
  }
}

@media (max-width: 768px) {
  .tooltip-container {
    padding: 10px 20px;
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .tooltip-container {
    width: 200px;
  }
}
</style>
