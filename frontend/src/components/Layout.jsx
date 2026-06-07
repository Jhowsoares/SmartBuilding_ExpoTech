import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/rooms': 'Salas & Dispositivos',
  '/alerts': 'Central de Alertas',
  '/reports': 'Relatórios',
  '/predictions': 'Predições de Consumo',
  '/system': 'Status do Sistema',
  '/users': 'Gerenciamento de Usuários',
  '/devices/new': 'Novo Dispositivo',
}

export default function Layout() {
  const location = useLocation()
  const pathname = location.pathname
  const title = pageTitles[pathname] || (pathname.startsWith('/rooms/') ? 'Detalhes da Sala' : 'SmartBuilding')

  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Fecha o drawer ao navegar (mobile/tablet)
  useEffect(() => {
    setSidebarOpen(false)
  }, [pathname])

  return (
    <div className="flex min-h-screen bg-sb-bg">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
