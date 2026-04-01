<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="title">📋 问卷系统后台</h2>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form
            :model="loginForm"
            :rules="rules"
            ref="loginFormRef"
            label-width="0"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-button
              type="primary"
              class="submit-btn"
              :loading="loading"
              @click="handleLogin"
              >登 录</el-button
            >
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form
            :model="regForm"
            :rules="rules"
            ref="regFormRef"
            label-width="0"
          >
            <el-form-item prop="username">
              <el-input
                v-model="regForm.username"
                placeholder="设置用户名 (至少3位)"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="regForm.password"
                type="password"
                placeholder="设置密码 (至少6位)"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-button
              type="success"
              class="submit-btn"
              :loading="loading"
              @click="handleRegister"
              >注 册</el-button
            >
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";
import request from "../utils/request";

const router = useRouter();
const activeTab = ref("login");
const loading = ref(false);

const loginFormRef = ref(null);
const regFormRef = ref(null);

const loginForm = reactive({ username: "", password: "" });
const regForm = reactive({ username: "", password: "" });

// 表单校验规则
const rules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, message: "用户名长度至少为 3", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度至少为 6", trigger: "blur" },
  ],
};

// 处理登录逻辑 (需使用 FormData 适配后端的 OAuth2)
const handleLogin = async () => {
  if (!loginFormRef.value) return;
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const formData = new FormData();
        formData.append("username", loginForm.username);
        formData.append("password", loginForm.password);

        const res = await request.post("/api/auth/login", formData);
        localStorage.setItem("token", res.access_token);
        localStorage.setItem("username", loginForm.username);
        ElMessage.success("登录成功！");
        router.push("/dashboard");
      } catch (error) {
        ElMessage.error(
          error.response?.data?.detail || "登录失败，请检查账号密码",
        );
      } finally {
        loading.value = false;
      }
    }
  });
};

// 处理注册逻辑 (发送 JSON)
const handleRegister = async () => {
  if (!regFormRef.value) return;
  await regFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await request.post("/api/auth/register", {
          username: regForm.username,
          password: regForm.password,
        });
        ElMessage.success("注册成功，请登录！");
        // 注册成功后清空表单并切回登录 Tab
        regForm.username = "";
        regForm.password = "";
        activeTab.value = "login";
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || "注册失败");
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
.login-card {
  width: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}
.submit-btn {
  width: 100%;
  margin-top: 10px;
}
</style>
