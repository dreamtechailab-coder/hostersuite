import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@fontsource-variable/inter'
import './assets/main.css'
import App from './App.vue'
import router from './router'
import { useUiStore } from './stores/ui'

const app = createApp(App)
app.use(createPinia())
useUiStore().applyTheme()
app.use(router)
app.mount('#app')
