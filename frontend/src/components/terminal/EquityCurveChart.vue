<template>
  <VChart class="chart-surface chart-surface--equity" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const props = defineProps<{
  points: Array<{ time: string; value: number }>
}>()

const option = computed(() => ({
  animation: false,
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    borderColor: '#dbe7f0',
    backgroundColor: 'rgba(255,255,255,0.96)',
    textStyle: { color: '#11233d' },
  },
  grid: { left: 56, right: 20, top: 18, bottom: 34 },
  xAxis: {
    type: 'category',
    data: props.points.map((item) => item.time),
    axisLine: { lineStyle: { color: '#d7e5ee' } },
    axisLabel: { color: '#6e879d' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(214, 227, 236, 0.7)' } },
    axisLabel: { color: '#6e879d' },
  },
  series: [
    {
      type: 'line',
      data: props.points.map((item) => item.value),
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2, color: '#20b7d7' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(32, 183, 215, 0.24)' },
            { offset: 1, color: 'rgba(32, 183, 215, 0.02)' },
          ],
        },
      },
    },
  ],
}))
</script>

<style scoped>
.chart-surface--equity {
  height: 220px;
}
</style>
