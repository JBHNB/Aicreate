<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import GlobalFooter from '@/components/GlobalFooter.vue'
import GlobalHeader from '@/components/GlobalHeader.vue'

const route = useRoute()
const isFullBleed = computed(() => route.meta.fullBleed === true)
</script>

<template>
  <a-layout class="basic-layout">
    <GlobalHeader />
    <a-layout-content :class="['main-content', { 'main-content--full': isFullBleed }]">
      <router-view />
    </a-layout-content>
    <GlobalFooter v-if="!isFullBleed" />
  </a-layout>
</template>

<style scoped>
.basic-layout {
  min-height: 100vh;
  background: var(--app-bg, #f5f5f5);
}
.main-content {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
  flex: 1;
  background: transparent;
}
.main-content--full {
  max-width: none;
  margin: 0;
  padding: 0;
  background: none;
}
</style>
