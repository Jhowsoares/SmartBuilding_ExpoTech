import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info?.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-sb-outline">
          <span className="material-symbols-outlined text-[56px] opacity-30 mb-4">error</span>
          <p className="text-base font-medium text-sb-on-surface mb-1">Algo deu errado nesta página</p>
          <p className="text-sm opacity-70 mb-6 max-w-sm text-center">
            {this.state.error?.message || 'Erro inesperado. Tente recarregar.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="btn-primary"
          >
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
