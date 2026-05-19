import { createRouter, createWebHistory } from 'vue-router'

import FilmsView from '@/views/FilmsView.vue'
import GapsView from '@/views/GapsView.vue'
import PlanningView from '@/views/PlanningView.vue'
import SettingsView from '@/views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/films' },
    { path: '/films', component: FilmsView },
    { path: '/planning', component: PlanningView },
    { path: '/gaps', component: GapsView },
    { path: '/settings', component: SettingsView },
  ],
})

export default router
