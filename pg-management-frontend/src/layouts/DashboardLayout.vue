<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import MobileNavigation from '@/components/layout/MobileNavigation.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'
</script>

<template>
  <div class="flex min-h-dvh">
    <a href="#main" class="sr-only z-50 rounded-md bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
    <AppSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <AppHeader />
      <main id="main" class="mx-auto w-full max-w-[1400px] flex-1 px-4 pb-28 pt-5 sm:px-6 sm:pt-6 lg:pb-10">
        <RouterView v-slot="{ Component, route }">
          <component :is="Component" :key="route.path" />
        </RouterView>
      </main>
    </div>
    <MobileNavigation />
    <GlobalSearch />
  </div>
</template>
