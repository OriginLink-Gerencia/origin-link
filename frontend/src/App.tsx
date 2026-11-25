import { Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleRoute from './components/RoleRoute';
import EnConstruccion from './pages/EnConstruccion';
import Inicio from './pages/Inicio';
import Invitacion from './pages/Invitacion';
import Login from './pages/Login';
import Proveedores from './pages/Proveedores';
import Vinculos from './pages/Vinculos';
import Registro from './pages/Registro';

export default function App() {
  return <AuthProvider><Routes>
    <Route path='/login' element={<Login />} />
    <Route path='/registro' element={<Registro />} />
    <Route path='/invitacion/:token' element={<Invitacion />} />
    <Route path='/invitaciones/:token' element={<Invitacion />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
        <Route path='lotes' element={<EnConstruccion titulo='Lotes' historia='épica colaborativa' />} />
        <Route element={<RoleRoute tipo='TOSTADOR' />}>
          <Route path='proveedores' element={<Proveedores />} />
          <Route path='compras' element={<EnConstruccion titulo='Compras y recepciones' historia='épica de compras' />} />
          <Route path='inventario' element={<EnConstruccion titulo='Inventario' historia='épica de inventario' />} />
          <Route path='pronostico' element={<EnConstruccion titulo='Pronóstico y recomendaciones' historia='épica de pronóstico' />} />
        </Route>
        <Route element={<RoleRoute tipo='PROVEEDOR' />}>
          <Route path='vinculos' element={<Vinculos />} />
        </Route>
      </Route>
    </Route>
    <Route path='*' element={<Login />} />
  </Routes></AuthProvider>;
}
