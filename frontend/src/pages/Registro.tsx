import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';

export default function Registro() {
  const { registro, usuario } = useAuth();
  const navigate = useNavigate();
  const [empresa, setEmpresa] = useState('');
  const [ruc, setRuc] = useState('');
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);
  if (usuario) return <Navigate to='/' replace />;

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError('');
    if (empresa.trim().length < 2 || nombre.trim().length < 2) {
      setError('El nombre de la empresa y del responsable requieren al menos 2 caracteres.'); return;
    }
    if (ruc && !/^\d{11}$/.test(ruc)) { setError('El RUC debe contener 11 dígitos.'); return; }
    if (password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return; }
    setEnviando(true);
    try {
      await registro({ empresa: empresa.trim(), ruc: ruc || null, nombre: nombre.trim(),
        email: email.trim(), password });
      navigate('/', { replace: true });
    } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo registrar la cuenta.'); }
    finally { setEnviando(false); }
  };

  const campo = 'w-full rounded-lg border border-stone-300 p-3';
  return <main className='mx-auto max-w-lg px-6 py-12'>
    <h1 className='text-3xl font-semibold'>Registrar tostadora</h1>
    <p className='mt-2 text-stone-600'>Crea una cuenta para gestionar tus proveedores de café verde.</p>
    <form onSubmit={submit} className='mt-8 space-y-4'>
      <label className='block' htmlFor='empresa'>Nombre de la empresa</label>
      <input id='empresa' className={campo} minLength={2} maxLength={150} required value={empresa} onChange={e=>setEmpresa(e.target.value)} />
      <label className='block' htmlFor='ruc'>RUC (opcional)</label>
      <input id='ruc' className={campo} inputMode='numeric' pattern='[0-9]{11}' maxLength={11} value={ruc} onChange={e=>setRuc(e.target.value)} />
      <label className='block' htmlFor='nombre'>Nombre del responsable</label>
      <input id='nombre' className={campo} minLength={2} maxLength={120} autoComplete='name' required value={nombre} onChange={e=>setNombre(e.target.value)} />
      <label className='block' htmlFor='email'>Correo electrónico</label>
      <input id='email' className={campo} type='email' autoComplete='email' required value={email} onChange={e=>setEmail(e.target.value)} />
      <label className='block' htmlFor='password'>Contraseña (mínimo 8 caracteres)</label>
      <input id='password' className={campo} type='password' autoComplete='new-password' minLength={8} maxLength={128} required value={password} onChange={e=>setPassword(e.target.value)} />
      {error && <p role='alert' className='text-red-700'>{error}</p>}
      <button type='submit' disabled={enviando} className='w-full rounded-lg bg-amber-800 px-5 py-3 font-medium text-white disabled:opacity-60'>
        {enviando ? 'Creando cuenta…' : 'Crear cuenta'}
      </button>
    </form>
    <p className='mt-5 text-sm'>¿Ya tienes cuenta? <Link className='text-amber-800 underline' to='/login'>Inicia sesión</Link></p>
  </main>;
}
