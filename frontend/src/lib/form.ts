export const values = (form: HTMLFormElement) =>
  Object.fromEntries(new FormData(form)) as Record<string, string>;
