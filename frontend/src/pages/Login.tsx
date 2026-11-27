import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';

export default function Login() {
  const { login, usuario } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);
  if (usuario) return <Navigate to='/' replace />;

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError(''); setEnviando(true);
    try {
      await login({ email, password });
      const origen = (location.state as { from?: string } | null)?.from;
      navigate(origen?.startsWith('/') && !origen.startsWith('//') ? origen : '/', { replace: true });
    } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión.'); }
    finally { setEnviando(false); }
  };

  return <main className='mx-auto max-w-md px-6 py-14'>
    <h1 className='text-3xl font-semibold text-stone-900'>Iniciar sesión</h1>
    <p className='mt-2 text-stone-600'>Accede a tu cuenta de Origin Link.</p>
    <form onSubmit={submit} className='mt-8 space-y-5'>
      <label className='block text-sm font-medium' htmlFor='login-email'>Correo electrónico</label>
      <input id='login-email' type='email' autoComplete='email' required value={email}
        onChange={e => setEmail(e.target.value)} className='w-full rounded-lg border border-stone-300 p-3' />
      <label className='block text-sm font-medium' htmlFor='login-password'>Contraseña</label>
      <input id='login-password' type='password' autoComplete='current-password' required value={password}
        onChange={e => setPassword(e.target.value)} className='w-full rounded-lg border border-stone-300 p-3' />
      {error && <p role='alert' className='text-sm text-red-700'>{error}</p>}
      <button type='submit' disabled={enviando} className='w-full rounded-lg bg-amber-800 px-5 py-3 font-medium text-white disabled:opacity-60'>
        {enviando ? 'Ingresando…' : 'Ingresar'}
      </button>
    </form>
    <p className='mt-6 text-sm'>¿Todavía no tienes cuenta? <Link className='font-medium text-amber-800 underline' to='/registro'>Registra tu tostadora</Link></p>
  </main>;
}
