<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const items = ref([])
const activeCount = ref(0)
const activeArea = ref(0)
const includeVoided = ref(false)
const err = ref('')
const busy = ref(false)

async function load() {
  err.value = ''
  try {
    const data = await getJSON(`/api/runs?include_voided=${includeVoided.value}`)
    items.value = data.items
    activeCount.value = data.active_count
    activeArea.value = data.active_area_m2
  } catch (e) {
    err.value = String(e.message || e)
  }
}

async function voidRun(r) {
  const reason = window.prompt(`作废 #${r.id}（${r.box_name ?? '未知盒'}）的作废原因：`)
  if (reason === null) return
  const trimmed = reason.trim()
  if (!trimmed) {
    window.alert('必须填写作废原因。')
    return
  }
  busy.value = true
  try {
    await postJSON(`/api/runs/${r.id}/void`, { reason: trimmed })
    await load()
  } catch (e) {
    window.alert('作废失败：' + String(e.message || e))
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1>用纸档</h1>
    <p class="lede">算纸页「写入用纸档」后的落库结果，按次保留盒名与面积。作废为冲正留痕：原测算数字不改动，只附写作废原因与时间。</p>

    <div class="row">
      <label class="toggle">
        <input type="checkbox" v-model="includeVoided" @change="load" />
        含作废
      </label>
      <span class="meta">
        活跃合计：<strong>{{ activeCount }}</strong> 单 ·
        <strong>{{ activeArea }}</strong> m²
        <span class="meta-note">（仅计活跃单，作废单不计）</span>
      </span>
    </div>

    <p v-if="err" class="bad">{{ err }}</p>
    <p v-else-if="!items.length" class="empty">还没有写入过。先去算纸试一单。</p>
    <ul v-else class="item-list">
      <li v-for="r in items" :key="r.id" :class="{ 'is-void': r.status === 'voided' }">
        <span class="run-main">
          <router-link :to="`/history/${r.id}`">#{{ r.id }} {{ r.box_name ?? '未知盒' }}</router-link>
          <span v-if="r.status === 'voided'" class="pill warn">已作废</span>
        </span>
        <span class="run-side">
          <span class="meta">{{ r.result?.paper_m2 ?? '—' }} m²</span>
          <button
            v-if="r.status !== 'voided'"
            class="ghost btn-sm"
            :disabled="busy"
            @click="voidRun(r)"
          >作废</button>
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  cursor: pointer;
}
.meta-note {
  font-size: 0.8rem;
}
.run-main {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
}
.run-side {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
}
.btn-sm {
  padding: 0.25rem 0.7rem;
  font-size: 0.82rem;
}
.item-list li.is-void {
  opacity: 0.62;
}
.item-list li.is-void a {
  text-decoration: line-through;
  text-decoration-color: var(--ribbon);
}
</style>
