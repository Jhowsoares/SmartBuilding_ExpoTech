import { NavLink } from 'react-router-dom'
import useAuthStore from '../store/authStore'

const nav = [
  {
    section: 'Principal',
    items: [
      {
        to: '/dashboard',
        label: 'Dashboard',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        ),
      },
      {
        to: '/rooms',
        label: 'Salas',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        ),
      },
      {
        to: '/devices/new',
        label: 'Dispositivos',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        ),
      },
    ],
  },
  {
    section: 'Dados',
    items: [
      {
        to: '/alerts',
        label: 'Alertas',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        ),
        badge: true,
      },
      {
        to: '/reports',
        label: 'Relatórios',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
      },
      {
        to: '/predictions',
        label: 'Predições',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        ),
      },
    ],
  },
  {
    section: 'Sistema',
    adminOnly: false,
    items: [
      {
        to: '/system',
        label: 'Status do Sistema',
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
          </svg>
        ),
      },
      {
        to: '/users',
        label: 'Usuários',
        adminOnly: true,
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
      },
    ],
  },
]

export default function Sidebar() {
  const { user, role, logout } = useAuthStore()
  const isAdmin = role === 'admin'
  const initials = (user?.email || 'U')[0].toUpperCase()
  const roleLabel = role === 'admin' ? 'Administrador' : role === 'operador' ? 'Operador' : 'Visualizador'

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col bg-sb-card border-r border-sb-border min-h-screen">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-sb-border">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-sb-primary-btn">
          <span className="material-symbols-outlined text-white text-[20px]">apartment</span>
        </div>
        <div>
          <p className="text-sb-on-surface font-bold text-sm leading-tight">SmartBuilding</p>
          <p className="text-sb-outline text-xs tracking-widest uppercase">GESTÃO IOT</p>
        </div>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {nav.map(({ section, items }) => {
          const visibleItems = items.filter((item) => !item.adminOnly || isAdmin)
          if (visibleItems.length === 0) return null
          return (
            <div key={section}>
              <p className="px-3 mb-1.5 text-xs font-semibold text-sb-outline uppercase tracking-wider">{section}</p>
              <div className="space-y-0.5">
                {visibleItems.map(({ to, label, icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/dashboard'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                        isActive
                          ? 'bg-sb-secondary-c text-sb-secondary'
                          : 'text-sb-outline hover:bg-sb-card-high hover:text-sb-on-surface'
                      }`
                    }
                  >
                    {icon}
                    {label}
                  </NavLink>
                ))}
              </div>
            </div>
          )
        })}
      </nav>

      {/* User footer */}
      <div className="px-4 py-4 border-t border-sb-border">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-full bg-sb-primary-btn text-white text-sm font-bold flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sb-on-surface text-sm font-medium truncate">{user?.email || 'Admin'}</p>
            <p className="text-sb-outline text-xs">{roleLabel}</p>
          </div>
          <button
            onClick={() => { logout(); window.location.href = '/login' }}
            className="p-1.5 rounded-lg text-sb-outline hover:text-sb-on-surface hover:bg-sb-card-high transition-colors flex-shrink-0"
            title="Sair"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
          </button>
        </div>
      </div>
    </aside>
  )
}
