import { locale, languageTags } from "./i18n";
import { pending, received, type Order } from "./demo";
export function performance(orders: Order[]) {
  const delivered = orders.filter((o) => o.receipts.length && !pending(o));
  if (!delivered.length) return null;
  const weight =
    delivered.reduce((sum, o) => sum + received(o), 0) /
    delivered.reduce((sum, o) => sum + o.kg, 0);
  const onTime =
    delivered.filter((o) => o.receipts.every((r) => r.date <= o.due)).length /
    delivered.length;
  const percent = (n: number) =>
    n.toLocaleString(languageTags[locale()], {
      style: "percent",
      maximumFractionDigits: 1,
    });
  return {
    weight: percent(weight),
    onTime: percent(onTime),
    count: delivered.length,
  };
}
