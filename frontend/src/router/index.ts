import { createRouter, createWebHistory } from 'vue-router'
import OverviewPage from '../pages/OverviewPage.vue'
import StrategyCenterPage from '../pages/StrategyCenterPage.vue'
import ExecutionPage from '../pages/ExecutionPage.vue'
import BacktestPage from '../pages/BacktestPage.vue'
import SettingsPage from '../pages/SettingsPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/overview' },
    { path: '/overview', name: 'overview', component: OverviewPage },
    { path: '/strategies', name: 'strategies', component: StrategyCenterPage },
    { path: '/execution', name: 'execution', component: ExecutionPage },
    { path: '/backtest', name: 'backtest', component: BacktestPage },
    { path: '/settings', name: 'settings', component: SettingsPage },
  ],
})

export default router
