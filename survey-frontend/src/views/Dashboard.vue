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
            <el-button type="primary" @click="goBuilder"> + 创建新问卷</el-button>
          </div>
        </template>
        
        <el-empty description="问卷列表加载中或暂无数据..." />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref(localStorage.getItem('username') || '用户')

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}

const goBuilder = () => {
  router.push('/builder')
}
</script>

<style scoped>
.dashboard-layout {
  min-height: 100vh;
  background-color: #f5f7fa;
}
.top-menu {
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.logo {
  font-size: 20px;
  font-weight: bold;
  line-height: 58px;
  color: #409EFF;
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
</style>