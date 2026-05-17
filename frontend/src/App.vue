<template>
  <div class="shell">
    <SidebarNav />
    <div class="shell__main">
      <AppHeader />
      <main class="shell__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import SidebarNav from './components/layout/SidebarNav.vue'
import AppHeader from './components/layout/AppHeader.vue'
</script>
