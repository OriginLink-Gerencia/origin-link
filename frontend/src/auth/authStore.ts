import { createContext } from 'react';
import type { LoginIn, RegistroPorInvitacionIn, RegistroTostadorIn, Usuario } from '../lib/authTypes';

export type AuthState = {
  usuario: Usuario | null;
  cargando: boolean;
  login: (datos: LoginIn) => Promise<void>;
  registro: (datos: RegistroTostadorIn) => Promise<void>;
  registroInvitacion: (datos: RegistroPorInvitacionIn) => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthState | null>(null);
