import { createContext, useContext } from "react";
import type {usePilot} from "./pilotSession";
export type Session = ReturnType<typeof usePilot> & { theme:boolean; toggleTheme:()=>void };
export const SessionContext = createContext<Session | null>(null);
export function useDemo() {
  const s = useContext(SessionContext);
  if (!s) throw new Error("Sesión no disponible");
  return s;
}
