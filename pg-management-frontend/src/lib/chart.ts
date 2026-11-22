import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent, AriaComponent } from 'echarts/components'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent, AriaComponent])

/**
 * Categorical palette – validated (CVD-safe adjacent pairs, light & dark
 * stepped separately). Assigned in fixed order by ENTITY, never cycled:
 *   1 blue   = invoiced / billed
 *   2 orange = expenses
 *   3 aqua   = collected / received
 */
const LIGHT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
const DARK = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#0ca30c', '#9085e9', '#e66767']

export const SERIES = { invoiced: 0, expenses: 1, collected: 2 } as const

export function chartTheme(dark: boolean) {
  return {
    palette: dark ? DARK : LIGHT,
    text: dark ? '#c3c2b7' : '#52514e',
    textStrong: dark ? '#f0efec' : '#0b0b0b',
    grid: dark ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.07)',
    axis: dark ? 'rgba(255,255,255,0.18)' : 'rgba(15,23,42,0.18)',
    surface: dark ? '#1a1f33' : '#ffffff',
    neutral: dark ? '#4b5563' : '#cbd5e1',
  }
}
export type ChartTheme = ReturnType<typeof chartTheme>

export function baseOption(t: ChartTheme) {
  return {
    color: t.palette,
    textStyle: { fontFamily: 'Inter Variable, system-ui, sans-serif', color: t.text },
    aria: { enabled: true },
    animationDuration: 300,
    tooltip: {
      backgroundColor: t.surface,
      borderColor: t.axis,
      borderWidth: 1,
      textStyle: { color: t.textStrong, fontSize: 12 },
      extraCssText: 'border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.12);',
    },
  }
}
