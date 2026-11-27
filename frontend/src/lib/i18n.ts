import { isValidElement, cloneElement, type ReactElement } from "react";
import { english } from "./translations";
export type Locale = "es" | "en";
export const languageTags = { es: "es-PE", en: "en-US" };
export function locale(): Locale {
  return document.documentElement.lang.startsWith("en") ? "en" : "es";
}
const keys = Object.keys(english).sort((a, b) => b.length - a.length);
export function translate<T>(value: T): T {
  if (locale() === "es") return value;
  if (Array.isArray(value)) return value.map(translate) as T;
  if (isValidElement(value)) {
    const element = value as ReactElement<Record<string, unknown>>,
      props = { ...element.props };
    if (
      element.type === "option" &&
      props.value === undefined &&
      typeof props.children === "string"
    )
      props.value = props.children;
    for (const key of [
      "children",
      "title",
      "label",
      "placeholder",
      "aria-label",
      "alt",
      "eyebrow",
      "labels",
    ])
      if (key in props) props[key] = translate(props[key]);
    return cloneElement(element, props) as T;
  }
  if (typeof value !== "string") return value;
  const leading = value.match(/^\s*/)?.[0] ?? "",
    trailing = value.match(/\s*$/)?.[0] ?? "",
    text = value.trim();
  if (english[text]) return (leading + english[text] + trailing) as T;
  const pattern = new RegExp(
    keys.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"),
    "gu",
  );
  return value.replace(pattern, (match) => english[match]) as T;
}
