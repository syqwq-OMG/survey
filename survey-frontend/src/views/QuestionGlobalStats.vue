<template>
  <div class="stats-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>全局题目统计</h2>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>

      <div v-loading="loading" style="min-height: 200px">
        <div v-if="stat" class="stat-content">
          <h3>{{ stat.title }} <el-tag type="info">{{ getTypeName(stat.type) }}</el-tag></h3>
          <p class="total-bar">
            <span>总答题量: <strong>{{ stat.total_responses }}</strong> 人次</span>
          </p>
          
          <div v-if="stat.type === 'single' || stat.type === 'multiple'" class="options-stat">
            <div v-for="(count, opt) in stat.options_count" :key="opt" class="opt-row">
               <span class="opt-name">{{ opt }}</span>
               <div style="flex: 1">
                 <el-progress 
                   :percentage="stat.total_responses ? Math.round((count / stat.total_responses) * 100) : 0" 
                   :format="(p) => `${p}% (${count})`" 
                 />
               </div>
            </div>
            <p v-if="!stat.options_count || Object.keys(stat.options_count).length === 0" style="color:#999">暂无答题数据</p>
          </div>
          
          <div v-else-if="stat.type === 'number'">
            <div class="stat-box">
               <div class="stat-item">
                 <span>平均值</span>
                 <strong>{{ stat.average?.toFixed(2) || 0 }}</strong>
               </div>
            </div>
          </div>
          
          <div v-else-if="stat.type === 'text'">
            <h4>填写示例选摘:</h4>
            <div class="text-answers">
              <el-tag v-for="(txt, i) in stat.text_answers" :key="i" type="info" class="text-tag">{{ txt }}</el-tag>
              <div v-if="!stat.text_answers?.length" style="color:#999">暂无答题数据</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const stat = ref(null)

const typeMap = { single: '单选题', multiple: '多选题', text: '文本填空', number: '数字填空' }
const getTypeName = (t) => typeMap[t] || t

const loadStats = async () => {
  loading.value = true
  try {
    const res = await request.get(`/api/stats/question/${route.params.id}`)
    stat.value = res
  } catch(e) {
    ElMessage.error("获取全局统计数据失败")
  } finally {
    loading.value = false
  }
}

onMounted(() => loadStats())
</script>
<style scoped>
.stats-container { padding: 20px; max-width: 800px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; }
.total-bar { font-size: 16px; margin: 20px 0; padding: 10px; background: #f4f4f5; border-radius: 4px;}
.opt-row { margin-bottom: 15px; display: flex; align-items: center; gap: 15px; }
.opt-name { min-width: 80px; }
.stat-box { display: flex; gap: 20px; }
.stat-item { padding: 20px; text-align: center; background: #fdfdfd; border: 1px solid #eee; border-radius: 8px;}
.stat-item span { display: block; color: #666; margin-bottom: 10px; }
.stat-item strong { font-size: 24px; color: #409eff; }
.text-answers { display: flex; flex-wrap: wrap; gap: 10px; }
.text-tag { max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
</style>
