import { translate } from "../lib/i18n";
import { useState } from "react";
import type { Lot } from "../lib/demo";
import { useDemo } from "../lib/session";
import { loadStore, scoped } from "../lib/workspaces";

async function storage() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("originlink.fichas", 1);
    request.onupgradeneeded = () =>
      request.result.createObjectStore("archivos");
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(Error("No se pudo abrir el archivo local."));
  });
}
async function fileRecord(id: string, file?: File): Promise<File | undefined> {
  const db = await storage();
  try {
    return await new Promise<File | undefined>((resolve, reject) => {
      const tx = db.transaction("archivos", file ? "readwrite" : "readonly"),
        records = tx.objectStore("archivos");
      const req = file ? records.put(file, id) : records.get(id);
      tx.oncomplete = () =>
        resolve(file ? undefined : (req.result as File | undefined));
      tx.onabort = () =>
        reject(Error("No se pudo acceder al archivo en este navegador."));
    });
  } finally {
    db.close();
  }
}
export default function LotDocuments({ lot }: { lot: Lot }) {
  const s = useDemo(),
    [error, setError] = useState("");
  return (
    <section className="lot-docs">
      <h3>{translate("Documentos del lote")}</h3>
      {translate(!lot.documents?.length && <p>Sin fichas adjuntas.</p>)}
      {translate(
        lot.documents?.map((doc) => (
          <button
            key={doc.id}
            className="secondary"
            onClick={async () => {
              try {
                const visible =
                  s.role &&
                  scoped(loadStore(), {
                    role: s.role,
                    id: s.supplier,
                  }).lots.find((l) => l.id === lot.id);
                if (
                  !visible ||
                  !visible.documents?.some((d) => d.id === doc.id)
                )
                  throw Error("No tienes acceso a esta ficha.");
                const blob = await fileRecord(doc.id);
                if (!blob) throw Error("Archivo local no disponible.");
                const url = URL.createObjectURL(blob),
                  a = document.createElement("a");
                a.href = url;
                a.download = doc.name;
                a.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
              } catch (ex) {
                setError((ex as Error).message);
              }
            }}
          >
            Descargar {doc.name}
          </button>
        )),
      )}
      {translate(
        s.role === "cooperativa" && (
          <label>
            Adjuntar ficha o muestra · PDF, PNG o JPEG, hasta 5 MB
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={async (e) => {
                const input = e.currentTarget,
                  file = input.files?.[0];
                if (!file) return;
                try {
                  if (
                    !["application/pdf", "image/png", "image/jpeg"].includes(
                      file.type,
                    ) ||
                    file.size > 5 * 1024 * 1024 ||
                    !file.size
                  )
                    throw Error("Elige un PDF, PNG o JPEG de hasta 5 MB.");
                  const id = crypto.randomUUID();
                  await fileRecord(id, file);
                  s.update(
                    (d) => ({
                      ...d,
                      lots: d.lots.map((l) =>
                        l.id === lot.id
                          ? {
                              ...l,
                              documents: [
                                ...(l.documents ?? []),
                                { id, name: file.name },
                              ],
                            }
                          : l,
                      ),
                    }),
                    "Documento guardado.",
                  );
                  setError("");
                } catch (ex) {
                  setError((ex as Error).message);
                }
                input.value = "";
              }}
            />
          </label>
        ),
      )}
      {translate(error && <p role="alert">{error}</p>)}
    </section>
  );
}
