<script setup lang="ts">
const logoUrl = `${import.meta.env.BASE_URL}icons/logo.svg`
const appName = import.meta.env.VITE_APP_NAME || 'HostelSuite'
const year = new Date().getFullYear()

// Illustrative front-desk key rack: a key off its hook = room taken.
const floors = [3, 2, 1].map((floor) => ({
  floor,
  rooms: Array.from({ length: 6 }, (_, i) => {
    const no = floor * 100 + i + 1
    return { no, out: [302, 305, 201, 204, 206, 103].includes(no) }
  }),
}))
</script>

<template>
  <div class="grid min-h-dvh bg-background lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
    <section class="hs-panel relative hidden flex-col justify-between overflow-hidden p-12 lg:flex xl:p-16" aria-hidden="true">
      <div class="flex items-center gap-3">
        <img :src="logoUrl" alt="" class="size-9 rounded-[10px]" />
        <span class="text-xl font-bold tracking-[-0.02em]">{{ appName }}</span>
      </div>

      <div class="max-w-xl">
        <div class="hs-rack">
          <div v-for="(f, fi) in floors" :key="f.floor" class="hs-row">
            <span class="hs-floor">Floor {{ f.floor }}</span>
            <div class="hs-hooks">
              <div v-for="(r, ri) in f.rooms" :key="r.no" class="hs-slot">
                <span class="hs-hook" />
                <span v-if="!r.out" class="hs-fob" :style="{ animationDelay: `${(fi * 6 + ri) * 45}ms` }">
                  <span class="hs-ring" />
                  <span class="hs-no">{{ r.no }}</span>
                </span>
                <span v-else class="hs-empty" />
              </div>
            </div>
          </div>
          <p class="hs-caption">A key on its hook is a free room.</p>
        </div>

        <h2 class="mt-12 text-[2.75rem] font-semibold leading-[1.05] tracking-[-0.03em] text-balance">Know who's in every bed.</h2>
        <p class="mt-4 max-w-md text-[1.0625rem] leading-relaxed text-white/70">
          Rooms, tenants, rent and electricity for your hostels and PGs, in one place.
        </p>
      </div>

      <p class="text-sm text-white/45">© {{ year }} {{ appName }}</p>
    </section>

    <section class="flex items-center px-5 py-10 sm:px-10 lg:px-16">
      <div class="mx-auto w-full max-w-[22rem]">
        <div class="mb-10 flex items-center gap-3 lg:hidden">
          <img :src="logoUrl" alt="" class="size-9 rounded-[10px]" />
          <span class="text-xl font-bold tracking-[-0.02em]">{{ appName }}</span>
        </div>
        <RouterView />
      </div>
    </section>
  </div>
</template>

<style scoped>
.hs-panel {
  --ink: #1c1a3f;
  --board: #252256;
  --brass: #c99a3b;
  --fob: #ecebff;
  --fob-ink: #2a2770;
  background: var(--ink);
  color: #fff;
}

.hs-rack {
  background: var(--board);
  border-radius: 18px;
  padding: 22px 26px 18px;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.06);
}
.hs-row {
  display: grid;
  grid-template-columns: 4.5rem 1fr;
  align-items: start;
  padding-block: 4px 14px;
}
.hs-row + .hs-row {
  border-top: 1px solid rgb(255 255 255 / 0.07);
  padding-top: 14px;
}
.hs-floor {
  padding-top: 2px;
  font-size: 0.8125rem;
  color: rgb(255 255 255 / 0.5);
}
.hs-hooks {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
}
.hs-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 78px;
}
.hs-hook {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--brass);
  box-shadow: 0 1px 0 rgb(0 0 0 / 0.35);
}
.hs-fob {
  position: relative;
  margin-top: -5px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform-origin: 50% 0;
  animation: hs-swing 900ms cubic-bezier(0.3, 1.6, 0.5, 1) both;
}
.hs-ring {
  width: 16px;
  height: 16px;
  border: 2.5px solid var(--brass);
  border-radius: 999px;
}
.hs-no {
  margin-top: -3px;
  display: grid;
  place-items: center;
  width: 42px;
  height: 50px;
  padding-top: 4px;
  background: var(--fob);
  color: var(--fob-ink);
  font-size: 0.8125rem;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
  clip-path: polygon(22% 0, 78% 0, 100% 14%, 100% 100%, 0 100%, 0 14%);
  border-radius: 0 0 9px 9px;
}
.hs-empty {
  margin-top: 8px;
  width: 42px;
  height: 58px;
  border: 1.5px dashed rgb(255 255 255 / 0.16);
  border-radius: 6px 6px 9px 9px;
}
.hs-caption {
  margin-top: 6px;
  font-size: 0.8125rem;
  color: rgb(255 255 255 / 0.5);
}

@keyframes hs-swing {
  0% {
    opacity: 0;
    transform: rotate(-14deg);
  }
  40% {
    opacity: 1;
  }
  100% {
    transform: rotate(0);
  }
}
@media (prefers-reduced-motion: reduce) {
  .hs-fob {
    animation: none;
  }
}
</style>
