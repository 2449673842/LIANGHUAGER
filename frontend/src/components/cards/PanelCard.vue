<template>
  <section class="panel">
    <div class="panel__header">
      <div class="panel__title">
        <h3>{{ title }}</h3>
        <span v-if="description">{{ description }}</span>
      </div>
      <div v-if="$slots.actions" class="panel__actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="panel__body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
