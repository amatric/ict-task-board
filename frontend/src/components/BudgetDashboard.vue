<template>
  <div class="budget-board">
    <div class="bb-header">
      <div>
        <h2 class="bb-title">预算看板</h2>
        <p class="bb-sub">预算执行情况 · 分类占比 · 每日趋势 · 成员分摊与结算</p>
      </div>
      <a-button type="primary" ghost @click="openExpenseModal">记一笔支出</a-button>
    </div>

    <!-- 1. 预算 vs 实际 -->
    <div class="bb-cards">
      <div class="bb-card">
        <div class="bb-card-label">计划预算</div>
        <div class="bb-card-value">¥{{ fmt(totalBudget) }}</div>
        <div class="bb-card-hint">来自行程规划</div>
      </div>
      <div class="bb-card">
        <div class="bb-card-label">实际支出</div>
        <div class="bb-card-value">¥{{ fmt(totalActual) }}</div>
        <div class="bb-card-hint">{{ expenses.length }} 笔记录</div>
      </div>
      <div class="bb-card" :class="diffClass">
        <div class="bb-card-label">{{ diff >= 0 ? '剩余预算' : '已超支' }}</div>
        <div class="bb-card-value">¥{{ fmt(Math.abs(diff)) }}</div>
        <div class="bb-card-hint">执行率 {{ execRate }}%</div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="bb-progress-wrap">
      <div class="bb-progress-bar">
        <div class="bb-progress-inner" :class="diffClass" :style="{ width: Math.min(100, Number(execRate)) + '%' }"></div>
      </div>
      <div class="bb-progress-meta">
        <span>预算执行率</span>
        <span>{{ execRate }}%</span>
      </div>
    </div>

    <!-- 2. 分类占比 + 3. 每日趋势 -->
    <div class="bb-charts">
      <div class="bb-chart-box">
        <div class="bb-chart-title">分类占比</div>
        <div ref="pieRef" class="bb-chart"></div>
      </div>
      <div class="bb-chart-box">
        <div class="bb-chart-title">每日支出趋势</div>
        <div ref="lineRef" class="bb-chart"></div>
      </div>
    </div>

    <!-- 4. 成员分摊 -->
    <div class="bb-split">
      <div class="bb-split-head">
        <div class="bb-chart-title">成员分摊与结算建议</div>
        <a-button size="small" type="link" @click="addMember">+ 添加成员</a-button>
      </div>
      <a-table
        :columns="columns"
        :data-source="memberRows"
        :pagination="false"
        size="small"
        row-key="name"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'net'">
            <span :class="record.net >= 0 ? 'bb-pos' : 'bb-neg'">
              {{ record.net >= 0 ? '+' : '' }}{{ fmt(record.net) }}
            </span>
          </template>
        </template>
      </a-table>
      <div v-if="settlements.length" class="bb-settle">
        <div class="bb-settle-title">结算建议</div>
        <div v-for="(s, i) in settlements" :key="i" class="bb-settle-item">
          <span class="bb-settle-from">{{ s.from }}</span>
          <span class="bb-settle-arrow">→</span>
          <span class="bb-settle-to">{{ s.to }}</span>
          <span class="bb-settle-amt">¥{{ fmt(s.amount) }}</span>
        </div>
      </div>
      <div v-else class="bb-empty">暂无待结算款项，账目已平</div>
    </div>

    <!-- 支出明细 -->
    <div class="bb-list">
      <div class="bb-split-head">
        <div class="bb-chart-title">支出明细</div>
        <a-button v-if="expenses.length" size="small" type="link" danger @click="clearAll">清空</a-button>
      </div>
      <a-table :columns="expenseColumns" :data-source="expenses" :pagination="false" size="small" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'amount'">¥{{ fmt(record.amount) }}</template>
          <template v-else-if="column.key === 'action'">
            <a-button size="small" type="link" danger @click="removeExpense(record.id)">删除</a-button>
          </template>
        </template>
      </a-table>
      <div v-if="!expenses.length" class="bb-empty">还没有支出记录，点右上角「记一笔支出」开始</div>
    </div>

    <!-- 记账弹窗 -->
    <a-modal v-model:open="expenseModalOpen" title="记一笔支出" @ok="saveExpense" ok-text="保存" cancel-text="取消">
      <div class="bb-form">
        <div class="bb-form-item">
          <label>日期</label>
          <a-input v-model:value="form.date" placeholder="2026-11-03" />
        </div>
        <div class="bb-form-item">
          <label>分类</label>
          <a-select v-model:value="form.category" style="width: 100%">
            <a-select-option value="景点">景点</a-select-option>
            <a-select-option value="住宿">住宿</a-select-option>
            <a-select-option value="餐饮">餐饮</a-select-option>
            <a-select-option value="交通">交通</a-select-option>
            <a-select-option value="其他">其他</a-select-option>
          </a-select>
        </div>
        <div class="bb-form-item">
          <label>金额</label>
          <a-input-number v-model:value="form.amount" :min="0" :precision="2" style="width: 100%" />
        </div>
        <div class="bb-form-item">
          <label>付款人</label>
          <a-select v-model:value="form.payer" style="width: 100%">
            <a-select-option v-for="m in members" :key="m" :value="m">{{ m }}</a-select-option>
          </a-select>
        </div>
        <div class="bb-form-item">
          <label>参与分摊</label>
          <a-select v-model:value="form.participants" mode="multiple" style="width: 100%">
            <a-select-option v-for="m in members" :key="m" :value="m">{{ m }}</a-select-option>
          </a-select>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { TripPlan } from '@/types'

