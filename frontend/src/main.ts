import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/films.css'
import './styles/settings.css'
import './styles/planning.css'
import './style.css'

createApp(App).use(createPinia()).use(router).mount('#app')
