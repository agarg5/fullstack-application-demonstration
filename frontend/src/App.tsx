import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useLocation,
  Navigate,
} from "react-router-dom";
import OrdersPage from "./pages/OrdersPage";
import DriversPage from "./pages/DriversPage";
import TrackingPage from "./pages/TrackingPage";
import UploadPage from "./pages/UploadPage";
import LoginPage from "./pages/LoginPage";
import { cn } from "./lib/utils";
import { getAuth, clearAuth } from "./api/client";

function Navigation() {
  const location = useLocation();
  const auth = getAuth();

  const navItems = [
    { path: "/orders", label: "Orders" },
    { path: "/drivers", label: "Drivers" },
    { path: "/tracking", label: "Tracking" },
    { path: "/upload", label: "Upload CSV" },
  ];

  if (!auth) {
    return null;
  }

  return (
    <nav className="border-b bg-background">
      <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 sm:h-16 sm:flex-nowrap">
          <Link to="/" className="text-xl font-bold">
            TMS
          </Link>

          <span className="text-sm text-muted-foreground flex-1">
            Logged in as{" "}
            <span className="font-medium">{auth.merchant.name}</span>
          </span>

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

          <button
            className="text-sm text-muted-foreground hover:text-destructive"
            onClick={() => {
              clearAuth();
              window.location.href = "/login";
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

function ProtectedRoute({ children }: { children: React.ReactElement }) {
  const auth = getAuth();
  const location = useLocation();

  if (!auth) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <>
                <Navigation />
                <main className="w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:max-w-6xl">
                  <Routes>
                    <Route
                      path="/"
                      element={
                        <ProtectedRoute>
                          <OrdersPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/orders"
                      element={
                        <ProtectedRoute>
                          <OrdersPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/drivers"
                      element={
                        <ProtectedRoute>
                          <DriversPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/tracking"
                      element={
                        <ProtectedRoute>
                          <TrackingPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/upload"
                      element={
                        <ProtectedRoute>
                          <UploadPage />
                        </ProtectedRoute>
                      }
                    />
                  </Routes>
                </main>
              </>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
