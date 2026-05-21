import { expect, type Page, type Route, test } from "@playwright/test";

const apiBaseUrl = "http://127.0.0.1:8000";

test("homepage loads in demo mode", async ({ page }) => {
  await mockApi(page, { userAuthEnabled: false });

  await page.goto("/");

  await expect(page.getByRole("heading", { name: /upload a csv or excel dataset/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /api status: api online/i })).toBeVisible();
});

test("logged out production users see auth page", async ({ page }) => {
  await mockApi(page, { userAuthEnabled: true });

  await page.goto("/");

  await expect(page.getByRole("heading", { name: /sign in to your aidssist intelligence workspace/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /welcome back/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /^sign in$/i })).toBeVisible();
});

test("dataset 401 routes to auth page without showing api offline", async ({ page }) => {
  let authStatusCalls = 0;
  await mockApi(page, {
    userAuthEnabled: false,
    onAuthStatus: () => {
      authStatusCalls += 1;
      return { user_auth_enabled: authStatusCalls > 2 };
    },
    datasetsStatus: 401,
  });

  await page.goto("/");

  await expect(page.getByText("Sign in required")).toBeVisible();
  await expect(page.getByRole("heading", { name: /sign in to your aidssist intelligence workspace/i })).toBeVisible();
  await expect(page.getByText("API Offline")).toHaveCount(0);
});

test("401 api status shows auth required, not api offline", async ({ page }) => {
  await mockApi(page, { healthStatus: 401, userAuthEnabled: true });

  await page.goto("/");

  await expect(page.getByRole("button", { name: /api status: auth required/i })).toBeVisible();
  await expect(page.getByText("API Offline")).toHaveCount(0);
});

test("register and login flow reaches upload workspace", async ({ page }) => {
  await mockApi(page, { userAuthEnabled: true });

  await page.goto("/");
  await page.getByRole("button", { name: /create an account/i }).click();
  await page.getByLabel("Full name").fill("Test User");
  await page.getByLabel("Email").fill("test@example.com");
  await page.getByLabel("Password").fill("test-password");
  await page.getByRole("button", { name: /^create account$/i }).click();

  await expect(page.getByRole("heading", { name: /upload a csv or excel dataset/i })).toBeVisible();
});

test("authenticated user can reach dashboard, chat, and report flows", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("aidssist_access_token", "test-token");
  });
  await mockApi(page, { userAuthEnabled: true, datasets: [dataset] });

  await page.goto("/");
  await page.getByRole("button", { name: /open dataset sales\.csv/i }).click();

  await expect(page.getByRole("heading", { name: /dataset intelligence profile/i })).toBeVisible();
  await expect(page.getByText("Running deterministic analysis")).toHaveCount(0);
  await expect(page.getByText("Dataset Q&A")).toBeVisible();

  await page.getByLabel("Ask a question about this dataset").fill("Summarize this dataset");
  await page.getByRole("button", { name: /^send$/i }).click();
  await expect(page.getByText("Chat answer for Summarize this dataset")).toBeVisible();

  await page.getByRole("button", { name: /^generate report$/i }).click();
  await expect(page.getByText("Report generated")).toBeVisible();
});

