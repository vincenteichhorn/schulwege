import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useNominatimStore = defineStore('nominatim', () => {
  
  const region = ref<string | null>(null)

  const setRegion = (newRegion: string | null) => {
    region.value = newRegion
  }

  const getRegion = computed(() => region.value)

  return {
    region,
    setRegion,
    getRegion,
  }
})
