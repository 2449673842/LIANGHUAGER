<template>
  <div class="stat-tile">
    <span class="stat-tile__label">{{ label }}</span>
    <strong class="stat-tile__value" :class="toneClass">{{ value }}</strong>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: string
  tone?: 'up' | 'down' | 'neutral'
}>()

const toneClass = computed(() => {
  if (props.tone === 'up') return 'tone-up'
  if (props.tone === 'down') return 'tone-down'
  return 'tone-neutral'
})
</script>

<style scoped>
.stat-tile {
  display: grid;
  gap: 8px;
  min-height: 112px;
  padding: 18px;
  border-radius: 16px;
  border: 1px solid rgba(206, 220, 230, 0.9);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 44px rgba(128, 152, 181, 0.12);
}

.stat-tile__label {
  font-size: 13px;
  color: #678198;
  font-weight: 600;
}

.stat-tile__value {
  font-size: 28px;
  line-height: 1;
  color: #132238;
}
</style>
