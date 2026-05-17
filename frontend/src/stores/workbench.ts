import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useWorkbenchStore = defineStore('workbench', () => {
  const tradeMode = ref<'paper' | 'live'>('paper')
  const selectedSymbol = ref('BTC/USDT')
  const selectedTimeframe = ref('15m')
  const notificationChannels = ref(['SMTP 邮件', '企业微信 Webhook'])

  const modeLabel = computed(() => (tradeMode.value === 'paper' ? '模拟' : '实盘'))

  function toggleTradeMode() {
    tradeMode.value = tradeMode.value === 'paper' ? 'live' : 'paper'
  }

  return {
    tradeMode,
    selectedSymbol,
    selectedTimeframe,
    notificationChannels,
    modeLabel,
    toggleTradeMode,
  }
})
