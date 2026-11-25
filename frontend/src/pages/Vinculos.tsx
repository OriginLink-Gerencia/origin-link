import { useEffect, useState } from 'react';
import { listarVinculos } from '../lib/api';
import type { VinculoAceptado } from '../lib/authTypes';

export default function Vinculos() {
  const [vinculos, setVinculos] = useState<VinculoAceptado[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let activo = true;
    listarVinculos().then((datos) => { if (activo) setVinculos(datos); })
      .catch((err: unknown) => { if (activo) setError(err instanceof Error ? err.message : 'No se pudieron consultar los vínculos.'); })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, []);

  return <section className='space-y-6'>
    <div>
      <h1 className='text-3xl font-semibold'>Mis vínculos</h1>
      <p className='mt-2 text-stone-600'>Tostadores con los que tu cooperativa mantiene una relación activa.</p>
    </div>
    {cargando && <p>Cargando vínculos…</p>}
    {error && <p role='alert' className='rounded-lg bg-red-50 p-3 text-red-700'>{error}</p>}
    {!cargando && !error && vinculos.length === 0 && <p className='rounded-lg border border-stone-200 p-4 text-stone-600'>Todavía no tienes vínculos. Acepta una invitación de un tostador para aparecer aquí.</p>}
    {!cargando && !error && vinculos.map((v) => <article key={v.tostador_id} className='rounded-xl border border-stone-200 bg-white p-5'>
      <h2 className='text-lg font-semibold'>{v.tostador}</h2>
      <p className='mt-2 text-sm text-stone-600'>Vinculado desde: {new Date(v.vinculado_desde).toLocaleDateString('es-PE')}</p>
    </article>)}
  </section>;
}
