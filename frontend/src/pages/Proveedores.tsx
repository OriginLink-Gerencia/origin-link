import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { ApiError, crearProveedor, invitarProveedor, listarProveedores, actualizarProveedor } from '../lib/api';
import type { InvitacionGenerada, Proveedor, ProveedorDatos } from '../lib/authTypes';

const vacio: ProveedorDatos = {
  nombre: '', region: '', contacto_nombre: '', contacto_telefono: '', contacto_email: '',
};
const campo = 'w-full rounded-lg border border-stone-300 p-2';
const estado: Record<Proveedor['estado_vinculo'], string> = {
  SIN_VINCULAR: 'Sin vincular', INVITADO: 'Invitado', VINCULADO: 'Vinculado',
};

export default function Proveedores() {
  const [lista, setLista] = useState<Proveedor[]>([]);
  const [datos, setDatos] = useState<ProveedorDatos>({ ...vacio });
  const [edicion, setEdicion] = useState<number | null>(null);
  const [invitacion, setInvitacion] = useState<InvitacionGenerada | null>(null);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [invitandoId, setInvitandoId] = useState<number | null>(null);

  const cargar = useCallback(async () => {
    try { setLista(await listarProveedores()); }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo consultar el directorio.'); }
    finally { setCargando(false); }
  }, []);
  useEffect(() => { void cargar(); }, [cargar]);

  function editar(proveedor: Proveedor) {
    setEdicion(proveedor.id);
    setDatos({
      nombre: proveedor.nombre, region: proveedor.region ?? '',
      contacto_nombre: proveedor.contacto_nombre ?? '',
      contacto_telefono: proveedor.contacto_telefono ?? '',
      contacto_email: proveedor.contacto_email ?? '',
    });
    setAviso(''); setError('');
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); setError(''); setAviso(''); setEnviando(true);
    try {
      const limpio: ProveedorDatos = {
        nombre: datos.nombre.trim(), region: datos.region?.trim() || null,
        contacto_nombre: datos.contacto_nombre?.trim() || null,
        contacto_telefono: datos.contacto_telefono?.trim() || null,
        contacto_email: datos.contacto_email?.trim() || null,
      };
      if (edicion === null) await crearProveedor(limpio);
      else await actualizarProveedor(edicion, limpio);
      setDatos({ ...vacio }); setEdicion(null);
      setAviso(edicion === null ? 'Proveedor registrado correctamente.' : 'Proveedor actualizado correctamente.');
      await cargar();
    } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar el proveedor.'); }
    finally { setEnviando(false); }
  }

  async function invitar(id: number) {
    setError(''); setAviso(''); setInvitacion(null); setInvitandoId(id);
    try { setInvitacion(await invitarProveedor(id)); await cargar(); }
    catch (err) {
      if (err instanceof ApiError && err.status === 409) setError('Este proveedor ya está vinculado.');
      else setError(err instanceof Error ? err.message : 'No se pudo crear la invitación.');
    } finally { setInvitandoId(null); }
  }

  async function copiarEnlace() {
    if (!invitacion) return;
    try { await navigator.clipboard.writeText(invitacion.url); setAviso('Enlace copiado.'); }
    catch { setError('No se pudo copiar automáticamente. Selecciona el enlace y cópialo.'); }
  }

  const actualizarCampo = (nombre: keyof ProveedorDatos, valor: string) =>
    setDatos((anterior) => ({ ...anterior, [nombre]: valor }));

  return <section className='space-y-7'>
    <div>
      <h1 className='text-3xl font-semibold text-stone-900'>Proveedores</h1>
      <p className='mt-2 text-stone-600'>Registra tus proveedores, actualiza sus datos y envía invitaciones de vinculación.</p>
    </div>
    {error && <p role='alert' className='rounded-lg bg-red-50 p-3 text-red-700'>{error}</p>}
    {aviso && <p role='status' className='rounded-lg bg-green-50 p-3 text-green-800'>{aviso}</p>}
    <form onSubmit={guardar} className='space-y-4 rounded-xl border border-stone-200 bg-white p-5'>
      <h2 className='text-xl font-semibold'>{edicion === null ? 'Registrar proveedor' : 'Editar proveedor'}</h2>
      <div className='grid gap-4 sm:grid-cols-2'>
        <label className='block text-sm font-medium'>Nombre del proveedor *
          <input className={campo} required minLength={2} maxLength={150} value={datos.nombre} onChange={(e) => actualizarCampo('nombre', e.target.value)} />
        </label>
        <label className='block text-sm font-medium'>Región
          <input className={campo} maxLength={100} value={datos.region ?? ''} onChange={(e) => actualizarCampo('region', e.target.value)} />
        </label>
        <label className='block text-sm font-medium'>Nombre del contacto
          <input className={campo} maxLength={120} value={datos.contacto_nombre ?? ''} onChange={(e) => actualizarCampo('contacto_nombre', e.target.value)} />
        </label>
        <label className='block text-sm font-medium'>Teléfono del contacto
          <input className={campo} maxLength={30} value={datos.contacto_telefono ?? ''} onChange={(e) => actualizarCampo('contacto_telefono', e.target.value)} />
        </label>
        <label className='block text-sm font-medium'>Correo del contacto
          <input type='email' className={campo} value={datos.contacto_email ?? ''} onChange={(e) => actualizarCampo('contacto_email', e.target.value)} />
        </label>
      </div>
      <div className='flex flex-wrap gap-3'>
        <button type='submit' disabled={enviando} className='rounded-lg bg-amber-800 px-5 py-2.5 font-medium text-white disabled:opacity-60'>
          {enviando ? 'Guardando…' : edicion === null ? 'Registrar proveedor' : 'Guardar cambios'}
        </button>
        {edicion !== null && <button type='button' onClick={() => { setEdicion(null); setDatos({ ...vacio }); }} className='rounded-lg border border-stone-300 px-5 py-2.5'>Cancelar edición</button>}
      </div>
    </form>
    {invitacion && <div className='rounded-xl border border-amber-300 bg-amber-50 p-5'>
      <h2 className='font-semibold'>Enlace de invitación generado</h2>
      <p className='mt-1 text-sm'>Válido hasta {new Date(invitacion.expira_en).toLocaleString('es-PE')}. Comparte el enlace con la cooperativa.</p>
      <div className='mt-3 flex flex-wrap gap-2'>
        <input aria-label='Enlace de invitación' readOnly className='min-w-0 flex-1 rounded-lg border border-stone-300 bg-white p-2 text-sm' value={invitacion.url} onFocus={(e) => e.target.select()} />
        <button type='button' onClick={() => void copiarEnlace()} className='rounded-lg bg-amber-800 px-4 py-2 text-sm font-medium text-white'>Copiar enlace</button>
      </div>
    </div>}
    <div>
      <h2 className='text-xl font-semibold'>Directorio de proveedores</h2>
      {cargando ? <p className='mt-4'>Cargando proveedores…</p> : lista.length === 0 ? <p className='mt-4 text-stone-600'>Aún no tienes proveedores registrados.</p> : <div className='mt-4 space-y-3'>
        {lista.map((p) => <article key={p.id} className='rounded-xl border border-stone-200 bg-white p-4'>
          <div className='flex flex-wrap items-start justify-between gap-3'>
            <div>
              <h3 className='font-semibold text-stone-900'>{p.nombre}</h3>
              <p className='text-sm text-stone-600'>{p.region || 'Región sin especificar'} · {estado[p.estado_vinculo]}</p>
              {p.contacto_nombre && <p className='mt-1 text-sm'>Contacto: {p.contacto_nombre}</p>}
              {p.contacto_email && <p className='text-sm'>Correo: {p.contacto_email}</p>}
              {p.contacto_telefono && <p className='text-sm'>Teléfono: {p.contacto_telefono}</p>}
            </div>
            <div className='flex flex-wrap gap-2'>
              <button type='button' onClick={() => editar(p)} className='rounded-lg border border-stone-300 px-3 py-2 text-sm'>Editar</button>
              {p.estado_vinculo !== 'VINCULADO' && <button type='button' disabled={invitandoId !== null} onClick={() => void invitar(p.id)} className='rounded-lg bg-amber-800 px-3 py-2 text-sm font-medium text-white disabled:opacity-60'>
                {invitandoId === p.id ? 'Generando…' : p.estado_vinculo === 'INVITADO' ? 'Reenviar invitación' : 'Invitar'}
              </button>}
            </div>
          </div>
        </article>)}
      </div>}
    </div>
  </section>;
}
