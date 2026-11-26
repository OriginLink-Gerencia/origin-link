// Plan de abastecimiento: combina el pronóstico, la recomendación y las alertas del servidor con los datos de pantalla.
import { after, balance, pending, round, type Data, type Week } from "./demo";
import { toWeek, type AlertDTO, type ForecastDTO, type RecommendationDTO } from "./backend";

export type Plan = {
  forecast: ForecastDTO | null;
  recommendation: RecommendationDTO | null;
  alerts: AlertDTO[];
  /** Por qué no hay pronóstico (por ejemplo, falta importar consumo). */
  reason: string;
};

export const emptyPlan: Plan = { forecast: null, recommendation: null, alerts: [], reason: "" };

/** Lo que muestran el resumen y la pantalla de pronóstico. Los números del cálculo vienen del servidor. */
export function summary(d: Data, plan: Plan, recommendation: RecommendationDTO | null = plan.recommendation) {
  const history: Week[] = plan.forecast?.historial.map(toWeek) ?? [];
  const values = plan.forecast?.pronostico.map((p) => p.kg) ?? [0, 0, 0, 0];
  const first = plan.forecast?.pronostico[0]?.semana ?? after(1);
  const demand = round(values.reduce((sum, n) => sum + n, 0));
  const mean = demand / (values.length || 1);
  const stock = recommendation?.factores.existencias_kg ?? balance(d);
  const incoming = d.orders.filter((o) => o.due <= after(28)).reduce((sum, o) => sum + pending(o), 0);
  return {
    history,
    mean,
    demand,
    first,
    prediction: {
      method: plan.forecast?.metodo === "TCN" ? "TCN global" : "Promedio móvil",
      reason: plan.forecast?.motivo_metodo ?? (plan.forecast ? "La TCN se aplicó con el historial disponible." : plan.reason),
      values,
      mape: plan.forecast?.mape_referencia ?? null,
    },
    stock,
    incoming,
    gap: Math.max(0, round(mean * 4 - stock - incoming)),
    need: recommendation?.cantidad_sugerida_kg ?? 0,
    days: recommendation?.factores.plazo_entrega_dias ?? 7,
    minimum: recommendation?.factores.cantidad_minima_kg ?? 0,
    low: plan.alerts.some((a) => a.tipo === "STOCK_BAJO"),
    date: recommendation?.fecha_limite_compra ?? after(0),
    daysStock: recommendation?.dias_cobertura_actual ?? 0,
    explanation: recommendation?.explicacion ?? "",
  };
}
