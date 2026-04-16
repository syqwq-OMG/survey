<template>
  <div class="question-bank-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>题库中心</h2>
          <el-button type="primary" @click="router.push('/dashboard')">返回工作台</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="loadQuestions">
        <el-tab-pane label="我的题库" name="my"></el-tab-pane>
        <el-tab-pane label="共享大厅" name="shared"></el-tab-pane>
      </el-tabs>

      <el-table :data="questions" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="题目内容" />
        <el-table-column prop="type" label="题型" width="120">
          <template #default="{ row }">
             {{ getTypeName(row.type) }}
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="is_shared" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_shared ? 'success' : 'info'">
              {{ row.is_shared ? '已共享' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewStats(row)">全局统计</el-button>
            <el-button size="small" type="info" link @click="viewDependencies(row)">引用明细</el-button>
            <el-switch v-if="activeTab === 'my'" v-model="row.is_shared" @change="toggleShare(row)" size="small" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Dependencies Dialog -->
    <el-dialog v-model="depDialogVisible" title="被以下问卷引用">
      <el-table :data="dependencies" v-loading="depLoading">
        <el-table-column prop="id" label="问卷ID" width="220" />
        <el-table-column prop="title" label="问卷标题" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'warning'">
              {{ row.is_active ? '进行中' : '未发布' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const activeTab = ref('my')
const questions = ref([])
const loading = ref(false)

const depDialogVisible = ref(false)
const dependencies = ref([])
const depLoading = ref(false)

const typeMap = { single: '单选题', multiple: '多选题', text: '文本填空', number: '数字填空' }
const getTypeName = (t) => typeMap[t]

const loadQuestions = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/questions', {
      params: { is_shared: activeTab.value === 'shared' ? true : false }
    })
    questions.value = res.data
  } catch(e) {
    ElMessage.error("获取题库失败")
  } finally {
    loading.value = false
  }
}

const toggleShare = async (row) => {
  try {
    await request.post(`/api/questions/${row.id}/share`, { is_shared: row.is_shared })
    ElMessage.success("状态已更新")
  } catch(e) {
    ElMessage.error("状态更新失败")
    row.is_shared = !row.is_shared
  }
}

const viewStats = (row) => {
  router.push(`/stats/question/${row.original_q_id}`)
}

const viewDependencies = async (row) => {
  depDialogVisible.value = true
  depLoading.value = true
  try {
    const res = await request.get(`/api/questions/${row.id}/dependencies`)
    dependencies.value = res.data
  } catch(e) {
    ElMessage.error("获取引用情况失败")
  } finally {
    depLoading.value = false
  }
}

onMounted(() => loadQuestions())
</script>
<style scoped>
.question-bank-container { padding: 20px; max-width: 1000px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; }
</style>
