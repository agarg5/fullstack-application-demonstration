import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import OrdersPage from './pages/OrdersPage'
import DriversPage from './pages/DriversPage'
import TrackingPage from './pages/TrackingPage'
import UploadPage from './pages/UploadPage'
import { cn } from './lib/utils'

function Navigation() {
  const location = useLocation()
  
  const navItems = [
    { path: '/orders', label: 'Orders' },
    { path: '/drivers', label: 'Drivers' },
    { path: '/tracking', label: 'Tracking' },
    { path: '/upload', label: 'Upload CSV' },
  ]

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center space-x-8">
          <Link to="/" className="text-xl font-bold">
            TMS
          </Link>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "text-sm font-medium transition-colors hover:text-primary",
                location.pathname === item.path
                  ? "text-primary border-b-2 border-primary"
                  : "text-muted-foreground"
              )}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<OrdersPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/drivers" element={<DriversPage />} />
            <Route path="/tracking" element={<TrackingPage />} />
            <Route path="/upload" element={<UploadPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App