test("dataset search, quality score, and delete work", async ({ page }) => {
  const datasets = [dataset, { ...dataset, dataset_id: "dataset-2", original_filename: "inventory.csv" }];
  await mockApi(page, { userAuthEnabled: false, datasets });

  await page.goto("/");
  await page.getByPlaceholder("Search datasets or columns").fill("inventory");
  await expect(page.getByText("inventory.csv")).toBeVisible();
  await expect(page.getByText("sales.csv")).toHaveCount(0);

  await page.getByPlaceholder("Search datasets or columns").fill("sales");
  await page.getByRole("button", { name: /open dataset sales\.csv/i }).click();
  await expect(page.getByText("Quality score: 82/100")).toBeVisible();
  await expect(page.getByText("Good")).toBeVisible();

  await page.getByRole("button", { name: /back to uploads/i }).click();
  page.on("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: /delete dataset sales\.csv/i }).click();
  await expect(page.getByText("sales.csv")).toHaveCount(0);
});

type MockApiOptions = {
  datasets?: unknown[];
  datasetsStatus?: number;
  healthStatus?: number;
  onAuthStatus?: () => Partial<AuthStatus>;
  userAuthEnabled: boolean;
};

type AuthStatus = {
  user_auth_enabled: boolean;
  api_key_auth_enabled: boolean;
  llm_enabled: boolean;
  llm_provider: string;
  llm_model: string;
  llm_key_configured: boolean;
};

async function mockApi(page: Page, options: MockApiOptions) {
  let currentDatasets = [...(options.datasets ?? [])];

  await page.route(`${apiBaseUrl}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (path === "/health") {
      await fulfillJson(route, { status: "ok", app_name: "Aidssist V3 API", version: "test", environment: "test" }, options.healthStatus ?? 200);
      return;
    }

    if (path === "/auth/status") {
      await fulfillJson(route, {
        user_auth_enabled: options.userAuthEnabled,
        api_key_auth_enabled: false,
        llm_enabled: false,
        llm_provider: "gemini",
        llm_model: "gemini-2.5-flash",
        llm_key_configured: false,
        ...options.onAuthStatus?.(),
      } satisfies AuthStatus);
      return;
    }

    if (path === "/auth/register") {
      await fulfillJson(route, user, 201);
      return;
    }

    if (path === "/auth/login") {
      await fulfillJson(route, { access_token: "test-token", token_type: "bearer", expires_in: 86400, user });
      return;
    }

    if (path === "/auth/me") {
      await fulfillJson(route, user);
      return;
    }

    if (path === "/workspaces") {
      await fulfillJson(route, [workspace]);
      return;
    }

    if (path === "/datasets" && request.method() === "GET") {
      if (options.datasetsStatus) {
        await fulfillJson(route, { detail: "Authentication is required." }, options.datasetsStatus);
        return;
      }
      await fulfillJson(route, currentDatasets);
      return;
    }

    if (path.startsWith("/datasets/") && request.method() === "DELETE") {
      const datasetId = path.split("/")[2];
      currentDatasets = currentDatasets.filter(
        (item) => (item as { dataset_id?: string }).dataset_id !== datasetId,
      );
      await fulfillJson(route, {
        dataset_id: datasetId,
        deleted: true,
        message: "Dataset deleted successfully.",
      });
      return;
    }

    if (path === `/datasets/${dataset.dataset_id}/analyze`) {
      await fulfillJson(route, analysis);
      return;
    }

    if (path === `/datasets/${dataset.dataset_id}/charts/date_sales_line/data`) {
      await fulfillJson(route, {
        chart_id: "date_sales_line",
        chart_type: "line",
        data: [
          { date: "2026-01-01", sales: 100 },
          { date: "2026-01-02", sales: 125 },
        ],
        x: "date",
        y: "sales",
        series: null,
        metadata: {},
      });
      return;
    }

    if (path === `/datasets/${dataset.dataset_id}/forecast`) {
      await fulfillJson(route, forecast);
      return;
    }

    if (path === `/datasets/${dataset.dataset_id}/chat`) {
      const payload = request.postDataJSON() as { message?: string };
      await fulfillJson(route, {
        dataset_id: dataset.dataset_id,
        conversation_id: "conversation-1",
        message: payload.message ?? "",
        answer: `Chat answer for ${payload.message ?? ""}`,
        intent: "summary",
        confidence: 0.94,
        columns_used: ["sales"],
        result: { type: "text", data: "Chat result" },
        suggested_followups: [],
        warnings: [],
        created_at: now,
      });
      return;
    }

    if (path === `/datasets/${dataset.dataset_id}/report`) {
      await fulfillJson(route, report);
      return;
    }

    if (path === "/jobs") {
      await fulfillJson(route, { jobs: [], total: 0, limit: 8, offset: 0 });
      return;
    }

    await fulfillJson(route, { detail: `Unhandled mocked route: ${path}` }, 404);
  });
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    headers: { "X-Request-ID": "test-request" },
    body: JSON.stringify(body),
  });
}

const now = "2026-05-20T00:00:00.000Z";

const user = {
  id: 1,
  email: "test@example.com",
  full_name: "Test User",
  is_active: true,
  is_admin: false,
  created_at: now,
};

const workspace = {
  id: 1,
  name: "Test Workspace",
  slug: "test-workspace",
  role: "owner",
  created_at: now,
};

const dataset = {
  dataset_id: "dataset-1",
  original_filename: "sales.csv",
  stored_filename: "sales.csv",
  file_size_bytes: 1024,
  content_type: "text/csv",
  row_count: 2,
  column_count: 2,
  created_at: now,
  last_analyzed_at: now,
  workspace_id: 1,
  owner_user_id: 1,
  columns: ["date", "sales", "region"],
};

const analysis = {
  dataset_id: dataset.dataset_id,
  row_count: 2,
  column_count: 2,
  created_at: now,
  columns: [
    {
      name: "date",
      dtype: "datetime64[ns]",
      semantic_type: "datetime",
      missing_count: 0,
      missing_percent: 0,
      unique_count: 2,
      unique_percent: 100,
      sample_values: ["2026-01-01", "2026-01-02"],
      stats: { min_date: "2026-01-01", max_date: "2026-01-02", range_days: 1 },
    },
    {
      name: "sales",
      dtype: "int64",
      semantic_type: "numeric",
      missing_count: 0,
      missing_percent: 0,
      unique_count: 2,
      unique_percent: 100,
      sample_values: [100, 125],
      stats: { mean: 112.5, median: 112.5, min: 100, max: 125, std: 12.5 },
    },
  ],
  quality: {
    missing_cells: 0,
    missing_percent: 0,
    duplicate_rows: 0,
    duplicate_percent: 0,
    empty_columns: [],
    constant_columns: [],
    invalid_type_columns: [],
    high_cardinality_columns: ["region"],
    date_parse_issue_columns: [],
    outlier_columns: [],
    issue_breakdown: [
      {
        type: "high_cardinality",
        severity: "low",
        title: "High-cardinality columns",
        message: "These columns have many distinct values and may need grouping for analysis.",
        columns: ["region"],
        count: 1,
        percent: null,
      },
    ],
    quality_score: 82,
  },
  correlations: [],
  insights: [
    {
      type: "growth",
      severity: "info",
      title: "Sales increased",
      message: "Sales increased across the sample period.",
      columns: ["sales"],
    },
  ],
  recommended_charts: [
    {
      chart_id: "date_sales_line",
      title: "Sales over time",
      description: "Sales trend by date.",
      chart_type: "line",
      x: "date",
      y: "sales",
      series: null,
      priority: 1,
      reason: "A time series chart is useful for sales.",
      config: {},
    },
  ],
};

const forecast = {
  dataset_id: dataset.dataset_id,
  date_column: "date",
  target_column: "sales",
  model_used: "linear_regression",
  frequency: "D",
  periods: 2,
  historical_points: [
    { date: "2026-01-01", value: 100 },
    { date: "2026-01-02", value: 125 },
  ],
  forecast_points: [
    { date: "2026-01-03", predicted_value: 150, lower_bound: 145, upper_bound: 155 },
    { date: "2026-01-04", predicted_value: 175, lower_bound: 168, upper_bound: 182 },
  ],
  metrics: { mae: 1, rmse: 1.2, mape: 1.5 },
  assumptions: ["Mock forecast assumption."],
  warnings: [],
  created_at: now,
};

const report = {
  dataset_id: dataset.dataset_id,
  report_id: "report-1",
  format: "html",
  filename: "aidssist_report.html",
  download_url: `/datasets/${dataset.dataset_id}/reports/report-1/download`,
  created_at: now,
};
