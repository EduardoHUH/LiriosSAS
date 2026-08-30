import { useEffect, useState } from 'react'
import { apiClient } from '../api/client'

type BackendStatus = 'checking' | 'online' | 'offline'

const STATUS_LABELS: Record<BackendStatus, string> = {
  checking: 'verificando...',
  online: 'en línea',
  offline: 'sin conexión',
}

export default function Home() {
  const [status, setStatus] = useState<BackendStatus>('checking')

  useEffect(() => {
    apiClient
      .get('/health/')
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <main className="container py-5">
      <h1>Lirios</h1>
      <p>Maquillaje, uñas y pestañas.</p>
      <p>
        Estado del servidor: <strong>{STATUS_LABELS[status]}</strong>
      </p>
    </main>
  )
}
