import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/rooms': 'Salas & Dispositivos',
  '/alerts': 'Alertas',
  '/reports': 'Relatórios',
  '/predictions': 'Predições',
}

export default function Layout() {
  const location = useLocation()
  const title = pageTitles[location.pathname] || 'SmartBuilding'

  return (
    <div className="flex min-h-screen bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={title} />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
