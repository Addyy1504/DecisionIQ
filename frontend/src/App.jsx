import { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";

import "./App.css";


const CHART_COLORS = {
  primary: "#6366F1",
  secondary: "#14B8A6",
  accent: "#F59E0B",
  success: "#22C55E",
  danger: "#EF4444",
  neutral: "#64748B",
};


const SERIES_PALETTE = [
  "#6366F1",
  "#14B8A6",
  "#F59E0B",
  "#22C55E",
  "#EF4444",
  "#8B5CF6",
];


function formatNumber(value, key = "") {
  if (typeof value !== "number") {
    return value;
  }

  const lowerKey = key.toLowerCase();

  if (
    lowerKey.includes("pct") ||
    lowerKey.includes("rate") ||
    lowerKey.includes("margin")
  ) {
    return `${value.toFixed(2)}%`;
  }

  if (
    lowerKey.includes("revenue") ||
    lowerKey.includes("profit") ||
    lowerKey.includes("sales") ||
    lowerKey.includes("refund") ||
    lowerKey.includes("cogs") ||
    lowerKey.includes("spend")
  ) {
    return `₹${value.toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    })}`;
  }

  return value.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
}


function formatChartAxis(value, key = "") {
  if (typeof value !== "number") {
    return value;
  }

  const lowerKey = key.toLowerCase();

  const isCurrency =
    lowerKey.includes("revenue") ||
    lowerKey.includes("profit") ||
    lowerKey.includes("sales") ||
    lowerKey.includes("refund") ||
    lowerKey.includes("cogs") ||
    lowerKey.includes("spend");

  if (
    lowerKey.includes("pct") ||
    lowerKey.includes("rate") ||
    lowerKey.includes("margin")
  ) {
    return `${value.toFixed(1)}%`;
  }

  if (isCurrency) {
    if (Math.abs(value) >= 1_000_000_000) {
      return `₹${(value / 1_000_000_000).toFixed(1)}B`;
    }

    if (Math.abs(value) >= 1_000_000) {
      return `₹${(value / 1_000_000).toFixed(0)}M`;
    }

    if (Math.abs(value) >= 1_000) {
      return `₹${(value / 1_000).toFixed(0)}K`;
    }

    return `₹${value}`;
  }

  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }

  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(0)}K`;
  }

  return value.toFixed(1);
}


function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>

      {payload.map((item) => (
        <div key={item.dataKey}>
          <span>{item.name}</span>

          <b>
            {formatNumber(
              item.value,
              item.dataKey
            )}
          </b>
        </div>
      ))}
    </div>
  );
}


function DataTable({ data }) {
  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>
                {column.replaceAll("_", " ")}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column}>
                  {formatNumber(
                    row[column],
                    column
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}



function extractYear(value) {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "number") {
    const year = Math.trunc(value);
    return year >= 2000 && year <= 2100 ? year : null;
  }

  const match = String(value).match(/\b(20\d{2})\b/);
  return match ? Number(match[1]) : null;
}


function filterDataByYear(data, xKey, selectedYear) {
  if (
    selectedYear === "all" ||
    !Array.isArray(data) ||
    !xKey
  ) {
    return data;
  }

  const filtered = data.filter(
    (row) => extractYear(row?.[xKey]) === Number(selectedYear)
  );

  return filtered.length ? filtered : data;
}



function cleanFeatureLabel(feature = "") {
  return feature
    .replace("category_", "Category: ")
    .replace("subcategory_", "Subcategory: ")
    .replaceAll("_", " ");
}


function cleanRiskTableRows(rows = []) {
  return rows.map((row) => ({
    order_item_id: row.order_item_id,
    customer_id: row.customer_id,
    order_date: row.order_date
      ? String(row.order_date).split("T")[0]
      : "",
    category: row.category,
    subcategory: row.subcategory,
    quantity: row.quantity,
    unit_price: row.unit_price,
    discount: `${Math.round(Number(row.discount_pct || 0) * 100)}%`,
    return_risk_pct: row.return_risk_pct,
    risk_level: row.risk_level,
  }));
}


function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showVisuals, setShowVisuals] = useState(false);
  const [selectedYear, setSelectedYear] = useState("all");
  const [activeView, setActiveView] = useState("analyst");
  const [segmentation, setSegmentation] = useState(null);
  const [segmentationLoading, setSegmentationLoading] = useState(false);
  const [segmentationError, setSegmentationError] = useState("");
  const [selectedSegment, setSelectedSegment] = useState("");
  const [segmentCustomers, setSegmentCustomers] = useState([]);
  const [segmentCustomersLoading, setSegmentCustomersLoading] = useState(false);
  const [segmentCustomersError, setSegmentCustomersError] = useState("");
  const segmentRequestId = useRef(0);

  const [returnRisk, setReturnRisk] = useState(null);
  const [returnRiskLoading, setReturnRiskLoading] = useState(false);
  const [returnRiskError, setReturnRiskError] = useState("");


  const askQuestion = async (
    presetQuestion = null
  ) => {
    const finalQuestion =
      presetQuestion || question;

    if (!finalQuestion.trim()) {
      return;
    }

    setQuestion(finalQuestion);
    setLoading(true);
    setError("");
    setResult(null);
    setShowVisuals(false);
    setSelectedYear("all");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/ask",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            question: finalQuestion,
          }),
        }
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.error ||
            "DecisionIQ could not complete the analysis."
        );
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };


  const loadSegmentation = async () => {
    if (segmentation || segmentationLoading) {
      return;
    }

    setSegmentationLoading(true);
    setSegmentationError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/analytics/customer-segmentation"
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.error ||
            "Customer segmentation could not be loaded."
        );
      }

      setSegmentation(data);
    } catch (err) {
      setSegmentationError(err.message);
    } finally {
      setSegmentationLoading(false);
    }
  };


  const loadSegmentCustomers = async (segment) => {
    const requestId = ++segmentRequestId.current;

    setSelectedSegment(segment);
    setSegmentCustomers([]);
    setSegmentCustomersError("");
    setSegmentCustomersLoading(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/analytics/customer-segmentation/customers?segment=${encodeURIComponent(
          segment
        )}&limit=100`
      );

      const data = await response.json();

      // Ignore an older response if the user clicked another segment.
      if (requestId !== segmentRequestId.current) {
        return;
      }

      if (!data.success) {
        throw new Error(
          data.error ||
            "Customer list could not be loaded."
        );
      }

      if (data.segment !== segment) {
        throw new Error(
          "The returned customer segment did not match the selected segment."
        );
      }

      setSegmentCustomers(data.customers || []);
    } catch (err) {
      if (requestId === segmentRequestId.current) {
        setSegmentCustomersError(err.message);
      }
    } finally {
      if (requestId === segmentRequestId.current) {
        setSegmentCustomersLoading(false);
      }
    }
  };


  const downloadSegmentCsv = async () => {
    if (!selectedSegment) {
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/analytics/customer-segmentation/customers?segment=${encodeURIComponent(
          selectedSegment
        )}&limit=15000`
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.error ||
            "Customer CSV could not be prepared."
        );
      }

      const rows = data.customers || [];

      if (!rows.length) {
        throw new Error(
          "No customers were found for this segment."
        );
      }

      const columns = Object.keys(rows[0]);

      const escapeCsv = (value) => {
        if (value === null || value === undefined) {
          return "";
        }

        const stringValue = String(value);

        if (
          stringValue.includes(",") ||
          stringValue.includes('"') ||
          stringValue.includes("\n")
        ) {
          return `"${stringValue.replaceAll('"', '""')}"`;
        }

        return stringValue;
      };

      const csv = [
        columns.join(","),
        ...rows.map((row) =>
          columns
            .map((column) => escapeCsv(row[column]))
            .join(",")
        ),
      ].join("\n");

      const blob = new Blob(
        [csv],
        { type: "text/csv;charset=utf-8;" }
      );

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `${selectedSegment
        .toLowerCase()
        .replaceAll(" ", "_")}_customers.csv`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setSegmentCustomersError(err.message);
    }
  };


  const loadReturnRisk = async () => {
    if (returnRisk || returnRiskLoading) {
      return;
    }

    setReturnRiskLoading(true);
    setReturnRiskError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/analytics/return-risk"
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.error ||
            "Return risk model could not be loaded."
        );
      }

      setReturnRisk(data);
    } catch (err) {
      setReturnRiskError(err.message);
    } finally {
      setReturnRiskLoading(false);
    }
  };


  const downloadHighRiskCsv = () => {
    const rows = returnRisk?.high_risk_items || [];

    if (!rows.length) {
      return;
    }

    const columns = Object.keys(rows[0]);

    const escapeCsv = (value) => {
      if (value === null || value === undefined) {
        return "";
      }

      const stringValue = String(value);

      if (
        stringValue.includes(",") ||
        stringValue.includes('"') ||
        stringValue.includes("\n")
      ) {
        return `"${stringValue.replaceAll('"', '""')}"`;
      }

      return stringValue;
    };

    const csv = [
      columns.join(","),
      ...rows.map((row) =>
        columns
          .map((column) => escapeCsv(row[column]))
          .join(",")
      ),
    ].join("\n");

    const blob = new Blob(
      [csv],
      { type: "text/csv;charset=utf-8;" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "high_risk_return_items.csv";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };


  const openView = (view) => {
    setActiveView(view);

    if (view === "data-science") {
      loadSegmentation();
      loadReturnRisk();
    }
  };


  const renderSegmentationDashboard = () => {
    if (segmentationLoading) {
      return (
        <div className="loading-panel">
          <div className="loading-header">
            <span className="loader"></span>
            <div>
              <strong>Loading data science models</strong>
              <p>Building the customer segmentation view.</p>
            </div>
          </div>
          <div className="skeleton"></div>
          <div className="skeleton"></div>
        </div>
      );
    }

    if (segmentationError) {
      return (
        <div className="error-panel">
          <div className="error-icon">!</div>
          <div>
            <strong>Data Science module unavailable</strong>
            <p>{segmentationError}</p>
          </div>
        </div>
      );
    }

    if (!segmentation) {
      return null;
    }

    const profiles = segmentation.cluster_profile || [];
    const values = segmentation.segment_value || [];
    const scoreEntries = Object.entries(
      segmentation.silhouette_scores || {}
    ).map(([k, score]) => ({
      k: `K=${k}`,
      score: Number(score),
    }));

    const segmentColors = [
      CHART_COLORS.danger,
      CHART_COLORS.secondary,
      CHART_COLORS.primary,
    ];

    const segmentBubbleData = profiles.map((profile) => ({
      ...profile,
      avg_recency: Number(profile.avg_recency),
      avg_monetary: Number(profile.avg_monetary),
      customers: Number(profile.customers),
    }));

    const topFeatureData = (returnRisk?.feature_importance || [])
      .slice(0, 8)
      .map((item) => ({
        ...item,
        display_feature: cleanFeatureLabel(item.feature),
      }));

    const riskTableData = cleanRiskTableRows(
      returnRisk?.high_risk_items || []
    );

    return (
      <div className="results ds-dashboard">
        <section className="ds-summary-grid">
          {values.map((segment) => (
            <article
              className="panel ds-segment-card"
              key={segment.segment}
            >
              <span className="section-label">
                CUSTOMER SEGMENT
              </span>
              <h3>{segment.segment}</h3>
              <strong className="ds-big-number">
                {segment.customers.toLocaleString("en-IN")}
              </strong>
              <span className="ds-card-caption">customers</span>
              <div className="ds-card-metric">
                <span>Value share</span>
                <b>{segment.value_share_pct.toFixed(1)}%</b>
              </div>
              <div className="ds-card-metric">
                <span>Avg. monetary</span>
                <b>{formatChartAxis(segment.avg_monetary, "monetary")}</b>
              </div>

              <button
                className="segment-customer-button"
                type="button"
                onClick={() =>
                  loadSegmentCustomers(segment.segment)
                }
              >
                View Customers
              </button>
            </article>
          ))}
        </section>

        <section className="panel ds-model-card">
          <div className="section-heading">
            <div>
              <span className="section-label">MODEL QUALITY</span>
              <h3>K-Means Customer Segmentation</h3>
            </div>
            <div className="ds-model-badge">
              Best K = {segmentation.best_k}
            </div>
          </div>

          <div className="ds-model-copy">
            The model selected {segmentation.best_k} clusters using the
            highest silhouette score across K=2 to K=6.
          </div>

          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart
                data={scoreEntries}
                margin={{ top: 10, right: 20, left: 4, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e8ebf2"
                />
                <XAxis
                  dataKey="k"
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 0.5]}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => Number(value).toFixed(3)}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  name="Silhouette Score"
                  stroke={CHART_COLORS.primary}
                  strokeWidth={3}
                  dot={{ r: 5 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel chart-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">VALUE DISTRIBUTION</span>
              <h3>Customer Value Share by Segment</h3>
            </div>
          </div>

          <div className="donut-layout">
            <div className="chart-wrapper donut-chart">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={values}
                    dataKey="value_share_pct"
                    nameKey="segment"
                    cx="50%"
                    cy="50%"
                    innerRadius={76}
                    outerRadius={112}
                    paddingAngle={3}
                  >
                    {values.map((entry, index) => (
                      <Cell
                        key={entry.segment}
                        fill={segmentColors[index % segmentColors.length]}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    formatter={(value) =>
                      `${Number(value).toFixed(1)}%`
                    }
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="donut-legend">
              {values.map((segment, index) => (
                <div
                  className="donut-legend-row"
                  key={segment.segment}
                >
                  <span
                    className="donut-legend-dot"
                    style={{
                      background:
                        segmentColors[
                          index % segmentColors.length
                        ],
                    }}
                  />

                  <div>
                    <strong>{segment.segment}</strong>
                    <span>
                      {segment.value_share_pct.toFixed(1)}% of value
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="panel chart-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">SEGMENT MAP</span>
              <h3>Customer Segment Positioning</h3>
            </div>
          </div>

          <p className="ds-model-copy">
            Recency is shown on the horizontal axis, average monetary
            value on the vertical axis, and bubble size represents the
            number of customers in each segment.
          </p>

          <div className="chart-wrapper segment-bubble-chart">
            <ResponsiveContainer width="100%" height={360}>
              <ScatterChart
                margin={{ top: 20, right: 35, bottom: 28, left: 26 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e8ebf2"
                />

                <XAxis
                  type="number"
                  dataKey="avg_recency"
                  name="Avg Recency"
                  unit=" days"
                  axisLine={false}
                  tickLine={false}
                />

                <YAxis
                  type="number"
                  dataKey="avg_monetary"
                  name="Avg Monetary"
                  width={86}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value) =>
                    formatChartAxis(value, "monetary")
                  }
                />

                <ZAxis
                  type="number"
                  dataKey="customers"
                  range={[280, 1200]}
                  name="Customers"
                />

                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  formatter={(value, name) => {
                    if (name === "Avg Monetary") {
                      return [
                        formatChartAxis(value, "monetary"),
                        name,
                      ];
                    }

                    if (name === "Avg Recency") {
                      return [`${Number(value).toFixed(0)} days`, name];
                    }

                    return [Number(value).toLocaleString("en-IN"), name];
                  }}
                />

                {segmentBubbleData.map((segment, index) => (
                  <Scatter
                    key={segment.segment}
                    name={segment.segment}
                    data={[segment]}
                    fill={
                      segmentColors[
                        index % segmentColors.length
                      ]
                    }
                  />
                ))}

                <Legend />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </section>


        {selectedSegment && (
          <section className="panel compact-panel targeting-panel">
            <div className="section-heading">
              <div>
                <span className="section-label">TARGETING LIST</span>
                <h3>{selectedSegment} Customers</h3>
              </div>

              <div className="targeting-actions">
                <button
                  className="download-csv-button"
                  type="button"
                  onClick={downloadSegmentCsv}
                  disabled={segmentCustomersLoading}
                >
                  Download CSV
                </button>

                <button
                  className="targeting-close-button"
                  type="button"
                  onClick={() => {
                    segmentRequestId.current += 1;
                    setSelectedSegment("");
                    setSegmentCustomers([]);
                    setSegmentCustomersError("");
                    setSegmentCustomersLoading(false);
                  }}
                >
                  Close
                </button>
              </div>
            </div>

            <p className="targeting-copy">
              Showing the top 100 customers in this segment ranked by monetary value.
              Download CSV exports the full segment for campaign targeting or downstream CRM workflows.
            </p>

            {segmentCustomersLoading && (
              <div className="targeting-loading">
                Loading customer list...
              </div>
            )}

            {segmentCustomersError && (
              <div className="targeting-error">
                {segmentCustomersError}
              </div>
            )}

            {!segmentCustomersLoading &&
              !segmentCustomersError &&
              segmentCustomers.length > 0 && (
                <DataTable data={segmentCustomers} />
              )}
          </section>
        )}

        <section className="panel risk-model-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">PREDICTIVE MODEL</span>
              <h3>Experimental Return Risk Model</h3>
            </div>

            {returnRisk?.best_model_name && (
              <div className="ds-model-badge">
                Best: {returnRisk.best_model_name}
              </div>
            )}
          </div>

          <p className="ds-model-copy">
            Predicts item-level return risk using transaction, category,
            and historical customer behavior. Performance is moderate,
            so use this as a prioritization signal rather than a production decision rule.
          </p>

          {returnRiskLoading && (
            <div className="targeting-loading">
              Loading return risk model...
            </div>
          )}

          {returnRiskError && (
            <div className="targeting-error">
              {returnRiskError}
            </div>
          )}

          {returnRisk && (
            <>
              <div className="risk-metric-grid">
                <div className="risk-metric-card">
                  <span>ROC-AUC</span>
                  <strong>{returnRisk.best_metrics.roc_auc.toFixed(3)}</strong>
                </div>

                <div className="risk-metric-card">
                  <span>Precision</span>
                  <strong>
                    {(returnRisk.best_metrics.precision * 100).toFixed(1)}%
                  </strong>
                </div>

                <div className="risk-metric-card">
                  <span>Recall</span>
                  <strong>
                    {(returnRisk.best_metrics.recall * 100).toFixed(1)}%
                  </strong>
                </div>

                <div className="risk-metric-card">
                  <span>F1 Score</span>
                  <strong>{returnRisk.best_metrics.f1.toFixed(3)}</strong>
                </div>
              </div>

              <div className="risk-chart-grid">
                <div>
                  <h4>Model Comparison</h4>

                  <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart
                        data={Object.entries(
                          returnRisk.model_metrics
                        ).map(([model, metrics]) => ({
                          model,
                          roc_auc: metrics.roc_auc,
                          f1: metrics.f1,
                        }))}
                        barCategoryGap="30%"
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          vertical={false}
                          stroke="#e8ebf2"
                        />
                        <XAxis
                          dataKey="model"
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          domain={[0, 1]}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip />
                        <Legend />

                        <Bar
                          dataKey="roc_auc"
                          name="ROC-AUC"
                          fill={CHART_COLORS.primary}
                          radius={[5, 5, 0, 0]}
                        />
                        <Bar
                          dataKey="f1"
                          name="F1"
                          fill={CHART_COLORS.secondary}
                          radius={[5, 5, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div>
                  <h4>Top Predictive Features</h4>

                  <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height={330}>
                      <BarChart
                        data={topFeatureData}
                        layout="vertical"
                        margin={{ top: 4, right: 18, bottom: 4, left: 18 }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          horizontal={false}
                          stroke="#e8ebf2"
                        />
                        <XAxis
                          type="number"
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          type="category"
                          dataKey="display_feature"
                          width={185}
                          tick={{ fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip />

                        <Bar
                          dataKey="importance"
                          name="Importance"
                          fill={CHART_COLORS.accent}
                          radius={[0, 5, 5, 0]}
                          maxBarSize={24}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="risk-table-header">
                <div>
                  <span className="section-label">HIGH-RISK ITEMS</span>
                  <h4>Highest Predicted Return Risk</h4>
                </div>

                <button
                  className="download-csv-button"
                  type="button"
                  onClick={downloadHighRiskCsv}
                >
                  Download CSV
                </button>
              </div>

              <p className="risk-table-note">
                Showing the most useful fields on-screen. The CSV keeps
                the complete model output and historical features.
              </p>

              <DataTable data={riskTableData} />
            </>
          )}
        </section>


        <section className="panel compact-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">SEGMENT PROFILE</span>
              <h3>RFM Summary</h3>
            </div>
          </div>
          <DataTable data={profiles} />
        </section>
      </div>
    );
  };


  const renderCharts = () => {
    if (
      !showVisuals ||
      !result?.charts ||
      result.charts.length === 0
    ) {
      return null;
    }

    return result.charts.map(
      (chart, index) => {
        const rawData =
          chart.data ||
          (Array.isArray(result.data)
            ? result.data
            : []);

        const data = Array.isArray(rawData)
          ? filterDataByYear(
              rawData,
              chart.x,
              selectedYear
            )
          : rawData;

        if (
          chart.type === "bar" &&
          Array.isArray(data)
        ) {
          return (
            <section
              className="panel chart-panel"
              key={`${chart.title}-${index}`}
            >
              <div className="section-heading">
                <div>
                  <span className="section-label">
                    VISUAL ANALYSIS
                  </span>

                  <h3>{chart.title}</h3>
                </div>
              </div>

              <div className="chart-wrapper">
                <ResponsiveContainer
                  width="100%"
                  height={300}
                >
                  <BarChart
                    data={data}
                    barCategoryGap="28%"
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e8ebf2"
                    />

                    <XAxis
                      dataKey={chart.x}
                      axisLine={false}
                      tickLine={false}
                      interval={0}
                      tick={{
                        fontSize: 11,
                        fill: "#64748b",
                      }}
                    />

                    <YAxis
                      width={82}
                      axisLine={false}
                      tickLine={false}
                      tick={{
                        fontSize: 10,
                        fill: "#94a3b8",
                      }}
                      tickFormatter={(value) =>
                        formatChartAxis(
                          value,
                          chart.y
                        )
                      }
                    />

                    <Tooltip
                      content={
                        <CustomTooltip />
                      }
                    />

                    <Bar
                      dataKey={chart.y}
                      name={
                        chart.y_label ||
                        chart.y
                      }
                      fill={
                        CHART_COLORS.primary
                      }
                      radius={[
                        6,
                        6,
                        0,
                        0,
                      ]}
                      maxBarSize={65}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          );
        }


        if (
          chart.type ===
            "horizontal_bar" &&
          Array.isArray(data)
        ) {
          return (
            <section
              className="panel chart-panel"
              key={`${chart.title}-${index}`}
            >
              <div className="section-heading">
                <div>
                  <span className="section-label">
                    RANKING
                  </span>

                  <h3>{chart.title}</h3>
                </div>
              </div>

              <div className="chart-wrapper">
                <ResponsiveContainer
                  width="100%"
                  height={Math.max(
                    280,
                    data.length * 48
                  )}
                >
                  <BarChart
                    data={data}
                    layout="vertical"
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                      stroke="#e8ebf2"
                    />

                    <XAxis
                      type="number"
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value) =>
                        formatChartAxis(
                          value,
                          chart.y
                        )
                      }
                    />

                    <YAxis
                      type="category"
                      dataKey={chart.x}
                      width={130}
                      axisLine={false}
                      tickLine={false}
                    />

                    <Tooltip
                      content={
                        <CustomTooltip />
                      }
                    />

                    <Bar
                      dataKey={chart.y}
                      name={
                        chart.y_label ||
                        chart.y
                      }
                      fill={
                        CHART_COLORS.secondary
                      }
                      radius={[
                        0,
                        6,
                        6,
                        0,
                      ]}
                      maxBarSize={28}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          );
        }


        if (
          chart.type ===
            "grouped_bar" &&
          Array.isArray(data)
        ) {
          return (
            <section
              className="panel chart-panel"
              key={`${chart.title}-${index}`}
            >
              <div className="section-heading">
                <div>
                  <span className="section-label">
                    COMPARISON
                  </span>

                  <h3>{chart.title}</h3>
                </div>
              </div>

              <div className="chart-wrapper">
                <ResponsiveContainer
                  width="100%"
                  height={310}
                >
                  <BarChart
                    data={data}
                    barCategoryGap="25%"
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e8ebf2"
                    />

                    <XAxis
                      dataKey={chart.x}
                      axisLine={false}
                      tickLine={false}
                    />

                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value) =>
                        chart.format ===
                        "percent"
                          ? `${value.toFixed(
                              0
                            )}%`
                          : formatChartAxis(
                              value
                            )
                      }
                    />

                    <Tooltip
                      content={
                        <CustomTooltip />
                      }
                    />

                    <Legend />

                    {chart.series.map(
                      (
                        series,
                        seriesIndex
                      ) => (
                        <Bar
                          key={
                            series.key
                          }
                          dataKey={
                            series.key
                          }
                          name={
                            series.label
                          }
                          fill={
                            SERIES_PALETTE[
                              seriesIndex %
                                SERIES_PALETTE.length
                            ]
                          }
                          radius={[
                            5,
                            5,
                            0,
                            0,
                          ]}
                          maxBarSize={45}
                        />
                      )
                    )}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          );
        }


        if (
          chart.type === "line" &&
          Array.isArray(data)
        ) {
          return (
            <section
              className="panel chart-panel"
              key={`${chart.title}-${index}`}
            >
              <div className="section-heading">
                <div>
                  <span className="section-label">
                    TREND
                  </span>

                  <h3>{chart.title}</h3>
                </div>
              </div>

              <div className="chart-wrapper">
                <ResponsiveContainer
                  width="100%"
                  height={310}
                >
                  <LineChart data={data}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e8ebf2"
                    />

                    <XAxis
                      dataKey={chart.x}
                      axisLine={false}
                      tickLine={false}
                    />

                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={
                        formatChartAxis
                      }
                    />

                    <Tooltip
                      content={
                        <CustomTooltip />
                      }
                    />

                    <Legend />

                    {chart.series.map(
                      (
                        series,
                        seriesIndex
                      ) => (
                        <Line
                          key={
                            series.key
                          }
                          type="monotone"
                          dataKey={
                            series.key
                          }
                          name={
                            series.label
                          }
                          stroke={
                            SERIES_PALETTE[
                              seriesIndex %
                                SERIES_PALETTE.length
                            ]
                          }
                          strokeWidth={2.5}
                          dot={{
                            r: 3,
                            fill:
                              SERIES_PALETTE[
                                seriesIndex %
                                  SERIES_PALETTE.length
                              ],
                          }}
                          activeDot={{
                            r: 5,
                          }}
                        />
                      )
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
          );
        }


        if (
          chart.type === "kpi" &&
          data &&
          !Array.isArray(data)
        ) {
          return (
            <section
              className="panel"
              key={`${chart.title}-${index}`}
            >
              <div className="section-heading">
                <div>
                  <span className="section-label">
                    SCENARIO
                  </span>

                  <h3>{chart.title}</h3>
                </div>
              </div>

              <div className="kpi-grid">
                {chart.metrics.map(
                  (metric) => (
                    <div
                      className="kpi-card"
                      key={metric}
                    >
                      <span>
                        {metric.replaceAll(
                          "_",
                          " "
                        )}
                      </span>

                      <strong>
                        {formatNumber(
                          data[metric],
                          metric
                        )}
                      </strong>
                    </div>
                  )
                )}
              </div>
            </section>
          );
        }

        return null;
      }
    );
  };


  const availableYears = Array.from(
    new Set(
      (result?.charts || [])
        .flatMap((chart) => {
          const chartData =
            chart.data ||
            (Array.isArray(result?.data)
              ? result.data
              : []);

          if (!Array.isArray(chartData) || !chart.x) {
            return [];
          }

          return chartData
            .map((row) => extractYear(row?.[chart.x]))
            .filter(Boolean);
        })
    )
  ).sort((a, b) => a - b);


  const exampleQuestions = [
    "Why is mobile conversion lower than desktop?",
    "Which category drives the highest gross profit?",
    "What happens if discounts increase to 25%?",
    "Were there unusual revenue or refund anomalies over time?",
    "Which marketing channel has the highest ROAS?",
  ];


  return (
    <div className="app-shell">
      <aside className="sidebar">

        <div>
          <div className="brand">
            <div className="brand-icon">
              <span></span>
            </div>

            <div>
              <h1>DecisionIQ</h1>
              <p>Decision Intelligence</p>
            </div>
          </div>


          <div className="nav-section">
            <span className="nav-label">
              ANALYTICS ENGINE
            </span>

            <button
              className={`nav-item nav-button ${
                activeView === "analyst" ? "active" : ""
              }`}
              type="button"
              onClick={() => openView("analyst")}
            >
              AI Analyst
            </button>

            <button
              className={`nav-item nav-button ${
                activeView === "data-science" ? "active" : ""
              }`}
              type="button"
              onClick={() => openView("data-science")}
            >
              Data Science
            </button>
          </div>
        </div>


        <div className="sidebar-status">
          <div className="status-row">
            <span className="status-dot"></span>
            API Connected
          </div>

          <span className="status-subtext">
            DecisionIQ Backend
          </span>
        </div>

      </aside>


      <main className="main-content">

        <header className="topbar">
          <div>
            <span className="topbar-label">
              {activeView === "analyst"
                ? "AI BUSINESS ANALYST"
                : "DATA SCIENCE"}
            </span>

            <h2>
              {activeView === "analyst"
                ? "Ask your business data anything."
                : "Customer intelligence powered by machine learning."}
            </h2>

            <p>
              {activeView === "analyst"
                ? "DecisionIQ turns natural-language questions into SQL, analysis, simulations, and actionable business insights."
                : "Explore customer segments, model quality, value concentration, and behavioral profiles without using AI tokens."}
            </p>
          </div>

          <div className="live-pill">
            <span className="status-dot"></span>
            Live
          </div>
        </header>


        {activeView === "analyst" ? (
          <>
        <section className="query-panel">
          <textarea
            placeholder="Ask about revenue, profitability, conversion, customers, marketing, discounts, or anomalies..."
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !loading
              ) {
                e.preventDefault();

                askQuestion();
              }
            }}
          />

          <div className="query-actions">
            <span>
              Enter to analyze · Shift + Enter
              for a new line
            </span>

            <button
              onClick={() =>
                askQuestion()
              }
              disabled={loading}
            >
              {loading
                ? "Analyzing..."
                : "Ask DecisionIQ"}
            </button>
          </div>
        </section>


        <section className="prompt-section">

          <span>
            Try an example
          </span>

          <div className="prompt-chips">

            {exampleQuestions.map(
              (item) => (
                <button
                  key={item}
                  onClick={() =>
                    askQuestion(item)
                  }
                  disabled={loading}
                >
                  {item}
                </button>
              )
            )}

          </div>

        </section>


        {!result &&
          !loading &&
          !error && (
            <section className="empty-state">

              <span className="empty-dot"></span>

              <h3>
                Your AI analyst is ready.
              </h3>

              <p>
                Ask a business question and
                DecisionIQ will choose the
                appropriate analytical approach.
              </p>

            </section>
          )}


        {loading && (
          <div className="loading-panel">

            <div className="loading-header">
              <span className="loader"></span>

              <div>
                <strong>
                  DecisionIQ is analyzing
                </strong>

                <p>
                  Running the appropriate
                  analytics and preparing your
                  insight.
                </p>
              </div>
            </div>

            <div className="skeleton"></div>
            <div className="skeleton"></div>
            <div className="skeleton skeleton-short"></div>

          </div>
        )}


        {error && (
          <div className="error-panel">

            <div className="error-icon">
              !
            </div>

            <div>
              <strong>
                AI temporarily unavailable
              </strong>

              <p>{error}</p>
            </div>

          </div>
        )}


        {result && (
          <div className="results">

            <section className="panel insight-panel">

              <div className="section-heading">
                <div>
                  <span className="section-label">
                    AI INSIGHT
                  </span>

                  <h3>
                    DecisionIQ Analysis
                  </h3>
                </div>
              </div>

              <div className="markdown-body">

                <ReactMarkdown
                  remarkPlugins={[
                    remarkGfm,
                  ]}
                >
                  {result.answer}
                </ReactMarkdown>

              </div>

            </section>


            {result?.charts?.length > 0 && (
              <section className="visual-controls">
                <div>
                  <span className="section-label">
                    VISUALIZATION
                  </span>

                  <p className="visual-controls-copy">
                    Explore the returned data interactively.
                  </p>
                </div>

                <div className="visual-controls-actions">
                  {showVisuals &&
                    availableYears.length > 0 && (
                      <label className="year-filter">
                        <span>Date</span>

                        <select
                          value={selectedYear}
                          onChange={(e) =>
                            setSelectedYear(e.target.value)
                          }
                        >
                          <option value="all">
                            All dates
                          </option>

                          {availableYears.map((year) => (
                            <option
                              key={year}
                              value={String(year)}
                            >
                              {year}
                            </option>
                          ))}
                        </select>
                      </label>
                    )}

                  <button
                    className="visualize-button"
                    type="button"
                    onClick={() =>
                      setShowVisuals((current) => !current)
                    }
                  >
                    {showVisuals
                      ? "Hide visuals"
                      : "Visualize"}
                  </button>
                </div>
              </section>
            )}

            {renderCharts()}


            <section className="panel compact-panel">

              <details>

                <summary>
                  View underlying data
                </summary>

                {Array.isArray(
                  result.data
                ) ? (
                  <DataTable
                    data={result.data}
                  />
                ) : (
                  <pre>
                    {JSON.stringify(
                      result.data,
                      null,
                      2
                    )}
                  </pre>
                )}

              </details>

            </section>


            {result.sql && (
              <section className="panel compact-panel">

                <details>

                  <summary>
                    View generated SQL
                  </summary>

                  <pre className="sql-block">
                    {result.sql}
                  </pre>

                </details>

              </section>
            )}

          </div>
        )}
          </>
        ) : (
          renderSegmentationDashboard()
        )}

      </main>
    </div>
  );
}


export default App;