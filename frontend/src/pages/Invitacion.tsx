import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import { aceptarInvitacion, consultarInvitacion } from '../lib/api';
import type { InvitacionInfo } from '../lib/authTypes';

export default function Invitacion() {
  const { token = '' } = useParams();
  const { usuario, registroInvitacion } = useAuth();
  const navigate = useNavigate();
  const [info, setInfo] = useState<InvitacionInfo | null>(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [empresa, setEmpresa] = useState('');
  const [ruc, setRuc] = useState('');
  const [region, setRegion] = useState('');
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    let vigente = true;
    consultarInvitacion(token)
      .then((datos) => { if (vigente) { setInfo(datos); setEmpresa(datos.proveedor); } })
      .catch((err: unknown) => { if (vigente) setError(err instanceof Error ? err.message : 'Invitación no encontrada'); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [token]);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setEnviando(true);
    try {
      await registroInvitacion({ token, empresa: empresa.trim(), ruc: ruc || null,
        region: region.trim() || null, nombre: nombre.trim(), email: email.trim(), password });
      navigate('/', { replace: true });
    } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo registrar la cuenta.'); }
    finally { setEnviando(false); }
  }

  async function aceptarCuentaExistente() {
    const accessToken = sessionStorage.getItem('originlink_access_token');
    if (!accessToken) { setError('Primero debes iniciar sesión con tu cuenta de cooperativa.'); return; }
    setError(''); setEnviando(true);
    try { await aceptarInvitacion(token, accessToken); navigate('/', { replace: true }); }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo aceptar la invitación.'); }
    finally { setEnviando(false); }
  }

  const campo = 'w-full rounded-lg border border-stone-300 p-3';
  return <main className='mx-auto max-w-lg px-6 py-12'>
    <h1 className='text-3xl font-semibold'>Invitación a Origin Link</h1>
    {cargando && <p className='mt-6'>Consultando invitación…</p>}
    {info && <p className='mt-4'>La tostadora <strong>{info.tostador}</strong> invitó a <strong>{info.proveedor}</strong>.</p>}
    {info && !info.vigente && <p role='alert' className='mt-4 text-red-700'>La invitación ha vencido o ya fue utilizada.</p>}
    {error && <p role='alert' className='mt-4 text-red-700'>{error}</p>}
    {info?.vigente && usuario?.organizacion.tipo === 'PROVEEDOR' &&
      <button className='mt-6 rounded-lg bg-amber-800 px-5 py-3 font-medium text-white' disabled={enviando}
        onClick={aceptarCuentaExistente}>Aceptar invitación con mi cuenta</button>}
    {info?.vigente && usuario?.organizacion.tipo === 'TOSTADOR' &&
      <p className='mt-4'>Esta invitación requiere una cuenta de cooperativa. Cierra sesión para registrarla.</p>}
    {info?.vigente && !usuario && <form onSubmit={submit} className='mt-8 space-y-4'>
      <label htmlFor='empresa' className='block'>Nombre de la cooperativa</label>
      <input id='empresa' className={campo} required minLength={2} maxLength={150} value={empresa} onChange={e=>setEmpresa(e.target.value)} />
      <label htmlFor='ruc' className='block'>RUC (opcional)</label>
      <input id='ruc' className={campo} inputMode='numeric' pattern='[0-9]{11}' value={ruc} onChange={e=>setRuc(e.target.value)} />
      <label htmlFor='region' className='block'>Región (opcional)</label>
      <input id='region' className={campo} maxLength={100} value={region} onChange={e=>setRegion(e.target.value)} />
      <label htmlFor='nombre' className='block'>Nombre del responsable</label>
      <input id='nombre' className={campo} required minLength={2} maxLength={120} value={nombre} onChange={e=>setNombre(e.target.value)} />
      <label htmlFor='email' className='block'>Correo electrónico</label>
      <input id='email' className={campo} required type='email' autoComplete='email' value={email} onChange={e=>setEmail(e.target.value)} />
      <label htmlFor='password' className='block'>Contraseña (mínimo 8 caracteres)</label>
      <input id='password' className={campo} required type='password' minLength={8} maxLength={128} autoComplete='new-password' value={password} onChange={e=>setPassword(e.target.value)} />
      <button type='submit' disabled={enviando} className='w-full rounded-lg bg-amber-800 px-5 py-3 font-medium text-white disabled:opacity-60'>
        {enviando ? 'Registrando…' : 'Registrarme y aceptar invitación'}
      </button>
    </form>}
  </main>;
}
