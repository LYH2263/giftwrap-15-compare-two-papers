<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const props = defineProps({ id: { type: [String, Number], required: true } })
const run = ref(null)
const err = ref('')

onMounted(async () => {
  try {
    run.value = await getJSON(`/api/runs/${props.id}`)
  } catch (e) {
    err.value = String(e.message || e)
  }
})
</script>

<template>
  <div class="page">
    <router-link class="back" to="/history">← 用纸档</router-link>

    <p v-if="err" class="bad">{{ err }}</p>
    <template v-else-if="run">
      <div class="detail-head">
        <h1>用纸档 #{{ run.id }} · {{ run.box_name ?? '未知盒' }}</h1>
        <span v-if="run.status === 'voided'" class="pill warn">已作废（只读）</span>
        <span v-else class="pill">活跃</span>
      </div>

      <div class="result-board">
        <div class="figure">{{ run.result?.paper_m2 ?? '—' }}<span>m² 用纸面积</span></div>
        <p class="stat-line">盒表面积：{{ run.result?.box_surface ?? '—' }} m² ｜ 折边系数：{{ run.overlap }}</p>
        <p class="stat-line">落库时间：{{ run.created_at }}</p>
        <p v-if="run.note" class="stat-line">备注：{{ run.note }}</p>
      </div>

      <div v-if="run.status === 'voided'" class="void-box">
        <h2>作废信息</h2>
        <p class="stat-line"><strong>作废原因：</strong>{{ run.void_reason }}</p>
        <p class="stat-line">作废时间：{{ run.voided_at }}</p>
        <p class="stat-line void-note">该单仅作冲正留痕，原测算数字保持不变，不做物理删除。</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.back {
  display: inline-block;
  margin-bottom: 1rem;
  color: var(--ink-soft);
  text-decoration: none;
  font-size: 0.9rem;
}
.back:hover {
  color: var(--wash-b);
}
.detail-head {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: wrap;
}
.void-box {
  margin-top: 1.4rem;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(180, 35, 24, 0.3);
  border-left: 3px solid var(--bad);
  border-radius: var(--radius);
  background: rgba(180, 35, 24, 0.05);
}
.void-box h2 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
}
.void-note {
  font-size: 0.82rem;
  color: var(--ink-soft);
}
</style>
