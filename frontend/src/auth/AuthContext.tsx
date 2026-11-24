import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { AuthContext } from './authStore';
import { iniciarSesion, obtenerPerfil, registrarTostador } from '../lib/api';
import type { LoginIn, RegistroTostadorIn, TokenOut, Usuario } from '../lib/authTypes';

// sessionStorage: el token desaparece al cerrar la sesión/pestaña. No se usa localStorage persistente.
// Nota: la protección ante XSS depende también de evitar HTML no confiable y aplicar CSP en hosting.
const KEY = 'originlink_access_token';


export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  const logout = useCallback(() => {
    sessionStorage.removeItem(KEY);
    setUsuario(null);
  }, []);

  useEffect(() => {
    const token = sessionStorage.getItem(KEY);
    if (!token) { setCargando(false); return; }
    let vigente = true;
    obtenerPerfil(token)
      .then((perfil) => { if (vigente) setUsuario(perfil); })
      .catch(() => { if (vigente) logout(); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [logout]);

  const guardarSesion = (datos: TokenOut) => {
    sessionStorage.setItem(KEY, datos.access_token);
    setUsuario(datos.usuario);
  };

  const login = async (datos: LoginIn) => guardarSesion(await iniciarSesion(datos));
  const registro = async (datos: RegistroTostadorIn) => guardarSesion(await registrarTostador(datos));

  return <AuthContext.Provider value={{ usuario, cargando, login, registro, logout }}>{children}</AuthContext.Provider>;
}
