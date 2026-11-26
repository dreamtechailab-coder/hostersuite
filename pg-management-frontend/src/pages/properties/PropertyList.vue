<script setup lang="ts">
import { Building2, Plus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import Pagination from '@/components/common/Pagination.vue'
import PropertyCard from '@/components/property/PropertyCard.vue'
import { useResourceList } from '@/composables/useResourceList'
import { usePermissions } from '@/composables/usePermissions'
import type { Property } from '@/types'

const { hasRole } = usePermissions()
const list = useResourceList<Property>('PG Property', { scoped: false, pageSize: 24 })
</script>

<template>
  <div>
    <PageHeader title="Properties" description="All PG properties you manage.">
      <template #actions>
        <SearchInput v-model="list.search.value" placeholder="Search properties…" />
        <Button v-if="hasRole('PG Admin')" as-child><RouterLink to="/properties/new"><Plus />Add property</RouterLink></Button>
      </template>
    </PageHeader>
    <ErrorState v-if="list.error.value" :error="list.error.value" @retry="list.reload" />
    <LoadingSkeleton v-else-if="list.loading.value && !list.rows.value.length" variant="cards" />
    <EmptyState v-else-if="!list.rows.value.length" :icon="Building2" title="No properties found" description="Properties you have access to appear here." />
    <template v-else>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <PropertyCard v-for="p in list.rows.value" :key="p.name" :property="p" />
      </div>
      <div v-if="list.pageCount.value > 1" class="mt-4 rounded-xl border bg-card">
        <Pagination :page="list.page.value" :page-count="list.pageCount.value" :total="list.total.value" :from="list.from.value" :to="list.to.value" @update:page="list.setPage" />
      </div>
    </template>
  </div>
</template>
