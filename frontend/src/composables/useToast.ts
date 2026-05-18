import { reactive, onUnmounted } from 'vue'

export type ToastTone = 'neutral' | 'success' | 'error'

export function useToast() {
  let toastTimer: ReturnType<typeof setTimeout> | null = null

  const toast = reactive({
    visible: false,
    message: '',
    tone: 'neutral' as ToastTone,
  })

  function showToast(message: string, tone: ToastTone = 'neutral') {
    toast.message = message
    toast.tone = tone
    toast.visible = true
    if (toastTimer !== null) clearTimeout(toastTimer)
    toastTimer = setTimeout(() => { toast.visible = false }, 2600)
  }

  onUnmounted(() => {
    if (toastTimer !== null) clearTimeout(toastTimer)
  })

  return { toast, showToast }
}
