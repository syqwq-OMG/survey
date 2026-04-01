<template>
  <div class="stats-container">
    <el-card class="box-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>📊 问卷数据看板</h2>
          <div>
            <el-button
              type="success"
              @click="exportJson"
              :disabled="!statsData"
            >
              导出 JSON 数据
            </el-button>
            <el-button @click="router.push('/dashboard')">返回列表</el-button>
          </div>
        </div>
        <div v-if="statsData" class="summary-info">
          <el-tag size="large" type="primary"
            >总提交份数: {{ statsData.total_submissions }}</el-tag
          >
        </div>
      </template>

      <div v-if="statsData && statsData.questions.length > 0">
        <div
          v-for="(q, index) in statsData.questions"
          :key="q.q_id"
          class="stat-block"
        >
          <div class="q-title">
            Q{{ index + 1 }}. {{ q.title }}
            <el-tag size="small" type="info">{{ typeMap[q.type] }}</el-tag>
            <span class="reply-count">回答人数: {{ q.total_responses }}</span>
          </div>

          <div
            v-if="q.type === 'single' || q.type === 'multiple'"
            :id="'chart-' + q.q_id"
            class="chart-container"
          ></div>

          <div v-else-if="q.type === 'number'" class="number-stat">
            <el-statistic title="平均值" :value="q.average" :precision="2" />
          </div>

          <div v-else-if="q.type === 'text'" class="text-stat">
            <el-scrollbar max-height="200px">
              <ul v-if="q.text_answers && q.text_answers.length > 0">
                <li
                  v-for="(text, tIndex) in q.text_answers"
                  :key="tIndex"
                  class="text-answer-item"
                >
                  {{ text }}
                </li>
              </ul>
              <el-empty v-else description="暂无文本回答" :image-size="60" />
            </el-scrollbar>
          </div>
        </div>
      </div>
      <el-empty v-else-if="!loading" description="暂无统计数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import * as echarts from "echarts";
import request from "../utils/request";

const route = useRoute();
const router = useRouter();
const surveyId = route.params.id;

const loading = ref(true);
const statsData = ref(null);

const typeMap = {
  single: "单选题",
  multiple: "多选题",
  text: "文本填空",
  number: "数字填空",
};

onMounted(async () => {
  try {
    statsData.value = await request.get(`/api/surveys/${surveyId}/stats`);
    // 数据渲染到 DOM 后，初始化 ECharts
    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(
      error.response?.data?.detail || "获取统计数据失败，请确认是否有权限",
    );
  } finally {
    loading.value = false;
  }
});

// 渲染图表核心逻辑
const renderCharts = () => {
  if (!statsData.value) return;

  statsData.value.questions.forEach((q) => {
    if (q.type === "single" || q.type === "multiple") {
      const dom = document.getElementById("chart-" + q.q_id);
      if (!dom) return;

      const myChart = echarts.init(dom);
      const dataFormat = Object.entries(q.option_counts || {}).map(
        ([name, value]) => ({ name, value }),
      );

      const option = {
        tooltip: { trigger: q.type === "single" ? "item" : "axis" },
        // 单选题用饼图，多选题用柱状图
        series:
          q.type === "single"
            ? [{ type: "pie", radius: "60%", data: dataFormat }]
            : [{ type: "bar", data: dataFormat.map((item) => item.value) }],
        xAxis:
          q.type === "multiple"
            ? { type: "category", data: dataFormat.map((item) => item.name) }
            : undefined,
        yAxis:
          q.type === "multiple" ? { type: "value", minInterval: 1 } : undefined,
      };

      myChart.setOption(option);
    }
  });
};

// 导出 JSON 逻辑
const exportJson = () => {
  if (!statsData.value) return;
  const dataStr =
    "data:text/json;charset=utf-8," +
    encodeURIComponent(JSON.stringify(statsData.value, null, 2));
  const downloadAnchorNode = document.createElement("a");
  downloadAnchorNode.setAttribute("href", dataStr);
  downloadAnchorNode.setAttribute("download", `survey_stats_${surveyId}.json`);
  document.body.appendChild(downloadAnchorNode);
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
  ElMessage.success("导出成功！");
};
</script>

<style scoped>
.stats-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.summary-info {
  margin-top: 15px;
}
.stat-block {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}
.q-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 20px;
}
.reply-count {
  float: right;
  font-weight: normal;
  font-size: 14px;
  color: #909399;
}
.chart-container {
  height: 300px;
  width: 100%;
}
.number-stat {
  text-align: center;
  padding: 30px 0;
}
.text-answer-item {
  padding: 8px 10px;
  border-bottom: 1px solid #eee;
  color: #606266;
  font-size: 14px;
}
.text-answer-item:last-child {
  border-bottom: none;
}
</style>
