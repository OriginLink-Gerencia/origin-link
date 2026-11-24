import { Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleRoute from './components/RoleRoute';
import EnConstruccion from './pages/EnConstruccion';
import Inicio from './pages/Inicio';
import Login from './pages/Login';
import Registro from './pages/Registro';

export default function App() {
  return <AuthProvider><Routes>
    <Route path='/login' element={<Login />} />
    <Route path='/registro' element={<Registro />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
        <Route path='lotes' element={<EnConstruccion titulo='Lotes' historia='épica colaborativa' />} />
        <Route element={<RoleRoute tipo='TOSTADOR' />}>
          <Route path='proveedores' element={<EnConstruccion titulo='Proveedores' historia='épica de relaciones' />} />
          <Route path='compras' element={<EnConstruccion titulo='Compras y recepciones' historia='épica de compras' />} />
          <Route path='inventario' element={<EnConstruccion titulo='Inventario' historia='épica de inventario' />} />
          <Route path='pronostico' element={<EnConstruccion titulo='Pronóstico y recomendaciones' historia='épica de pronóstico' />} />
        </Route>
      </Route>
    </Route>
    <Route path='*' element={<Login />} />
  </Routes></AuthProvider>;
}
