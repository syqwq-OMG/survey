import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        redirect: '/dashboard'
    },
    {
        path: '/login',
        name: 'Login',
        // 稍后我们将创建这个组件
        component: () => import('../views/Login.vue')
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { requiresAuth: true } // 标记需要登录才能访问
    },
    {
        path: '/survey/:id',
        name: 'SurveyFill',
        component: () => import('../views/SurveyFill.vue')
    },
    // src/router/index.js (在 routes 数组中增加这一段)
    {
        path: '/builder',
        name: 'SurveyBuilder',
        component: () => import('../views/SurveyBuilder.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/stats/:id',
        name: 'SurveyStats',
        component: () => import('../views/SurveyStats.vue'),
        meta: { requiresAuth: true } // 只有登录用户（创建者）能看
    },
    {
        path: '/question-bank',
        name: 'QuestionBank',
        component: () => import('../views/QuestionBank.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/stats/question/:id',
        name: 'QuestionGlobalStats',
        component: () => import('../views/QuestionGlobalStats.vue'),
        meta: { requiresAuth: true }
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫：拦截未登录用户的访问
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.requiresAuth && !token) {
        next('/login')
    } else {
        next()
    }
})

export default router