import { useEffect, useId, useRef, useState } from "react";
import type { InputHTMLAttributes, PointerEvent } from "react";

type Props = Pick<
  InputHTMLAttributes<HTMLInputElement>,
  "name" | "min" | "max" | "step" | "defaultValue" | "required" | "readOnly"
> & { label: string };

export default function NumberField({ label, ...props }: Props) {
  const id = useId(),
    ref = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState(Number(props.defaultValue ?? NaN));
  const repeatTimer = useRef<number>();
  function stopRepeat() {
    window.clearTimeout(repeatTimer.current);
    repeatTimer.current = undefined;
  }
  useEffect(() => {
    const form = ref.current?.form;
    const onReset = () =>
      queueMicrotask(() => setValue(ref.current?.valueAsNumber ?? NaN));
    form?.addEventListener("reset", onReset);
    window.addEventListener("blur", stopRepeat);
    return () => {
      stopRepeat();
      window.removeEventListener("blur", stopRepeat);
      form?.removeEventListener("reset", onReset);
    };
  }, []);
  function adjust(direction: number) {
    const input = ref.current;
    if (!input) return false;
    const previous = input.value;
    if (direction > 0) input.stepUp();
    else input.stepDown();
    if (input.value === previous) return false;
    setValue(input.valueAsNumber);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }
  function startRepeat(event: PointerEvent<HTMLButtonElement>, direction: number) {
    if (!event.isPrimary || event.button !== 0) return;
    stopRepeat();
    event.currentTarget.setPointerCapture(event.pointerId);
    if (!adjust(direction)) return;
    function repeat() {
      if (adjust(direction)) repeatTimer.current = window.setTimeout(repeat, 80);
    }
    repeatTimer.current = window.setTimeout(repeat, 400);
  }
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className="stepper">
        <input
          {...props}
          type="number"
          id={id}
          ref={ref}
          onInput={(e) => setValue(e.currentTarget.valueAsNumber)}
        />
        {[-1, 1].map(direction => (
          <button
            key={direction}
            type="button"
            aria-label={(direction < 0 ? "Disminuir " : "Aumentar ") + label}
            disabled={direction < 0 ? value <= Number(props.min) : value >= Number(props.max)}
            onPointerDown={event => startRepeat(event, direction)}
            onPointerUp={stopRepeat}
            onPointerCancel={stopRepeat}
            onLostPointerCapture={stopRepeat}
            onClick={event => { if (event.detail === 0) adjust(direction); }}
          >
            {direction < 0 ? "−" : "+"}
          </button>
        ))}
      </div>
    </div>
  );
}
