type PaginatedResponse<T> = {
  status: string;
  data: T[];
  pagination: {
    total: number;
    offset: number;
    limit: number;
    count: number;
    has_more: boolean;
  };
};

type ObjectResponse<T> = {
  status: string;
  data: T;
};

type ErrorResponse = {
  status?: string;
  detail?: string;
  error_code?: string;
};

export type ClientApi = {
  id: number;
  name: string;
  risk_profile: string;
};

export type AccountApi = {
  id: number;
  client_id: number;
  broker: string;
};

export type AssetApi = {
  id: number;
  ticker: string | null;
  original_name: string;
  normalized_name: string;
  asset_class: string;
  cnpj: string | null;
  maturity_date: string | null;
};

export type PositionApi = {
  id: number;
  account_id: number;
  asset_id: number;
  quantity: string;
  avg_price: string;
  total_value: string;
  reference_date: string;
};

export type UploadApi = {
  filename: string;
  detected_type: string;
  rows_processed: number;
  rows_skipped: number;
  message: string;
  processed_at: string;
  raw_file: string;
  processed_file: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function assertUploadPayload(value: unknown): UploadApi {
  if (!isRecord(value)) {
    throw new Error("A resposta do backend para upload veio em formato inválido.");
  }

  const requiredStringFields = ["filename", "detected_type", "message", "processed_at", "raw_file", "processed_file"] as const;
  for (const field of requiredStringFields) {
    if (typeof value[field] !== "string" || !value[field]) {
      throw new Error(`A resposta do backend não trouxe o campo obrigatório '${field}'.`);
    }
  }

  const requiredNumberFields = ["rows_processed", "rows_skipped"] as const;
  for (const field of requiredNumberFields) {
    if (typeof value[field] !== "number" || Number.isNaN(value[field])) {
      throw new Error(`A resposta do backend não trouxe o campo numérico '${field}' corretamente.`);
    }
  }

  return value as UploadApi;
}

async function parseErrorResponse(response: Response, fallbackMessage: string): Promise<string> {
  try {
    const payload: ErrorResponse = await response.json();
    return payload.detail || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function fetchPaginated<T>(path: string): Promise<T[]> {
  const items: T[] = [];
  let offset = 0;
  const limit = 100;

  while (true) {
    const response = await fetch(`${path}${path.includes("?") ? "&" : "?"}offset=${offset}&limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Falha ao consultar ${path}`);
    }

    const payload: PaginatedResponse<T> = await response.json();
    if (!payload || payload.status !== "success" || !Array.isArray(payload.data) || !payload.pagination) {
      throw new Error(`A resposta de ${path} veio em formato inesperado.`);
    }

    items.push(...payload.data);

    if (!payload.pagination.has_more) {
      break;
    }
    offset += limit;
  }

  return items;
}

export async function uploadPortfolioFile(file: File): Promise<UploadApi> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch("/upload", {
      method: "POST",
      body: formData
    });
  } catch {
    throw new Error("Não foi possível conectar ao backend para enviar o arquivo.");
  }

  if (!response.ok) {
    const fallbackMessage =
      response.status >= 500
        ? "O backend não conseguiu concluir o processamento do arquivo."
        : "O upload foi recusado. Revise o arquivo e tente novamente.";
    throw new Error(await parseErrorResponse(response, fallbackMessage));
  }

  const payload: ObjectResponse<unknown> = await response.json();
  if (!payload || payload.status !== "success") {
    throw new Error("O backend respondeu ao upload sem confirmar sucesso.");
  }

  return assertUploadPayload(payload.data);
}

export async function fetchPortfolioSnapshot() {
  const [clients, accounts, assets, positions] = await Promise.all([
    fetchPaginated<ClientApi>("/clients"),
    fetchPaginated<AccountApi>("/accounts"),
    fetchPaginated<AssetApi>("/assets"),
    fetchPaginated<PositionApi>("/positions")
  ]);

  return { clients, accounts, assets, positions };
}
