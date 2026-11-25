import { useId, useLayoutEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { after } from "../lib/demo";

const asDate = (day: string) => new Date(day + "T12:00:00Z");
const monthText = new Intl.DateTimeFormat("es-PE", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const fullDate = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "full",
  timeZone: "UTC",
});
const shortDate = new Intl.DateTimeFormat("es-PE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "UTC",
});
const monthStart = (day: string) => day.slice(0, 7) + "-01";
function shiftMonth(day: string, delta: number) {
  const date = asDate(monthStart(day));
  date.setUTCMonth(date.getUTCMonth() + delta);
  const start = date.toISOString().slice(0, 10);
  date.setUTCMonth(date.getUTCMonth() + 1, 0);
  return after(
    Math.min(asDate(day).getUTCDate(), date.getUTCDate()) - 1,
    start,
  );
}
export default function DateField({
  label,
  name,
  min,
  defaultValue,
}: {
  label: string;
  name: string;
  min: string;
  defaultValue: string;
}) {
  const id = useId(),
    dialog = useRef<HTMLDialogElement>(null),
    grid = useRef<HTMLDivElement>(null);
  const [selected, select] = useState(defaultValue),
    [cursor, setCursor] = useState(defaultValue);
  const first = monthStart(cursor),
    offset = (asDate(first).getUTCDay() + 6) % 7;
  const end = asDate(shiftMonth(first, 1));
  end.setUTCDate(0);
  function focusDay() {
    grid.current?.querySelector<HTMLButtonElement>('[tabindex="0"]')?.focus();
  }
  useLayoutEffect(() => {
    if (dialog.current?.open && grid.current?.contains(document.activeElement))
      focusDay();
  }, [cursor]);
  function open() {
    setCursor(selected);
    dialog.current?.showModal();
    requestAnimationFrame(focusDay);
  }
  function choose(day: string) {
    select(day);
    dialog.current?.close();
  }
  function keydown(e: KeyboardEvent<HTMLButtonElement>, day: string) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      choose(day);
      return;
    }
    const weekday = (asDate(day).getUTCDay() + 6) % 7;
    const shifts: Record<string, number> = {
      ArrowLeft: -1,
      ArrowRight: 1,
      ArrowUp: -7,
      ArrowDown: 7,
      Home: -weekday,
      End: 6 - weekday,
    };
    const next =
      e.key in shifts
        ? after(shifts[e.key], day)
        : e.key === "PageUp"
          ? shiftMonth(day, -1)
          : e.key === "PageDown"
            ? shiftMonth(day, 1)
            : null;
    if (next) {
      e.preventDefault();
      setCursor(next < min ? min : next);
      requestAnimationFrame(focusDay);
    }
  }
  function changeMonth(delta: number) {
    const next = shiftMonth(cursor, delta);
    setCursor(next < min ? min : next);
  }
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input type="hidden" name={name} value={selected} />
      <button
        type="button"
        id={id}
        aria-haspopup="dialog"
        className="date-trigger"
        onClick={open}
      >
        {shortDate.format(asDate(selected))}
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          aria-hidden="true"
        >
          <rect x="3" y="5" width="18" height="16" rx="3" />
          <path d="M7 3v5m10-5v5M3 11h18" />
        </svg>
      </button>
      <dialog
        className="calendar"
        ref={dialog}
        aria-labelledby={id + "-title"}
        onClick={(e) => {
          if (e.target === dialog.current) {
            const r = e.currentTarget.getBoundingClientRect();
            if (
              e.clientX < r.left ||
              e.clientX > r.right ||
              e.clientY < r.top ||
              e.clientY > r.bottom
            )
              dialog.current?.close();
          }
        }}
      >
        <header>
          <h2 id={id + "-title"}>{label}</h2>
          <button
            type="button"
            className="cal-icon"
            aria-label="Cerrar calendario"
            onClick={() => dialog.current?.close()}
          >
            ×
          </button>
        </header>
        <div className="cal-nav">
          <button
            type="button"
            className="cal-icon"
            aria-label="Mes anterior"
            disabled={first <= monthStart(min)}
            onClick={() => changeMonth(-1)}
          >
            ‹
          </button>
          <strong aria-live="polite">{monthText.format(asDate(cursor))}</strong>
          <button
            type="button"
            className="cal-icon"
            aria-label="Mes siguiente"
            onClick={() => changeMonth(1)}
          >
            ›
          </button>
        </div>
        <div className="cal-week" aria-hidden="true">
          {["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"].map((w) => (
            <span key={w}>{w}</span>
          ))}
        </div>
        <div className="cal-days" ref={grid}>
          {Array.from({ length: end.getUTCDate() }, (_, i) => {
            const day = after(i, first);
            return (
              <button
                type="button"
                key={day}
                style={i === 0 ? { gridColumnStart: offset + 1 } : undefined}
                disabled={day < min}
                aria-label={fullDate.format(asDate(day))}
                aria-pressed={day === selected}
                tabIndex={day === cursor ? 0 : -1}
                onKeyDown={(e) => keydown(e, day)}
                onClick={() => choose(day)}
              >
                {i + 1}
              </button>
            );
          })}
        </div>
        <footer>
          <button
            type="button"
            className="secondary"
            onClick={() => choose(min)}
          >
            Hoy · {shortDate.format(asDate(min))}
          </button>
        </footer>
      </dialog>
    </div>
  );
}
