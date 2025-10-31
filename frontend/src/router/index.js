import { createRouter, createWebHistory } from 'vue-router';

const TabRoute = { template: '<div />' };

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'dashboard' } },
    { path: '/dashboard', name: 'dashboard', component: TabRoute },
    { path: '/forecast', name: 'forecast', component: TabRoute },
    { path: '/advanced', name: 'advanced', component: TabRoute },
    { path: '/quality', name: 'quality', component: TabRoute },
    { path: '/analysis', name: 'analysis', component: TabRoute },
    { path: '/models', name: 'models', component: TabRoute },
  ],
  scrollBehavior: () => ({ top: 0 }),
});
