<script setup lang="ts">
import { Minus } from 'lucide-vue-next'
import { Card } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import SettingsNav from './SettingsNav.vue'
import { settingsService } from '@/services/settings.service'
import { useAsync } from '@/composables/useAsync'

const { data, loading, error, run } = useAsync(settingsService.roleMatrix, { immediate: true })
const ACTIONS = ['read', 'write', 'create', 'delete', 'submit', 'cancel'] as const
const short = { read: 'R', write: 'W', create: 'C', delete: 'D', submit: 'S', cancel: 'X' }
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <PageHeader title="Settings" />
    <SettingsNav />
    <p class="mb-4 text-sm text-muted-foreground">
      Role permissions are enforced by the server. Non-admin roles are further limited to the properties assigned to each user.
      <span class="sm:whitespace-nowrap">R = read · W = edit · C = create · D = delete · S = submit · X = cancel.</span>
    </p>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading" />
    <Card v-else-if="data" class="overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-muted/40">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">Record</th>
              <th v-for="r in data.roles" :key="r" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {{ r.replace('PG ', '') }} <span class="font-normal normal-case">({{ data.user_counts[r] }})</span>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="dt in data.doctypes" :key="dt">
              <td class="whitespace-nowrap px-4 py-2.5 font-medium">{{ dt.replace('PG ', '') }}</td>
              <td v-for="r in data.roles" :key="r" class="px-4 py-2.5">
                <span v-if="!data.matrix[dt]?.[r]" class="text-muted-foreground"><Minus class="size-4" /></span>
                <span v-else class="flex gap-1">
                  <span v-for="a in ACTIONS.filter((x) => data!.matrix[dt][r][x])" :key="a" class="inline-flex size-5 items-center justify-center rounded bg-primary/10 font-mono text-[10px] font-semibold text-primary" :title="a">{{ short[a] }}</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>
