<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const items = ref([])
const summary = ref({ active_count: 0, paper_m2_total: 0 })
const includeVoided = ref(false)
const err = ref('')
const voidingId = ref(null)
const reason = ref('')
const busy = ref(false)

async function load() {
  err.value = ''
  try {
    const data = await getJSON(`/api/runs?include_voided=${includeVoided.value}`)
    items.value = data.items
    summary.value = data.summary
  } catch (e) {
    err.value = String(e.message || e)
  }
}

onMounted(load)

function fmt(ts) {
  return ts ? String(ts).slice(0, 16).replace('T', ' ') : ''
}

function startVoid(r) {
  voidingId.value = r.id
  reason.value = ''
}

function cancelVoid() {
  voidingId.value = null
  reason.value = ''
}

async function confirmVoid(r) {
  if (!reason.value.trim()) return
  busy.value = true
  err.value = ''
  try {
    await postJSON(`/api/runs/${r.id}/void`, { reason: reason.value.trim() })
    cancelVoid()
    await load()
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <h1>用纸档</h1>
    <p class="lede">算纸页「写入用纸档」后的落库结果，按次保留盒名与面积。作废只附加冲正记录，原测算数字保留可审计。</p>
    <div class="row">
      <label class="check">
        <input type="checkbox" v-model="includeVoided" @change="load" />
        含作废
      </label>
      <span class="summary-chip">
        活跃 {{ summary.active_count }} 单 · 合计 {{ summary.paper_m2_total }} m²
        <em>（不计作废）</em>
      </span>
    </div>
    <p v-if="err" class="bad">{{ err }}</p>
    <p v-else-if="!items.length" class="empty">还没有写入过。先去算纸试一单。</p>
    <ul v-else class="item-list">
      <li v-for="r in items" :key="r.id" :class="{ voided: r.status === 'voided' }">
        <span class="run-main">
          <router-link :to="`/history/${r.id}`">{{ r.box_name }}</router-link>
          <span v-if="r.status === 'voided'" class="pill warn">已作废</span>
          <span v-if="r.status === 'voided'" class="meta void-reason">原因：{{ r.void_reason }}</span>
          <span v-if="voidingId === r.id" class="void-form">
            <input v-model="reason" placeholder="必填：作废原因" @keyup.enter="confirmVoid(r)" />
            <button class="ribbon" :disabled="busy || !reason.trim()" @click="confirmVoid(r)">确认作废</button>
            <button class="ghost" @click="cancelVoid">取消</button>
          </span>
        </span>
        <span class="run-side">
          <span class="meta">{{ r.result?.paper_m2 ?? '—' }} m² · {{ fmt(r.created_at) }}</span>
          <button
            v-if="r.status === 'active' && voidingId !== r.id"
            class="ghost small"
            @click="startVoid(r)"
          >作废</button>
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.check {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  cursor: pointer;
}

.summary-chip {
  font-size: 0.9rem;
  font-variant-numeric: tabular-nums;
  color: var(--ink-soft);
}

.summary-chip em {
  font-style: normal;
  font-size: 0.8rem;
  color: var(--foil);
}

.run-main {
  display: inline-flex;
  align-items: baseline;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.run-side {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  white-space: nowrap;
}

.void-reason {
  color: var(--bad);
}

.item-list li.voided {
  opacity: 0.62;
}

.item-list li.voided a {
  text-decoration: line-through;
}

.void-form {
  display: inline-flex;
  gap: 0.45rem;
  align-items: center;
}

.void-form input {
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  min-width: 200px;
  font: inherit;
}

button.small {
  padding: 0.3rem 0.7rem;
  font-size: 0.82rem;
}
</style>
