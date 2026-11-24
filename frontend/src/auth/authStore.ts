import { createContext } from 'react';
import type { LoginIn, RegistroTostadorIn, Usuario } from '../lib/authTypes';

export type AuthState = {
  usuario: Usuario | null;
  cargando: boolean;
  login: (datos: LoginIn) => Promise<void>;
  registro: (datos: RegistroTostadorIn) => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthState | null>(null);
