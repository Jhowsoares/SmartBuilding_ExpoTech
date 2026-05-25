import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import RoomsPage from './pages/RoomsPage'
import RoomDetailPage from './pages/RoomDetailPage'
import AlertsPage from './pages/AlertsPage'
import ReportsPage from './pages/ReportsPage'
import PredictionsPage from './pages/PredictionsPage'
import SystemStatusPage from './pages/SystemStatusPage'
import UsersPage from './pages/UsersPage'
import AddDevicePage from './pages/AddDevicePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"   element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
          <Route path="rooms"       element={<ErrorBoundary><RoomsPage /></ErrorBoundary>} />
          <Route path="rooms/:id"   element={<ErrorBoundary><RoomDetailPage /></ErrorBoundary>} />
          <Route path="devices/new" element={<ErrorBoundary><AddDevicePage /></ErrorBoundary>} />
          <Route path="alerts"      element={<ErrorBoundary><AlertsPage /></ErrorBoundary>} />
          <Route path="reports"     element={<ErrorBoundary><ReportsPage /></ErrorBoundary>} />
          <Route path="predictions" element={<ErrorBoundary><PredictionsPage /></ErrorBoundary>} />
          <Route path="system"      element={<ErrorBoundary><SystemStatusPage /></ErrorBoundary>} />
          <Route path="users"       element={<ErrorBoundary><UsersPage /></ErrorBoundary>} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
