import { translate } from "../lib/i18n";
import { useLayoutEffect, useRef, useState } from "react";
import { dateLabel, kg, type Week } from "../lib/demo";

const time = (week: Week) => Date.parse(week.date);
const weekMs = 7 * 86400000;

function tickInterval(range: number) {
  const rough = Math.max(range / 4, 0.01);
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  return (
    ([1, 2, 2.5, 5, 10].find((n) => n * magnitude >= rough) ?? 10) * magnitude
  );
}

export default function WeeklyTrend({
  history,
  projected,
}: {
  history: Week[];
  projected: Week[];
}) {
  const container = useRef<HTMLElement>(null);
  const [width, setWidth] = useState(700);
  const [selectedDate, select] = useState<string>();
  useLayoutEffect(() => {
    const node = container.current;
    if (!node) return;
    const resize = () => setWidth(Math.max(180, node.clientWidth));
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const points = [...history, ...projected];
  if (!points.length)
    return <p>{translate("Sin semanas disponibles para graficar.")}</p>;
  const selected =
    points.find((w) => w.date === selectedDate) ??
    history[history.length - 1] ??
    points[0];
  const low = Math.min(...points.map((w) => w.kg));
  const high = Math.max(...points.map((w) => w.kg));
  const step = tickInterval(Math.max(high - low, high * 0.2, 1));
  const min = Math.max(0, Math.floor((low - step * 0.35) / step) * step);
  const max = Math.max(
    min + step,
    Math.ceil((high + step * 0.35) / step) * step,
  );
  const ticks = Array.from(
    { length: Math.round((max - min) / step) + 1 },
    (_, i) => min + step * i,
  );
  const start = time(points[0]),
    span = Math.max(weekMs, time(points[points.length - 1]) - start);
  const left = 46,
    right = width - 28,
    top = 30,
    bottom = 172;
  const x = (w: Week) => left + ((time(w) - start) / span) * (right - left);
  const y = (amount: number) =>
    bottom - ((amount - min) / (max - min)) * (bottom - top);
  const path = (series: Week[]) =>
    series
      .map(
        (w, i) =>
          (i && time(w) - time(series[i - 1]) <= weekMs ? "L" : "M") +
          x(w) +
          " " +
          y(w.kg),
      )
      .join(" ");
  const boundary = projected.length
    ? x(projected[0]) - ((right - left) * weekMs) / span / 2
    : right;
  const isProjected = projected.some((w) => w.date === selected.date);
  return (
    <figure className="weekly-trend" ref={container}>
      <div className="trend-legend">
        <span>{translate("Historial registrado")}</span>
        <span>{translate("Pronóstico simulado")}</span>
      </div>
      <svg
        viewBox={`0 0 ${width} 210`}
        width="100%"
        height="210"
        aria-label={translate(
          "Consumo semanal en kilogramos. Selecciona un punto para consultar su valor.",
        )}
        role="group"
      >
        <text x="4" y="17" className="axis-text">
          {translate(" kg ")}
        </text>
        {translate(
          projected.length > 0 && (
            <rect
              className="projection-band"
              x={Math.max(left, boundary)}
              y={top - 8}
              width={right - Math.max(left, boundary) + 14}
              height={bottom - top + 8}
              rx="5"
            />
          ),
        )}
        {translate(
          ticks.map((n) => (
            <g key={n}>
              <line
                className="trend-rule"
                x1={left - 8}
                x2={right + 14}
                y1={y(n)}
                y2={y(n)}
              />
              <text
                className="axis-text"
                x={left - 14}
                y={y(n) + 4}
                textAnchor="end"
              >
                {n.toLocaleString("es-PE")}
              </text>
            </g>
          )),
        )}
        <path className="trend-path" d={path(history)} />
        <path className="trend-path estimate" d={path(projected)} />
        {translate(
          points.map((w, i) => {
            const future = i >= history.length,
              active = selected.date === w.date;
            const period = future
              ? "Pronóstico simulado"
              : "Historial registrado";
            return (
              <g
                key={w.date}
                className={future ? "trend-point estimate" : "trend-point"}
              >
                {(width >= 580 ||
                  i === 0 ||
                  i === points.length - 1 ||
                  i === history.length - 1) && (
                  <text
                    className="axis-text"
                    x={x(w)}
                    y={bottom + 24}
                    textAnchor="middle"
                  >
                    {dateLabel(w.date)}
                  </text>
                )}
                {(width >= 580 || active) && (
                  <text
                    className="point-value"
                    x={x(w)}
                    y={y(w.kg) - 13}
                    textAnchor="middle"
                  >
                    {w.kg.toLocaleString("es-PE")}
                  </text>
                )}
                {active && (
                  <circle className="point-halo" cx={x(w)} cy={y(w.kg)} r="9" />
                )}
                <circle className="point-mark" cx={x(w)} cy={y(w.kg)} r="4.2" />
                <circle
                  className="point-hit"
                  cx={x(w)}
                  cy={y(w.kg)}
                  r="13"
                  tabIndex={0}
                  role="button"
                  aria-pressed={active}
                  aria-label={
                    period + ", " + dateLabel(w.date) + ", " + kg(w.kg)
                  }
                  onFocus={() => select(w.date)}
                  onPointerEnter={() => select(w.date)}
                  onClick={() => select(w.date)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      select(w.date);
                    }
                  }}
                />
              </g>
            );
          }),
        )}
      </svg>
      <figcaption>
        <strong>{translate(kg(selected.kg))}</strong>
        <span>
          {translate(
            isProjected ? "Pronóstico simulado" : "Historial registrado",
          )}
          {translate(" · Semana del ")}
          {translate(dateLabel(selected.date))}
        </span>
      </figcaption>
    </figure>
  );
}
