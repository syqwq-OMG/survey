<template>
  <div class="builder-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <h2>✨ 创建新问卷</h2>
          <el-button type="primary" size="large" @click="submitSurvey" :loading="loading">保存并生成问卷</el-button>
        </div>
      </template>

      <el-form label-width="100px" class="base-info-form">
        <el-form-item label="问卷标题">
          <el-input v-model="survey.title" placeholder="请输入问卷标题" />
        </el-form-item>
        <el-form-item label="问卷说明">
          <el-input v-model="survey.description" type="textarea" placeholder="请输入感谢语或填写说明" />
        </el-form-item>
        <el-form-item label="匿名填写">
          <el-switch v-model="survey.is_anonymous" active-text="允许" inactive-text="必须登录" />
        </el-form-item>
      </el-form>

      <el-divider border-style="dashed" />

      <div v-for="(q, index) in survey.questions" :key="q.q_id" class="question-block">
        <div class="q-header">
          <span class="q-title">Q{{ index + 1 }}. {{ getTypeName(q.type) }}</span>
          <el-button type="danger" icon="Delete" circle size="small" @click="removeQuestion(index)" />
        </div>
        
        <el-form label-width="80px" size="small">
          <el-form-item label="题目内容">
            <el-input v-model="q.title" placeholder="请输入题目..." />
          </el-form-item>
          <el-form-item label="是否必答">
            <el-switch v-model="q.is_required" />
          </el-form-item>

          <template v-if="q.type === 'single' || q.type === 'multiple'">
            <el-form-item label="选项设置">
              <div v-for="(opt, oIndex) in q.options" :key="oIndex" class="option-item">
                <el-input v-model="q.options[oIndex]" placeholder="选项内容" style="width: 200px; margin-right: 10px;" />
                <el-button type="danger" link @click="removeOption(q, oIndex)">删除</el-button>
              </div>
              <el-button type="primary" link @click="addOption(q)">+ 添加选项</el-button>
            </el-form-item>
          </template>

          <template v-if="q.type === 'multiple'">
            <el-form-item label="选择限制">
              最少选 <el-input-number v-model="q.constraints.min_select" :min="1" style="width: 100px; margin: 0 10px;" /> 项，
              最多选 <el-input-number v-model="q.constraints.max_select" :min="1" style="width: 100px; margin: 0 10px;" /> 项
            </el-form-item>
          </template>

          <template v-if="q.type === 'number'">
            <el-form-item label="数值限制">
              最小值 <el-input-number v-model="q.constraints.min_value" style="width: 120px; margin: 0 10px;" />
              最大值 <el-input-number v-model="q.constraints.max_value" style="width: 120px; margin: 0 10px;" />
              <el-checkbox v-model="q.constraints.is_integer">必须为整数</el-checkbox>
            </el-form-item>
          </template>

          <el-divider border-style="dotted" />
          <el-form-item label="跳转逻辑" style="margin-bottom: 0;">
            <div 
              v-for="(logic, lIndex) in q.jump_logic" 
              :key="lIndex" 
              style="margin-bottom: 10px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;"
            >
              <span style="font-size: 13px; color: #606266;">如果本题等于</span>
              
              <el-select 
                v-if="q.type === 'single' || q.type === 'multiple'" 
                v-model="logic.condition_value" 
                placeholder="请选择触发选项" 
                size="small" 
                style="width: 160px;"
              >
                <el-option v-for="opt in q.options" :key="opt" :label="opt" :value="opt" />
              </el-select>
              
              <el-input-number 
                v-else-if="q.type === 'number'" 
                v-model="logic.condition_value" 
                size="small" 
                style="width: 160px;" 
                placeholder="触发数字"
              />
              
              <el-input 
                v-else 
                v-model="logic.condition_value" 
                placeholder="触发文本" 
                size="small" 
                style="width: 160px;" 
              />

              <span style="font-size: 13px; color: #606266;">则跳转到</span>
              
              <el-select 
                v-model="logic.target_q_id" 
                placeholder="选择目标题目" 
                size="small" 
                style="width: 200px;"
              >
                <template v-for="(targetQ, tIndex) in survey.questions" :key="targetQ.q_id">
                  <el-option 
                    v-if="targetQ.q_id !== q.q_id" 
                    :label="`Q${tIndex + 1}. ` + (targetQ.title || '未命名题目')" 
                    :value="targetQ.q_id" 
                  />
                </template>
              </el-select>
              
              <el-button type="danger" link @click="removeJumpLogic(q, lIndex)">删除</el-button>
            </div>
            
            <div style="width: 100%;">
              <el-button type="primary" link @click="addJumpLogic(q)">+ 添加跳转规则</el-button>
            </div>
          </el-form-item>
          </el-form>
      </div>

      <div class="add-toolbar">
        <el-button type="primary" plain @click="addQuestion('single')">+ 单选题</el-button>
        <el-button type="success" plain @click="addQuestion('multiple')">+ 多选题</el-button>
        <el-button type="info" plain @click="addQuestion('text')">+ 文本填空</el-button>
        <el-button type="warning" plain @click="addQuestion('number')">+ 数字填空</el-button>
      </div>

    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const loading = ref(false)

