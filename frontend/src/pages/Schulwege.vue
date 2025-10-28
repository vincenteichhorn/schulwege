<script setup lang="ts">
import SearchSelect from '@/components/SearchSelect.vue';
import Box from '@/components/Box.vue';
import Button from '@/components/Button.vue';
import { ref, watch } from 'vue';
import { fetchPlaces, fetchStatusNominatim, startNominatim, stopNominatim } from '@/api/api';
import { capitalize } from '@/util/util';

</script>

<script lang="ts">
const selectedPlace = ref<string | null>(null);

let places = await fetchPlaces();
places = places.map(place => capitalize(place));
const region = ref<string | null>(null);
const status_aquired = ref<Boolean>(false);
const container_found = ref<boolean>(false);
const nominatim_running = ref<boolean>(false);
const nominatim_loading = ref<boolean>(false);
const last_log = ref<string | null>(null);

// loading can be null | 'start' | 'stop' | 'init'
const loading = ref<null | 'start' | 'stop' | 'init'>(null);
const loading_duration = 5000; // ms
const update_interval = 5000; // ms

async function updateStatus() {
    if (selectedPlace.value) {
        const status = await fetchStatusNominatim(selectedPlace.value);
        region.value = status.region;
        status_aquired.value = true;
        container_found.value = status.status.container_status !== "unknown";
        nominatim_running.value = status.status.nominatim_status === "running";
        nominatim_loading.value = status.status.nominatim_status === "loading";
        last_log.value = status.status.nominatim_log_tail[status.status.nominatim_log_tail.length - 1] || null;
    }
}

async function onStart() {
    if (!selectedPlace.value) return;
    await startNominatim(selectedPlace.value);
    // show loading animation for 10s, then refresh status
    loading.value = 'start';
    setTimeout(async () => {
        await updateStatus();
        loading.value = null;
    }, loading_duration);
}

async function onStop() {
    if (!selectedPlace.value) return;
    await stopNominatim(selectedPlace.value);
    loading.value = 'stop';
    setTimeout(async () => {
        await updateStatus();
        loading.value = null;
    }, loading_duration);
}
async function onInit() {
    if (!selectedPlace.value) return;
    await startNominatim(selectedPlace.value);
    loading.value = 'init';
    setTimeout(async () => {
        await updateStatus();
        loading.value = null;
    }, loading_duration);
}

watch(selectedPlace, async (newValue) => {
    newValue = newValue ? newValue.toLowerCase() : null;
    selectedPlace.value = newValue;
    await updateStatus();
});

// regularly update status every 5s
setInterval(async () => {
    if (selectedPlace.value) {
        await updateStatus();
    }
}, update_interval);
</script>

<template>
    <div class="container">
        <Box 
            grow
            direction="horizontal"
        >
            <SearchSelect
                :options="places"
                placeholder="Select a place"
                @select="selectedPlace = $event"
                :index=0
            />
            <Button 
                v-if="selectedPlace && !container_found && !nominatim_running && status_aquired"
                variant="primary"
                @click="onInit"
                :disabled="!!loading"
            >
                Initialize
                <span v-if="loading === 'init'" class="spinner" />
            </Button>
            <Button 
                v-if="container_found && !nominatim_running && !nominatim_loading && status_aquired"
                variant="success"
                @click="onStart"
                :disabled="!!loading"
            >
                Start
                <span v-if="loading === 'start'" class="spinner" />
            </Button>
            <Button 
                v-if="container_found && nominatim_running && status_aquired"
                variant="danger"
                @click="onStop"
                :disabled="!!loading"
            >
                Stop
                <span v-if="loading === 'stop'" class="spinner" /> 
            </Button>
            <div v-if="container_found && nominatim_loading && status_aquired">
                Initializing...
                <span class="spinner" />
                ({{ last_log }})
            </div>
        </Box>
    </div>
</template>

<style scoped>
.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-right: 4px;
  margin-left: 4px;
  border: 2px solid rgba(0,0,0,0.2);
  border-top-color: rgba(0,0,0,0.7);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  vertical-align: middle;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>