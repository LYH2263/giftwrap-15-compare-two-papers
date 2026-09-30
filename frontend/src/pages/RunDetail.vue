<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const props = defineProps({ id: String })
const run = ref(null)
const err = ref('')
const showVoid = ref(false)
const reason = ref('')
const busy = ref(false)

async function load() {
  err.value = ''
  try {
    run.value = await getJSON(`/api/runs/${props.id}`)
  } catch (e) {
    err.value = String(e.message || e)
  }
}

onMounted(load)

function fmt(ts) {
  return ts ? String(ts).replace('T', ' ').slice(0, 25) : '—'
}

async function confirmVoid() {
  if (!reason.value.trim()) return
  busy.value = true
  err.value = ''
  try {
    run.value = await postJSON(`/api/runs/${props.id}/void`, { reason: reason.value.trim() })
    showVoid.value = false
    reason.value = ''
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <p v-if="err" class="bad">{{ err }}</p>
    <template v-else-if="run">
      <h1>
        用纸单 #{{ run.id }}
        <span v-if="run.status === 'voided'" class="pill warn">已作废</span>
      </h1>
      <p class="lede">
        {{ run.box_name }} · 落库于 {{ fmt(run.created_at) }}
      </p>

      <div v-if="run.status === 'voided'" class="void-banner">
        <strong>该单已作废（冲正），以下为原始测算，只读保留。</strong>
        <span>作废时间：{{ fmt(run.voided_at) }}</span>
        <span>作废原因：{{ run.void_reason }}</span>
      </div>

      <div class="result-board" style="border-top: none; padding-top: 0">
        <div class="figure">{{ run.result?.paper_m2 ?? '—' }}<span>m²</span></div>
        <p class="stat-line">盒表面积 {{ run.result?.box_surface }} m² · 折边系数 {{ run.overlap }}</p>
        <p v-if="run.note" class="stat-line">备注：{{ run.note }}</p>
      </div>

      <div class="row" style="margin-top: 1.25rem">
        <template v-if="run.status === 'active'">
          <button v-if="!showVoid" class="ribbon" @click="showVoid = true">作废此单</button>
          <span v-else class="void-form">
            <input v-model="reason" placeholder="必填：作废原因" @keyup.enter="confirmVoid" />
            <button class="ribbon" :disabled="busy || !reason.trim()" @click="confirmVoid">确认作废</button>
            <button class="ghost" @click="showVoid = false; reason = ''">取消</button>
          </span>
        </template>
        <router-link class="btn ghost" to="/history">返回用纸档</router-link>
      </div>
    </template>
  </div>
</template>

<style scoped>
.void-banner {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 1.25rem;
  padding: 0.9rem 1rem;
  border: 1px solid rgba(180, 35, 24, 0.3);
  border-left: 3px solid var(--bad);
  border-radius: var(--radius);
  background: rgba(180, 35, 24, 0.06);
  color: var(--ink);
  font-size: 0.92rem;
}

.void-banner strong {
  color: var(--bad);
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
  min-width: 220px;
  font: inherit;
}
</style>
