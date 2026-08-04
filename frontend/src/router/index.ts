import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'
import CompaniesPage from '../pages/CompaniesPage.vue'
import CustomersPage from '../pages/CustomersPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import FinancePage from '../pages/FinancePage.vue'
import HealthPage from '../pages/HealthPage.vue'
import HomePage from '../pages/HomePage.vue'
import InventoryPage from '../pages/InventoryPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import MaterialsPage from '../pages/MaterialsPage.vue'
import PurchasePage from '../pages/PurchasePage.vue'
import RolesPage from '../pages/RolesPage.vue'
import SalesPage from '../pages/SalesPage.vue'
import SuppliersPage from '../pages/SuppliersPage.vue'
import UsersPage from '../pages/UsersPage.vue'
import WarehousesPage from '../pages/WarehousesPage.vue'
import { getAccessToken } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
      meta: { public: true },
    },
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: HomePage },
        { path: 'health', name: 'health', component: HealthPage },
        {
          path: 'companies',
          name: 'companies',
          component: CompaniesPage,
          meta: { permission: 'org.company.read' },
        },
        {
          path: 'users',
          name: 'users',
          component: UsersPage,
          meta: { permission: 'org.user.read' },
        },
        {
          path: 'roles',
          name: 'roles',
          component: RolesPage,
          meta: { permission: 'org.role.read' },
        },
        {
          path: 'customers',
          name: 'customers',
          component: CustomersPage,
          meta: { permission: 'master.read' },
        },
        {
          path: 'suppliers',
          name: 'suppliers',
          component: SuppliersPage,
          meta: { permission: 'master.read' },
        },
        {
          path: 'materials',
          name: 'materials',
          component: MaterialsPage,
          meta: { permission: 'master.read' },
        },
        {
          path: 'warehouses',
          name: 'warehouses',
          component: WarehousesPage,
          meta: { permission: 'master.read' },
        },
        {
          path: 'inventory',
          name: 'inventory',
          component: InventoryPage,
          meta: { permission: 'inventory.read' },
        },
        {
          path: 'purchase',
          name: 'purchase',
          component: PurchasePage,
          meta: { permission: 'purchase.read' },
        },
        {
          path: 'sales',
          name: 'sales',
          component: SalesPage,
          meta: { permission: 'sales.read' },
        },
        {
          path: 'finance',
          name: 'finance',
          component: FinancePage,
          meta: { permission: 'finance.read' },
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardPage,
          meta: { permission: 'dashboard.read' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.bootstrapped.value) {
    await auth.bootstrap()
  }

  if (to.meta.public) {
    if (getAccessToken() && to.name === 'login') {
      return { path: '/' }
    }
    return true
  }

  if (!getAccessToken()) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const permission = to.meta.permission as string | undefined
  if (permission && !auth.hasPermission(permission)) {
    return { path: '/' }
  }

  return true
})

export default router
