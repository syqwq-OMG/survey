<template>
  <div class="dashboard-layout">
    <el-menu mode="horizontal" :ellipsis="false" class="top-menu">
      <div class="logo">🚀 问卷管理中心</div>
      <div class="flex-grow" />
      <el-menu-item index="1">
        <span class="welcome-text">欢迎, {{ username }}</span>
      </el-menu-item>
      <el-menu-item index="2" @click="handleLogout">
        <el-button type="danger" plain size="small">退出登录</el-button>
      </el-menu-item>
    </el-menu>

    <div class="main-content">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>我的问卷列表</span>
            <div style="display: flex; gap: 10px;">
              <el-button type="success" plain @click="router.push('/question-bank')">
                📚 管理题库中心
              </el-button>
              <el-button type="primary" @click="goBuilder">
                + 创建新问卷
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="surveys"
          style="width: 100%"
          v-loading="loading"
          empty-text="暂无问卷，快去创建一份吧！"
        >
          <el-table-column prop="title" label="问卷标题" min-width="200" />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'info'">
                {{ scope.row.is_active ? "已发布" : "未发布" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ new Date(scope.row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="截止时间" min-width="160">
            <template #default="scope">
              <template v-if="scope.row.deadline">
                <span :style="{ color: new Date(scope.row.deadline) < new Date() ? '#F56C6C' : '#606266' }">
                  {{ new Date(scope.row.deadline).toLocaleString() }}
                  <span v-if="new Date(scope.row.deadline) < new Date()" style="font-size: 12px;">(已过期)</span>
                </span>
              </template>
              <span v-else style="color: #909399;">永久有效</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="400" fixed="right">
            <template #default="scope">
              <div class="action-buttons">
                <el-button
                  size="small"
                  :type="scope.row.is_active ? 'warning' : 'success'"
                  @click="togglePublish(scope.row)"
                >
                  {{ scope.row.is_active ? "关闭问卷" : "发布问卷" }}
                </el-button>

                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="openDeadlineDialog(scope.row)"
                >
                  设置截止时间
                </el-button>

                <el-button
                  size="small"
                  type="info"
                  plain
                  @click="router.push(`/stats/${scope.row.id}`)"
                >
                  查看统计
                </el-button>

                <el-button
                  size="small"
                  type="primary"
                  :disabled="!scope.row.is_active"
                  @click="openSurvey(scope.row.id)"
                >
                  填写链接
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-dialog
        v-model="deadlineDialogVisible"
        title="设置问卷截止时间"
        width="400px"
      >
        <el-date-picker
          v-model="selectedDeadline"
          type="datetime"
          placeholder="选择截止日期和时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DDTHH:mm:ssZ"
          style="width: 100%"
        />
        <template #footer>
          <el-button @click="deadlineDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDeadline">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import request from "../utils/request"; // 引入我们封装好的 Axios

const router = useRouter();
const username = ref(localStorage.getItem("username") || "用户");
const surveys = ref([]);
const loading = ref(false);

const deadlineDialogVisible = ref(false);
const selectedDeadline = ref("");
const currentOperatingSurveyId = ref(null);

// 弹窗控制逻辑
const openDeadlineDialog = (row) => {
  currentOperatingSurveyId.value = row.id;
  selectedDeadline.value = row.deadline || "";
  deadlineDialogVisible.value = true;
};

const saveDeadline = async () => {
  try {
    await request.put(`/api/surveys/${currentOperatingSurveyId.value}/status`, {
      deadline: selectedDeadline.value || null,
    });
    ElMessage.success("截止时间设置成功！");
    deadlineDialogVisible.value = false;
    fetchSurveys();
  } catch (e) {
    ElMessage.error("设置失败");
  }
};

// 页面加载时（onMounted）自动获取问卷列表
onMounted(() => {
  fetchSurveys();
});

// 向后端请求当前用户的问卷列表
const fetchSurveys = async () => {
  loading.value = true;
  try {
    const data = await request.get("/api/surveys");
    surveys.value = data; // 把后端返回的数组赋值给表格数据源
  } catch (error) {
    ElMessage.error("获取问卷列表失败");
  } finally {
    loading.value = false;
  }
};

// 切换问卷的发布/关闭状态
const togglePublish = async (row) => {
  try {
    await request.put(`/api/surveys/${row.id}/status`, {
      is_active: !row.is_active,
    });
    ElMessage.success(row.is_active ? "已关闭问卷" : "发布成功！");
    fetchSurveys(); // 更新成功后重新拉取列表刷新状态
  } catch (error) {
    ElMessage.error("状态更新失败");
  }
};

// 跳转到填写页
const openSurvey = (id) => {
  // 会在新标签页打开 /survey/:id 路由
  window.open(`/survey/${id}`, "_blank");
};

const handleLogout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  router.push("/login");
};

const goBuilder = () => {
  router.push("/builder");
};
</script>

<style scoped>
.dashboard-layout {
  min-height: 100vh;
  background-color: #f5f7fa;
}
.top-menu {
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.logo {
  font-size: 20px;
  font-weight: bold;
  line-height: 58px;
  color: #409eff;
  margin-right: 20px;
}
.flex-grow {
  flex-grow: 1;
}
.welcome-text {
  font-weight: 500;
  color: #606266;
}
.main-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
/* 在最后面加上这个 */
.action-buttons {
  display: flex;
  gap: 8px; /* 按钮之间保持固定的 8px 间距 */
  flex-wrap: wrap; /* 空间不够时优雅地整体换行 */
}
/* 覆盖 Element Plus 按钮默认的左边距，完全由 gap 接管 */
.action-buttons .el-button {
  margin-left: 0 !important;
}
</style>
