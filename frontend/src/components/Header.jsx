import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function Header({ title }) {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-sb-card border-b border-sb-border sticky top-0 z-40">
      <h1 className="text-base font-semibold text-sb-on-surface">{title}</h1>

      <div className="flex items-center gap-3">
        {/* MQTT live indicator */}
        <div className="hidden sm:flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sb-primary opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-sb-primary" />
          </span>
          <span className="text-xs text-sb-outline">Sistema online</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-full text-sb-outline hover:text-sb-on-surface hover:bg-sb-card-high transition-colors">
          <span className="material-symbols-outlined text-[20px]">notifications</span>
        </button>

        {/* User avatar */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-sb-border">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-sb-primary-btn text-white text-sm font-bold select-none">
            {user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-sb-on-surface leading-tight truncate max-w-[140px]">{user?.email || 'Admin'}</p>
            <p className="text-xs text-sb-outline">Administrador</p>
          </div>
          <button
            onClick={handleLogout}
            className="ml-1 p-1.5 rounded-lg text-sb-outline hover:text-sb-on-surface hover:bg-sb-card-high transition-colors"
            title="Sair"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
          </button>
        </div>
      </div>
    </header>
  )
}
