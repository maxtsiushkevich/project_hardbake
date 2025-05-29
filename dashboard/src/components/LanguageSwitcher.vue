<template>
  <div class="language-switcher">
    <select v-model="currentLocale" @change="changeLocale" class="language-select">
      <option value="en">English</option>
      <option value="ru">Русский</option>
    </select>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const currentLocale = ref(locale.value)

const changeLocale = () => {
  locale.value = currentLocale.value
  localStorage.setItem('locale', currentLocale.value)
  // Remove the page reload
}

// Watch for changes in the locale
watch(() => locale.value, (newLocale) => {
  currentLocale.value = newLocale
})

onMounted(() => {
  const savedLocale = localStorage.getItem('locale')
  if (savedLocale) {
    currentLocale.value = savedLocale
    locale.value = savedLocale
  }
})
</script>

<style scoped>
.language-switcher {
  display: inline-block;
  width: 100%;
  margin-top: 10px;
}

.language-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc; /* Light mode border */
  border-radius: 4px;
  background-color: #fff; /* Light mode background */
  color: #333; /* Light mode text color */
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease; /* Smoother transition */
}

.language-select:hover {
  background-color: #f0f0f0; /* Light mode hover */
}

.language-select option {
  background-color: #fff; /* Light mode option background */
  color: #333; /* Light mode option text */
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .language-select {
    border: 1px solid rgba(255, 255, 255, 0.1); /* Dark mode border */
    background-color: rgba(255, 255, 255, 0.1); /* Dark mode background */
    color: white; /* Dark mode text color */
  }

  .language-select:hover {
    background-color: rgba(255, 255, 255, 0.2); /* Dark mode hover */
  }

  .language-select option {
    background-color: #2c3e50; /* Dark mode option background */
    color: white; /* Dark mode option text */
  }
}
</style> 