<template>
  <div class="survey-fill-container">
    <el-card class="survey-card" v-loading="loading">
      <template v-if="survey">
        <div class="survey-header">
          <h1>{{ survey.title }}</h1>
          <p class="description">{{ survey.description }}</p>
        </div>

        <div v-if="survey.deadline" style="margin-bottom: 20px;">
          <el-alert 
            :title="isExpired ? '该问卷已超过截止时间，停止收集' : '问卷截止时间：' + new Date(survey.deadline).toLocaleString()" 
            :type="isExpired ? 'error' : 'warning'" 
            :closable="false" 
            show-icon 
            center
          />
        </div>

        <el-divider />

        <el-form :model="formData" label-position="top" size="large">
          <div
            v-for="(q, index) in survey.questions"
            :key="q.q_id"
            v-show="!hiddenQuestions.has(q.q_id)"
            class="question-item"
          >
            <el-form-item :required="q.is_required">
              <template #label>
                <span class="q-title">{{ index + 1 }}. {{ q.title }}</span>
                <span class="q-type-tag"> [{{ typeMap[q.type] }}] </span>
              </template>

              <el-radio-group
                v-if="q.type === 'single'"
                v-model="formData[q.q_id]"
                @change="evaluateJumpLogic"
              >
                <el-radio v-for="opt in q.options" :key="opt" :value="opt">
                  {{ opt }}
                </el-radio>
              </el-radio-group>

              <el-checkbox-group
                v-else-if="q.type === 'multiple'"
                v-model="formData[q.q_id]"
                @change="evaluateJumpLogic"
              >
                <el-checkbox v-for="opt in q.options" :key="opt" :value="opt">
                  {{ opt }}
                </el-checkbox>
              </el-checkbox-group>

              <el-input-number
                v-else-if="q.type === 'number'"
                v-model="formData[q.q_id]"
                :min="q.constraints?.min_value"
                :max="q.constraints?.max_value"
                :step="q.constraints?.is_integer ? 1 : 0.1"
                @change="evaluateJumpLogic"
              />

              <el-input
                v-else-if="q.type === 'text'"
                v-model="formData[q.q_id]"
                type="textarea"
                rows="3"
                placeholder="请输入您的回答..."
                :minlength="q.constraints?.min_length"
                :maxlength="q.constraints?.max_length"
                show-word-limit
              />
            </el-form-item>
          </div>

          <div class="submit-action">
            <el-button
              type="primary"
              size="large"
              @click="submitResponse"
              :loading="submitting":disabled="isExpired"
            >
              提交答卷
            </el-button>
          </div>
        </el-form>
      </template>

      <el-empty v-else-if="!loading" description="问卷不存在或已关闭" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed} from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "../utils/request";

const route = useRoute();
const router = useRouter();
const surveyId = route.params.id;

const loading = ref(true);
const submitting = ref(false);
const survey = ref(null);

// 用户的答卷数据字典 { q_id: value }
const formData = reactive({});
// 被跳转逻辑隐藏的题目集合
const hiddenQuestions = ref(new Set());

const typeMap = {
  single: "单选",
  multiple: "多选",
  text: "填空",
  number: "数字",
};

onMounted(async () => {
  try {
    // 拉取问卷题目定义
    survey.value = await request.get(`/api/surveys/${surveyId}`);

    // 初始化响应式表单数据
    survey.value.questions.forEach((q) => {
      if (q.type === "multiple") {
        formData[q.q_id] = []; // 多选默认是空数组
      } else {
        formData[q.q_id] = null;
      }
    });
  } catch (error) {
    ElMessage.error("无法加载问卷信息");
  } finally {
    loading.value = false;
  }
});

// 核心引擎：执行跳转逻辑
const evaluateJumpLogic = () => {
  const newHidden = new Set();
  const questions = survey.value.questions;

  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    if (!q.jump_logic || q.jump_logic.length === 0) continue;

    const currentValue = formData[q.q_id];
    let targetId = null;

    // 检查是否命中跳转规则
    for (const logic of q.jump_logic) {
      if (q.type === "single" && currentValue === logic.condition_value) {
        targetId = logic.target_q_id;
        break;
      } else if (
        q.type === "multiple" &&
        Array.isArray(logic.condition_value)
      ) {
        // 多选题逻辑：用户选择的选项必须包含设定的所有触发选项 (子集匹配)
        const isMatch =
          logic.condition_value.length > 0 &&
          logic.condition_value.every((v) => currentValue.includes(v));
        if (isMatch) {
          targetId = logic.target_q_id;
          break;
        }
      } else if (
        q.type === "number" &&
        currentValue === Number(logic.condition_value)
      ) {
        targetId = logic.target_q_id;
        break;
      }
    }

    // 如果命中了，计算出中间需要隐藏的题目
    if (targetId) {
      const targetIndex = questions.findIndex((item) => item.q_id === targetId);
      if (targetIndex > i) {
        for (let j = i + 1; j < targetIndex; j++) {
          newHidden.add(questions[j].q_id);
        }
      }
    }
  }
  hiddenQuestions.value = newHidden;
};

// 计算属性：判断是否已过期
const isExpired = computed(() => {
  if (!survey.value || !survey.value.deadline) return false
  return new Date(survey.value.deadline) < new Date()
})

const submitResponse = async () => {
  // 1. 构造后端需要的 payload 格式
  const answers = [];

  for (const q of survey.value.questions) {
    // 如果题目被跳转逻辑隐藏了，就不收集它的答案
    if (hiddenQuestions.value.has(q.q_id)) continue;

    const val = formData[q.q_id];

    // 2. 简单的前端必填项拦截
    if (q.is_required) {
      if (
        val === null ||
        val === "" ||
        (Array.isArray(val) && val.length === 0)
      ) {
        ElMessage.warning(
          `第 ${survey.value.questions.indexOf(q) + 1} 题是必填项，请填写后再提交！`,
        );
        return;
      }
    }

    // 过滤掉没填的非必填项
    if (
      val !== null &&
      val !== "" &&
      !(Array.isArray(val) && val.length === 0)
    ) {
      answers.push({ q_id: q.q_id, value: val });
    }
  }

  // 3. 提交给后端 (接受后端的硬核校验)
  submitting.value = true;
  try {
    await request.post(`/api/surveys/${surveyId}/responses`, { answers });

    ElMessageBox.alert("您的答卷已成功提交，感谢您的参与！", "提交成功", {
      confirmButtonText: "确定",
      type: "success",
      callback: () => {
        // 提交成功后可以关闭页面或返回主页
        router.push("/");
      },
    });
  } catch (error) {
    // 如果后端校验不通过 (比如多选题选的太少)，把后端的 400 错误抛给用户
    ElMessage.error(error.response?.data?.detail || "提交失败，请检查填写内容");
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.survey-fill-container {
  min-height: 100vh;
  padding: 40px 20px;
  background-color: #f0f2f5;
  display: flex;
  justify-content: center;
}
.survey-card {
  width: 100%;
  max-width: 800px;
  border-radius: 8px;
}
.survey-header {
  text-align: center;
  margin-bottom: 30px;
}
.description {
  color: #666;
  font-size: 15px;
  white-space: pre-wrap;
}
.question-item {
  margin-bottom: 25px;
  padding: 15px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}
.q-title {
  font-size: 16px;
  font-weight: bold;
}
.q-type-tag {
  color: #909399;
  font-size: 13px;
  margin-left: 8px;
  font-weight: normal;
}
.submit-action {
  text-align: center;
  margin-top: 40px;
}
</style>