const props = defineProps<{ tripPlan: TripPlan }>()

const STORAGE_KEY = 'tripstar_budget_board_v1'

interface Expense {
  id: string
  date: string
  category: string
  amount: number
  payer: string
  participants: string[]
}

const expenses = ref<Expense[]>([])
const members = ref<string[]>(['我', '同行A', '同行B'])

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const data = JSON.parse(raw)
    if (Array.isArray(data.expenses)) expenses.value = data.expenses
    if (Array.isArray(data.members) && data.members.length) members.value = data.members
  } catch (e) { /* ignore */ }
}
function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ expenses: expenses.value, members: members.value }))
  } catch (e) { /* ignore */ }
}

const totalBudget = computed(() => Number(props.tripPlan?.budget?.total ?? 0))
const totalActual = computed(() => expenses.value.reduce((s, e) => s + Number(e.amount || 0), 0))
const diff = computed(() => totalBudget.value - totalActual.value)
const execRate = computed(() => {
  if (!totalBudget.value) return '0.0'
  return ((totalActual.value / totalBudget.value) * 100).toFixed(1)
})
const diffClass = computed(() => (diff.value >= 0 ? 'bb-ok' : 'bb-over'))

function fmt(n: number) {
  return Number(n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 分类聚合
const categoryData = computed(() => {
  const map = new Map<string, number>()
  for (const e of expenses.value) {
    map.set(e.category, (map.get(e.category) || 0) + Number(e.amount || 0))
  }
  return [...map.entries()].map(([name, value]) => ({ name, value: Number(value.toFixed(2)) }))
})

// 每日聚合
const dailyData = computed(() => {
  const map = new Map<string, number>()
  for (const e of expenses.value) {
    map.set(e.date, (map.get(e.date) || 0) + Number(e.amount || 0))
  }
  return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]))
})

// 成员分摊
const memberRows = computed(() => {
  return members.value.map((name) => {
    let paid = 0
    let share = 0
    for (const e of expenses.value) {
      const amt = Number(e.amount || 0)
      if (e.payer === name) paid += amt
      const ps = e.participants && e.participants.length ? e.participants : members.value
      if (ps.includes(name)) share += amt / ps.length
    }
    return {
      name,
      paid: Number(paid.toFixed(2)),
      share: Number(share.toFixed(2)),
      net: Number((paid - share).toFixed(2))
    }
  })
})

// 结算建议（贪心配对）
const settlements = computed(() => {
  const creditors = memberRows.value.filter((m) => m.net > 0.005).map((m) => ({ ...m }))
  const debtors = memberRows.value.filter((m) => m.net < -0.005).map((m) => ({ ...m }))
  const out: { from: string; to: string; amount: number }[] = []
  let i = 0
  let j = 0
  let guard = 0
  while (i < debtors.length && j < creditors.length && guard++ < 200) {
    const d = debtors[i]
    const c = creditors[j]
    const owe = -d.net
    const amount = Math.min(owe, c.net)
    if (amount > 0.005) {
      out.push({ from: d.name, to: c.name, amount: Number(amount.toFixed(2)) })
      d.net += amount
      c.net -= amount
    }
    if (-d.net <= 0.005) i++
    if (c.net <= 0.005) j++
  }
  return out
})

const columns = [
  { title: '成员', dataIndex: 'name', key: 'name' },
  { title: '已垫付', dataIndex: 'paid', key: 'paid' },
  { title: '应分摊', dataIndex: 'share', key: 'share' },
  { title: '净额', dataIndex: 'net', key: 'net' }
]
const expenseColumns = [
  { title: '日期', dataIndex: 'date', key: 'date' },
  { title: '分类', dataIndex: 'category', key: 'category' },
  { title: '金额', dataIndex: 'amount', key: 'amount' },
  { title: '付款人', dataIndex: 'payer', key: 'payer' },
  { title: '操作', key: 'action' }
]

// 记账
const expenseModalOpen = ref(false)
const form = ref<{ date: string; category: string; amount: number; payer: string; participants: string[] }>({
  date: new Date().toISOString().slice(0, 10),
  category: '餐饮',
  amount: 0,
  payer: '',
  participants: []
})

