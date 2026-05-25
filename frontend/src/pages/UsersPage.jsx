import { useState, useEffect, useCallback } from 'react'
import { getUsers, createUser, updateUser, deleteUser } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { format } from 'date-fns'

const ROLE_LABELS = { admin: 'Administrador', operador: 'Operador', viewer: 'Visualizador' }
const ROLE_COLORS = {
  admin: 'text-red-400 bg-red-900/30 border-red-700',
  operador: 'text-yellow-400 bg-yellow-900/30 border-yellow-700',
  viewer: 'text-blue-400 bg-blue-900/30 border-blue-700',
}

function Avatar({ name, email }) {
  const initials = (name || email || 'U').split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase()
  const colors = ['bg-blue-600', 'bg-purple-600', 'bg-green-600', 'bg-red-600', 'bg-yellow-600']
  const colorIdx = (name || '').length % colors.length
  return (
    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 ${colors[colorIdx]}`}>
      {initials}
    </div>
  )
}

function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t) }, [onClose])
  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium
      ${type === 'success' ? 'bg-green-800 text-green-100 border border-green-600' : 'bg-red-800 text-red-100 border border-red-600'}`}>
      {message}
    </div>
  )
}

function InviteModal({ onClose, onSave }) {
  const [form, setForm] = useState({ name: '', email: '', role: 'viewer', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.email || !form.password) { setError('E-mail e senha são obrigatórios.'); return }
    setLoading(true)
    try {
      await createUser(form)
      onSave()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar usuário.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md p-6 m-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-white font-semibold text-lg">Convidar Usuário</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-gray-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1">Nome</label>
            <input className="input-field" placeholder="Nome completo" value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1">E-mail *</label>
            <input className="input-field" type="email" placeholder="usuario@empresa.com" value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} required />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1">Senha *</label>
            <input className="input-field" type="password" placeholder="••••••••" value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1">Função</label>
            <select className="input-field" value={form.role}
              onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}>
              <option value="viewer">Visualizador</option>
              <option value="operador">Operador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 btn-secondary">Cancelar</button>
            <button type="submit" disabled={loading} className="flex-1 btn-primary disabled:opacity-50">
              {loading ? '...' : 'Criar Usuário'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function EditRoleModal({ user, onClose, onSave }) {
  const [role, setRole] = useState(user.role)
  const [loading, setLoading] = useState(false)

  const handleSave = async () => {
    setLoading(true)
    try {
      await updateUser(user.id, { role })
      onSave()
      onClose()
    } catch {
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-sm p-6 m-4">
        <h3 className="text-white font-semibold text-lg mb-4">Editar Função</h3>
        <p className="text-gray-400 text-sm mb-4">{user.email}</p>
        <select className="input-field mb-4" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="viewer">Visualizador</option>
          <option value="operador">Operador</option>
          <option value="admin">Administrador</option>
        </select>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 btn-secondary">Cancelar</button>
          <button onClick={handleSave} disabled={loading} className="flex-1 btn-primary disabled:opacity-50">
            {loading ? '...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function UsersPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showInvite, setShowInvite] = useState(false)
  const [editUser, setEditUser] = useState(null)
  const [toast, setToast] = useState(null)
  const [page, setPage] = useState(1)
  const [meta, setMeta] = useState({ total: 0, total_pages: 1 })

  const showToast = (message, type = 'success') => setToast({ message, type })

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getUsers({ page, size: 20 })
      const arr = Array.isArray(res.data) ? res.data : res.data?.data || []
      setUsers(arr)
      if (res.data?.meta) setMeta(res.data.meta)
    } catch {
      setUsers([])
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  const handleDelete = async (id) => {
    if (!confirm('Desativar este usuário?')) return
    try {
      await deleteUser(id)
      showToast('Usuário removido.')
      fetchUsers()
    } catch {
      showToast('Erro ao remover usuário.', 'error')
    }
  }

  const filtered = users.filter((u) =>
    (u.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (u.email || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      {showInvite && <InviteModal onClose={() => setShowInvite(false)} onSave={() => { fetchUsers(); showToast('Usuário criado com sucesso!') }} />}
      {editUser && <EditRoleModal user={editUser} onClose={() => setEditUser(null)} onSave={() => { fetchUsers(); showToast('Função atualizada.') }} />}

      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input className="input-field pl-9" placeholder="Buscar por nome ou email..."
            value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <span className="text-xs text-gray-500 ml-auto">
          {meta.total} usuário{meta.total !== 1 ? 's' : ''} no total
        </span>
        <button onClick={() => setShowInvite(true)} className="btn-primary flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Convidar Usuário
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" /></div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-500">
            <svg className="w-14 h-14 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <p className="font-medium">Nenhum usuário encontrado</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700 bg-gray-800/50">
                  {['Usuário', 'Função', 'Status', 'Último Login', 'Ações'].map((h) => (
                    <th key={h} className="table-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filtered.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-700/30 transition-colors">
                    <td className="table-cell">
                      <div className="flex items-center gap-3">
                        <Avatar name={u.name} email={u.email} />
                        <div>
                          <p className="text-white text-sm font-medium">{u.name || u.email}</p>
                          <p className="text-gray-400 text-xs">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${ROLE_COLORS[u.role] || ROLE_COLORS.viewer}`}>
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className={`flex items-center gap-1.5 text-xs font-medium w-fit px-2.5 py-1 rounded-full
                        ${u.is_active !== false ? 'text-green-400 bg-green-900/30' : 'text-gray-500 bg-gray-800'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${u.is_active !== false ? 'bg-green-400' : 'bg-gray-500'}`} />
                        {u.is_active !== false ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="table-cell text-gray-400 text-sm">
                      {u.last_login_at ? format(new Date(u.last_login_at), 'dd/MM/yy HH:mm') : 'Nunca'}
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <button onClick={() => setEditUser(u)}
                          className="text-xs px-3 py-1 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors">
                          Editar Função
                        </button>
                        <button onClick={() => handleDelete(u.id)}
                          className="text-xs px-3 py-1 rounded-lg bg-red-900/40 text-red-400 hover:bg-red-900/70 transition-colors">
                          Remover
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {meta.total_pages > 1 && (
          <div className="px-6 py-4 border-t border-gray-700 flex items-center justify-between">
            <p className="text-xs text-gray-500">
              Mostrando {(page - 1) * 20 + 1}–{Math.min(page * 20, meta.total)} de {meta.total}
            </p>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                className="btn-secondary text-xs py-1 px-3 disabled:opacity-40">Anterior</button>
              <span className="text-gray-400 text-xs">Pág. {page} de {meta.total_pages}</span>
              <button onClick={() => setPage((p) => Math.min(meta.total_pages, p + 1))} disabled={page === meta.total_pages}
                className="btn-secondary text-xs py-1 px-3 disabled:opacity-40">Próxima</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
