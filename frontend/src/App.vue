<script setup>
import NavBar from './components/NavBar.vue'

</script>

<script>
export const routes = [
  { path: '/', component: () => import('./pages/Schulwege.vue'), name: 'Schulwege' },
  { path: '/status', component: () => import('./pages/Status.vue'), name: 'Status' }
]
</script>

<template>
  <NavBar title="Schulkinder" :links="routes.map(route => ({ name: route.name || 'Home', href: route.path }))" />
  <main>
    <router-view />
  </main>
</template>
