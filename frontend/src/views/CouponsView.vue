<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')

const coupons = ref([])
const rolls = ref([])
const error = ref('')
const notice = ref('')
const busy = ref(false)
const filterRollId = ref('')

const form = reactive({
  rollId: null,
  couponNo: 1,
  blisterGrade: 0,
  inspectedAt: '',
})

function localNow() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString() : '—'
}

function stateOf(row) {
  if (row.voidedAt) return { text: '已作废', cls: 'badge-void' }
  if (row.blisterGrade === 0) return { text: '合格', cls: 'badge-pass' }
  return { text: '不合格', cls: 'badge-fail' }
}

async function load() {
  error.value = ''
  try {
    const params = filterRollId.value ? { rollId: filterRollId.value } : {}
    const [c, r] = await Promise.all([
      api.get('/coupons/', { params }),
      api.get('/rolls/'),
    ])
    coupons.value = c.data.results || c.data
    rolls.value = r.data.results || r.data
    if (!form.rollId && rolls.value.length) form.rollId = rolls.value[0].id
    if (!form.inspectedAt) form.inspectedAt = localNow()
    suggestNextNo()
  } catch {
    error.value = '盐雾试片台账加载失败'
  }
}

function suggestNextNo() {
  if (!form.rollId) return
  // 列表被筛到别的卷时，号段建议不可靠，交给服务端唯一约束兜底
  if (filterRollId.value && filterRollId.value !== form.rollId) return
  const actives = coupons.value
    .filter((c) => c.rollId === form.rollId && !c.voidedAt)
    .map((c) => c.couponNo)
  form.couponNo = actives.length ? Math.max(...actives) + 1 : 1
}

watch(() => form.rollId, suggestNextNo)
watch(filterRollId, load)

function fieldError(data) {
  if (!data) return ''
  return (
    data?.couponNo?.[0] ||
    data?.blisterGrade?.[0] ||
    data?.rollId?.[0] ||
    data?.inspectedAt?.[0] ||
    data?.detail ||
    ''
  )
}

async function create() {
  error.value = ''
  notice.value = ''
  busy.value = true
  try {
    await api.post('/coupons/', {
      rollId: form.rollId,
      couponNo: form.couponNo,
      blisterGrade: form.blisterGrade,
      inspectedAt: new Date(form.inspectedAt).toISOString(),
    })
    notice.value = `已写入 ${form.couponNo} 号条`
    form.inspectedAt = localNow()
    await load()
  } catch (e) {
    error.value = fieldError(e.response?.data) || '建条失败'
  } finally {
    busy.value = false
  }
}

async function voidCoupon(row) {
  error.value = ''
  notice.value = ''
  busy.value = true
  try {
    await api.post(`/coupons/${row.id}/void/`)
    notice.value = `${row.rollCode} 的 ${row.couponNo} 号条已作废`
    await load()
  } catch (e) {
    error.value = fieldError(e.response?.data) || '作废失败'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>盐雾试片</h1>
    <p class="sub">
      专页台账：按卷筛选、新建检验条；作废仅管理员。布卷标「已固化」须有一张未作废且起泡级数为 0 的合格条。
    </p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="notice" class="ok">{{ notice }}</p>

    <form class="panel row" @submit.prevent="create">
      <label>布卷
        <select v-model.number="form.rollId" required>
          <option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.rollCode }} · {{ r.loftName }}</option>
        </select>
      </label>
      <label>条号（从 1 起）
        <input v-model.number="form.couponNo" type="number" min="1" step="1" required />
      </label>
      <label>起泡级数（0–5）
        <input v-model.number="form.blisterGrade" type="number" min="0" max="5" step="1" required />
      </label>
      <label>检验时刻
        <input v-model="form.inspectedAt" type="datetime-local" required />
      </label>
      <button class="btn" type="submit" :disabled="busy">新建检验条</button>
    </form>

    <div class="panel row">
      <label>按卷筛选
        <select v-model="filterRollId">
          <option value="">全部布卷</option>
          <option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.rollCode }} · {{ r.loftName }}</option>
        </select>
      </label>
      <button class="btn secondary" type="button" @click="load">刷新</button>
    </div>

    <table>
      <thead>
        <tr>
          <th>布卷</th>
          <th>帆布间</th>
          <th>条号</th>
          <th>起泡级数</th>
          <th>检验时刻</th>
          <th>检验人</th>
          <th>状态</th>
          <th>作废时刻</th>
          <th v-if="isAdmin"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in coupons" :key="row.id">
          <td>{{ row.rollCode }}</td>
          <td>{{ row.loftName }}</td>
          <td>{{ row.couponNo }}</td>
          <td>{{ row.blisterGrade }} 级</td>
          <td>{{ fmt(row.inspectedAt) }}</td>
          <td>{{ row.inspectorName }}</td>
          <td><span class="badge" :class="stateOf(row).cls">{{ stateOf(row).text }}</span></td>
          <td>{{ fmt(row.voidedAt) }}</td>
          <td v-if="isAdmin">
            <button
              v-if="!row.voidedAt"
              class="btn secondary"
              type="button"
              :disabled="busy"
              @click="voidCoupon(row)"
            >
              作废
            </button>
          </td>
        </tr>
        <tr v-if="!coupons.length">
          <td :colspan="isAdmin ? 9 : 8" class="hint">暂无盐雾试片检验条</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