function openExpenseModal() {
  form.value = {
    date: new Date().toISOString().slice(0, 10),
    category: '餐饮',
    amount: 0,
    payer: members.value[0] || '',
    participants: [...members.value]
  }
  expenseModalOpen.value = true
}
function saveExpense() {
  const f = form.value
  if (!f.date || !Number(f.amount)) return
  expenses.value.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    date: f.date,
    category: f.category,
    amount: Number(f.amount),
    payer: f.payer || members.value[0] || '我',
    participants: f.participants.length ? [...f.participants] : [...members.value]
  })
  expenseModalOpen.value = false
  persist()
  renderCharts()
}
function removeExpense(id: string) {
  expenses.value = expenses.value.filter((e) => e.id !== id)
  persist()
  renderCharts()
}
function clearAll() {
  expenses.value = []
  persist()
  renderCharts()
}
function addMember() {
  const name = window.prompt('成员名称')
  if (!name) return
  const n = name.trim()
  if (!n || members.value.includes(n)) return
  members.value.push(n)
  persist()
}

// 图表
const pieRef = ref<HTMLElement | null>(null)
const lineRef = ref<HTMLElement | null>(null)
let pieChart: echarts.ECharts | null = null
let lineChart: echarts.ECharts | null = null

function renderCharts() {
  if (pieRef.value) {
    if (!pieChart) pieChart = echarts.init(pieRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
      legend: { bottom: 0, textStyle: { fontSize: 11 } },
      series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        data: categoryData.value.length ? categoryData.value : [{ name: '暂无数据', value: 1 }]
      }]
    }, true)
  }
  if (lineRef.value) {
    if (!lineChart) lineChart = echarts.init(lineRef.value)
    lineChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 16, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: dailyData.value.map((d) => d[0]), axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
      series: [{
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.15 },
        data: dailyData.value.map((d) => Number(d[1].toFixed(2)))
      }]
    }, true)
  }
}

function onResize() {
  pieChart?.resize()
  lineChart?.resize()
}

onMounted(() => {
  load()
  // 若没有任何记录，用计划预算铺一条初始分类，便于直观看到分布
  nextTick(() => renderCharts())
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  pieChart?.dispose()
  lineChart?.dispose()
  pieChart = null
  lineChart = null
})
watch(categoryData, () => renderCharts(), { deep: true })
</script>

<style scoped>
.budget-board { padding: 20px 24px 40px; }
.bb-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.bb-title { margin: 0; font-size: 22px; font-weight: 600; color: #1f2937; }
.bb-sub { margin: 6px 0 0; font-size: 13px; color: #6b7280; }
.bb-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.bb-card { background: #fff; border-radius: 14px; padding: 18px 20px; box-shadow: 0 2px 10px rgba(17,24,39,.06); border-left: 4px solid #5b7cfa; }
.bb-card.bb-ok { border-left-color: #22c55e; }
.bb-card.bb-over { border-left-color: #ef4444; }
.bb-card-label { font-size: 13px; color: #6b7280; }
.bb-card-value { font-size: 26px; font-weight: 600; margin-top: 6px; color: #111827; }
.bb-card-hint { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.bb-progress-wrap { margin: 18px 0 6px; }
.bb-progress-bar { height: 10px; background: #eef1f7; border-radius: 999px; overflow: hidden; }
.bb-progress-inner { height: 100%; background: #22c55e; border-radius: 999px; transition: width .3s; }
.bb-progress-inner.bb-over { background: #ef4444; }
.bb-progress-meta { display: flex; justify-content: space-between; font-size: 12px; color: #6b7280; margin-top: 6px; }
.bb-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
@media (max-width: 900px) { .bb-charts, .bb-cards { grid-template-columns: 1fr; } }
.bb-chart-box { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 2px 10px rgba(17,24,39,.06); }
.bb-chart-title { font-size: 15px; font-weight: 600; color: #1f2937; margin-bottom: 10px; }
.bb-chart { height: 260px; }
.bb-split, .bb-list { background: #fff; border-radius: 14px; padding: 16px; margin-top: 16px; box-shadow: 0 2px 10px rgba(17,24,39,.06); }
.bb-split-head { display: flex; justify-content: space-between; align-items: center; }
.bb-pos { color: #22c55e; font-weight: 600; }
.bb-neg { color: #ef4444; font-weight: 600; }
.bb-settle { margin-top: 14px; border-top: 1px dashed #e5e9f2; padding-top: 12px; }
.bb-settle-title { font-size: 13px; color: #6b7280; margin-bottom: 8px; }
.bb-settle-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 14px; }
.bb-settle-from { color: #ef4444; font-weight: 600; }
.bb-settle-arrow { color: #9ca3af; }
.bb-settle-to { color: #22c55e; font-weight: 600; }
.bb-settle-amt { margin-left: auto; font-weight: 600; color: #111827; }
.bb-empty { padding: 24px 0; text-align: center; color: #9ca3af; font-size: 13px; }
.bb-form-item { margin-bottom: 12px; }
.bb-form-item label { display: block; font-size: 13px; color: #6b7280; margin-bottom: 5px; }
</style>
