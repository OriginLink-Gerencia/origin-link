import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';

export default function ProtectedRoute() {
  const { usuario, cargando } = useAuth();
  const location = useLocation();
  if (cargando) return <p role='status'>Validando sesión…</p>;
  return usuario ? <Outlet /> : <Navigate to='/login' replace state={{ from: location.pathname }} />;
}