// 响应式的问卷数据树，完美替代手写 JSON
const survey = reactive({
  title: '',
  description: '',
  is_anonymous: true,
  questions: []
})

// 生成随机的 q_id
const generateId = () => 'q_' + Math.random().toString(36).substr(2, 9)

const typeMap = {
  'single': '单选题',
  'multiple': '多选题',
  'text': '文本填空',
  'number': '数字填空'
}
const getTypeName = (type) => typeMap[type]

// 核心逻辑：工厂模式添加题目
const addQuestion = (type) => {
  const baseQ = {
    q_id: generateId(),
    type: type,
    title: '',
    is_required: true,
    jump_logic: [] // 初始化跳转逻辑数组
  }

  // 根据题型附带不同的默认结构
  if (type === 'single') {
    baseQ.options = ['选项1', '选项2']
    baseQ.constraints = {}
  } else if (type === 'multiple') {
    baseQ.options = ['选项1', '选项2']
    baseQ.constraints = { min_select: 1, max_select: 2 }
  } else if (type === 'number') {
    baseQ.constraints = { min_value: 0, max_value: 100, is_integer: false }
  } else {
    baseQ.constraints = {}
  }

  survey.questions.push(baseQ)
}

const removeQuestion = (index) => {
  survey.questions.splice(index, 1)
}

const addOption = (q) => {
  q.options.push(`新选项${q.options.length + 1}`)
}

const removeOption = (q, oIndex) => {
  q.options.splice(oIndex, 1)
}

// 跳转规则的增删逻辑
const addJumpLogic = (q) => {
  if (!q.jump_logic) {
    q.jump_logic = []
  }
  q.jump_logic.push({ 
    condition_value: null, 
    target_q_id: '' 
  })
}

const removeJumpLogic = (q, lIndex) => {
  q.jump_logic.splice(lIndex, 1)
}

// 提交整个数据树给后端
const submitSurvey = async () => {
  if (!survey.title) {
    ElMessage.warning('请填写问卷标题')
    return
  }
  if (survey.questions.length === 0) {
    ElMessage.warning('至少需要添加一道题目')
    return
  }

  loading.value = true
  try {
    await request.post('/api/surveys', survey)
    ElMessage.success('问卷创建成功！')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.builder-container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.base-info-form {
  max-width: 600px;
}
.question-block {
  border: 1px solid #ebeef5;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
  background-color: #fafafa;
  transition: all 0.3s;
}
.question-block:hover {
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
.q-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}
.q-title {
  font-weight: bold;
  color: #409EFF;
}
.option-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.add-toolbar {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  border: 2px dashed #dcdfe6;
  border-radius: 4px;
}
</style>