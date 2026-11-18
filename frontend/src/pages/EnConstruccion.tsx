interface Props {
  titulo: string;
  historia: string;
}

/** Página temporal para los módulos del MVP que aún no se implementan. */
export default function EnConstruccion({ titulo, historia }: Props) {
  return (
    <section>
      <h1 className="text-2xl font-semibold">{titulo}</h1>
      <p className="mt-2 text-stone-600">Módulo en desarrollo ({historia}).</p>
    </section>
  );
}
