import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import type { TipoOrganizacion } from '../lib/authTypes';

/** Control de navegación UX. La autorización real debe estar en la API (HU-04). */
export default function RoleRoute({ tipo }: { tipo: TipoOrganizacion }) {
  const { usuario } = useAuth();
  if (usuario?.organizacion.tipo !== tipo) return <Navigate to='/' replace />;
  return <Outlet />;
}
