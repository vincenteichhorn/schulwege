import { createApp } from 'vue'
import { createPinia } from 'pinia'

// @ts-ignore: allow importing .vue without a declaration file
import App, { routes } from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'

import "bootstrap/dist/css/bootstrap.min.css"
import "bootstrap"


const app = createApp(App)

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: routes,
})

app.use(createPinia())
app.use(router)

app.mount('#app')
