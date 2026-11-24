import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';

const enlacesTostador = [
  { to: '/', label: 'Inicio' },
  { to: '/proveedores', label: 'Proveedores' },
  { to: '/lotes', label: 'Lotes' },
  { to: '/compras', label: 'Compras' },
  { to: '/inventario', label: 'Inventario' },
  { to: '/pronostico', label: 'Pronóstico' },
];
const enlacesCooperativa = [
  { to: '/', label: 'Inicio' },
  { to: '/lotes', label: 'Lotes' },
];

export default function Layout() {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();
  const enlaces = usuario?.organizacion.tipo === 'PROVEEDOR' ? enlacesCooperativa : enlacesTostador;
  const salir = () => { logout(); navigate('/login', { replace: true }); };
  return <div className='min-h-screen'>
    <header className='border-b border-stone-200 bg-white'>
      <nav aria-label='Navegación principal' className='mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-6 py-4'>
        <span className='text-lg font-semibold text-amber-800'>Origin Link</span>
        {enlaces.map((e) => <NavLink key={e.to} to={e.to} end={e.to === '/'}
          className={({ isActive }) => isActive ? 'font-medium text-amber-800' : 'text-stone-600 hover:text-stone-900'}>{e.label}</NavLink>)}
        <span className='ml-auto text-sm text-stone-600'>{usuario?.nombre}</span>
        <button onClick={salir} className='rounded-lg border border-stone-300 px-3 py-2 text-sm'>Cerrar sesión</button>
      </nav>
    </header>
    <main className='mx-auto max-w-6xl px-6 py-8'><Outlet /></main>
  </div>;
}
