const assetClassLabels: Record<string, string> = {
  fixed_income: "Renda fixa",
  equities: "Ações",
  crypto: "Cripto",
  funds: "Fundos",
  others: "Outros"
};

export function assetClassLabel(value: string) {
  return assetClassLabels[value] ?? value.replace(/_/g, " ");
}

export const chartPalette = ["#38bdf8", "#2563eb", "#14b8a6", "#f59e0b", "#8b5cf6", "#0f766e"];
