import { after, round, TODAY, type Week } from "./demo";
type Cell = unknown;
export function weeklyRows(rows: Cell[][]): Week[] {
  const header =
    rows[0]?.map((c) =>
      String(c ?? "")
        .replace(/^\uFEFF/, "")
        .trim()
        .toLowerCase(),
    ) ?? [];
  const time = header.includes("fecha")
      ? header.indexOf("fecha")
      : header.indexOf("semana"),
    weight = header.indexOf("kg_consumidos");
  if (time < 0 || weight < 0)
    throw Error("Incluye las columnas fecha y kg_consumidos.");
  const weeks = new Map<string, number>(),
    failures: string[] = [];
  rows.slice(1).forEach((cells, i) => {
    if (cells.every((c) => c === null || String(c).trim() === "")) return;
    const cell = cells[time],
      raw = cells[weight];
    const date =
      cell instanceof Date
        ? cell.toISOString().slice(0, 10)
        : String(cell ?? "").trim();
    const stamp = new Date(date + "T12:00:00Z"),
      amount = Number(
        String(raw ?? "")
          .trim()
          .replace(",", "."),
      );
    if (
      !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
      !Number.isFinite(stamp.getTime()) ||
      stamp.toISOString().slice(0, 10) !== date ||
      date > TODAY ||
      raw == null ||
      !String(raw).trim() ||
      !Number.isFinite(amount) ||
      amount < 0
    ) {
      failures.push(String(i + 2));
      return;
    }
    const monday = after(-((stamp.getUTCDay() + 6) % 7), date);
    weeks.set(monday, round((weeks.get(monday) ?? 0) + amount));
  });
  if (failures.length)
    throw Error(
      "Revisa las filas " +
        failures.join(", ") +
        ". Usa fechas válidas hasta el día del piloto y kilos positivos o cero.",
    );
  if (!weeks.size) throw Error("El archivo no contiene consumos.");
  return [...weeks].map(([date, kg]) => ({ date, kg }));
}
export async function readConsumption(file: File) {
  if (/\.xlsx$/i.test(file.name)) {
    const { default: read } = await import("read-excel-file");
    return weeklyRows(await read(file));
  }
  if (!/\.csv$/i.test(file.name))
    throw Error("Elige un archivo CSV o Excel (.xlsx).");
  const lines = (await file.text()).trim().split(/\r?\n/),
    delimiter = lines[0]?.includes(";") ? ";" : ",";
  return weeklyRows(
    lines.map((line) =>
      line
        .split(delimiter)
        .map((cell) => cell.trim().replace(/^"(.*)"$/, "$1")),
    ),
  );
}
