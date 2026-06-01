import { createRouter, createWebHistory } from 'vue-router'

import BasicLayout from '@/layouts/BasicLayout.vue'
import HomePage from '@/pages/HomePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: BasicLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomePage,
        },
        {
          path: 'about',
          name: 'about',
          component: () => import('@/pages/AboutPage.vue'),
        },
        {
          path: 'vip',
          name: 'vip',
          component: () => import('@/pages/VipPage.vue'),
        },
        {
          path: 'admin/userManage',
          name: 'user-manage',
          component: () => import('@/pages/admin/UserManagePage.vue'),
        },
        {
          path: 'admin/statistics',
          name: 'admin-statistics',
          component: () => import('@/pages/admin/StatisticsPage.vue'),
        },
        {
          path: 'passage/create',
          name: 'passage-create',
          meta: { requiresAuth: true },
          component: () => import('@/pages/passage/PassageCreatePage.vue'),
        },
        {
          path: 'passage/my',
          name: 'passage-my',
          meta: { requiresAuth: true },
          component: () => import('@/pages/passage/PassageListPage.vue'),
        },
        {
          path: 'article/create',
          name: 'article-create',
          meta: { requiresAuth: true, fullBleed: true },
          component: () => import('@/pages/article/ArticleCreatePage.vue'),
        },
        {
          path: 'article/workspace',
          redirect: '/article/create',
        },
        {
          path: 'article/list',
          name: 'article-list',
          meta: { requiresAuth: true },
          component: () => import('@/pages/article/ArticleListPage.vue'),
        },
        {
          path: 'article/:taskId',
          name: 'article-detail',
          meta: { requiresAuth: true },
          component: () => import('@/pages/article/ArticleDetailPage.vue'),
        },
      ],
    },
    {
      path: '/user/login',
      name: 'user-login',
      component: () => import('@/pages/user/UserLoginPage.vue'),
    },
    {
      path: '/user/register',
      name: 'user-register',
      component: () => import('@/pages/user/UserRegisterPage.vue'),
    },
  ],
})

export default router
