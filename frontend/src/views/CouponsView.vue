<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const coupons = ref([])
const rolls = ref([])
const lofts = ref([])
const error = ref('')
const formError = ref('')
const busy = ref(false)

const isAdmin = computed(() => auth.user?.role === 'admin')

const form = reactive({
  rollId: null,
  stripNo: 1,
  blisterGrade: 0,
  inspectedAt: '',
})

const gradeLabel = (g) => `起泡 ${g} 级`

function localNow() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

const selectedRoll = computed(
  () => rolls.value.find((r) => r.id === Number(form.rollId)) || null
)

// 按卷筛选：仅展示所选卷的条。
async function loadCoupons() {
  if (!form.rollId) {
    coupons.value = []
    return
  }
  const { data } = await api.get('/coupons/', { params: { rollId: form.rollId } })
  coupons.value = data.results || data
}

async function load() {
  error.value = ''
  try {
    const [r, l] = await Promise.all([api.get('/rolls/'), api.get('/lofts/')])
    rolls.value = r.data.results || r.data
    lofts.value = l.data.results || l.data
    const queryRoll = Number(route.query.rollId)
    if (queryRoll && rolls.value.some((r) => r.id === queryRoll)) {
      form.rollId = queryRoll
    } else if (!form.rollId && rolls.value.length) {
      form.rollId = rolls.value[0].id
    }
    if (!form.inspectedAt) form.inspectedAt = localNow()
    await loadCoupons()
  } catch {
    error.value = '盐雾试片数据加载失败'
  }
}

function rollName(id) {
  const r = rolls.value.find((x) => x.id === id)
  return r ? `${r.rollCode} · ${r.loftName}` : `卷#${id}`
}

watch(
  () => form.rollId,
  async (id) => {
    router.replace({ query: id ? { rollId: id } : {} })
    formError.value = ''
    await loadCoupons()
  }
)

async function createCoupon() {
  formError.value = ''
  busy.value = true
  try {
    await api.post('/coupons/', {
      rollId: form.rollId,
      stripNo: form.stripNo,
      blisterGrade: form.blisterGrade,
      inspectedAt: new Date(form.inspectedAt).toISOString(),
    })
    form.stripNo += 1
    await loadCoupons()
  } catch (e) {
    const data = e.response?.data
    formError.value =
      data?.stripNo?.[0] ||
      data?.blisterGrade?.[0] ||
      data?.rollId?.[0] ||
      data?.detail ||
      '建条失败'
  } finally {
    busy.value = false
  }
}

async function voidCoupon(coupon) {
  formError.value = ''
  busy.value = true
  try {
    await api.post(`/coupons/${coupon.id}/void/`)
    await loadCoupons()
  } catch (e) {
    formError.value = e.response?.data?.detail || '作废失败'
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
      按卷查看试片条、登记新条。起泡级数 0–5；只有未作废且起泡级数为 0 的最新条可放行固化。
      建条操作工可做，作废仅管理员。
    </p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="formError" class="error">{{ formError }}</p>

    <form class="panel row" @submit.prevent="createCoupon">
      <label>布卷
        <select v-model.number="form.rollId" required>
          <option v-for="r in rolls" :key="r.id" :value="r.id">
            {{ r.rollCode }} · {{ r.loftName }}
          </option>
        </select>
      </label>
      <label>条号（从 1 起）
        <input v-model.number="form.stripNo" type="number" min="1" step="1" required />
      </label>
      <label>起泡级数
        <select v-model.number="form.blisterGrade" required>
          <option v-for="g in 6" :key="g - 1" :value="g - 1">{{ g - 1 }} 级</option>
        </select>
      </label>
      <label>检验时刻
        <input v-model="form.inspectedAt" type="datetime-local" required />
      </label>
      <button class="btn" type="submit" :disabled="busy || !form.rollId">建条</button>
    </form>

    <section class="panel">
      <h2 class="feed-title">
        本卷试片<small v-if="selectedRoll" class="hint">　{{ selectedRoll.rollCode }} · {{ selectedRoll.loftName }}</small>
      </h2>
      <table>
        <thead>
          <tr>
            <th>条号</th>
            <th>起泡级数</th>
            <th>是否合格</th>
            <th>检验时刻</th>
            <th>检验人</th>
            <th>状态</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in coupons" :key="c.id" :class="{ 'row-void': c.voidedAt }">
            <td>{{ c.stripNo }}</td>
            <td>{{ c.blisterGrade }}</td>
            <td>
              <span v-if="c.blisterGrade === 0 && !c.voidedAt" class="ok">合格</span>
              <span v-else class="hint">不可放行</span>
            </td>
            <td>{{ new Date(c.inspectedAt).toLocaleString() }}</td>
            <td>{{ c.inspectorName }}</td>
            <td>
              <span v-if="c.voidedAt" class="badge">已作废 {{ new Date(c.voidedAt).toLocaleString() }}</span>
              <span v-else class="badge badge-dipping">有效</span>
            </td>
            <td>
              <button
                v-if="isAdmin && !c.voidedAt"
                class="btn secondary"
                type="button"
                :disabled="busy"
                @click="voidCoupon(c)"
              >
                作废
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="form.rollId && !coupons.length" class="hint" style="margin-top:10px">
        本卷尚无盐雾试片条
      </p>
    </section>
  </div>
</template>

<style scoped>
.row-void {
  opacity: 0.55;
}
</style>
