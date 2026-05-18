<template>
  <VChart class="chart-surface" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, CandlestickChart, LineChart } from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  AxisPointerComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { CandlePoint } from '../../services/api'

use([CanvasRenderer, CandlestickChart, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, AxisPointerComponent])

const props = defineProps<{
  items: CandlePoint[]
}>()

function movingAverage(period: number, items: CandlePoint[]) {
  return items.map((_, index) => {
    if (index < period) return null
    const slice = items.slice(index - period, index)
    const sum = slice.reduce((total, item) => total + item.close, 0)
    return Number((sum / period).toFixed(2))
  })
}

const option = computed(() => {
  const labels = props.items.map((item) => new Date(item.ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }))
  const candles = props.items.map((item) => [item.open, item.close, item.low, item.high])
  const volume = props.items.map((item, index) => ({
    value: item.volume,
    itemStyle: { color: item.close >= item.open ? '#18b36b' : '#d65263' },
    xAxis: index,
  }))

  return {
    animation: false,
    backgroundColor: 'transparent',
    legend: {
      top: 0,
      textStyle: { color: '#617c98' },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      borderColor: '#dbe7f0',
      backgroundColor: 'rgba(255,255,255,0.96)',
      textStyle: { color: '#11233d' },
    },
    grid: [
      { left: 56, right: 24, top: 48, height: '58%' },
      { left: 56, right: 24, top: '74%', height: '16%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: labels,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#d7e5ee' } },
        axisLabel: { color: '#6e879d', hideOverlap: true },
        min: 'dataMin',
        max: 'dataMax',
      },
      {
        type: 'category',
        gridIndex: 1,
        data: labels,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#d7e5ee' } },
        axisLabel: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: 'rgba(214, 227, 236, 0.7)' } },
        axisLabel: { color: '#6e879d' },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        splitLine: { show: false },
        axisLabel: { color: '#6e879d' },
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 55, end: 100 },
      { show: false, xAxisIndex: [0, 1], type: 'slider', start: 55, end: 100 },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candles,
        itemStyle: {
          color: '#18b36b',
          color0: '#d65263',
          borderColor: '#18b36b',
          borderColor0: '#d65263',
        },
      },
      {
        name: 'MA10',
        type: 'line',
        data: movingAverage(10, props.items),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.4, color: '#2fb7f6' },
      },
      {
        name: 'MA24',
        type: 'line',
        data: movingAverage(24, props.items),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.4, color: '#f4a63b' },
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volume,
      },
    ],
  }
})
</script>

<style scoped>
.chart-surface {
  height: 330px;
  width: 100%;
}
</style>
