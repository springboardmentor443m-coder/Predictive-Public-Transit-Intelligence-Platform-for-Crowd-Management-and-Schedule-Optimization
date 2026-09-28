/**
 * ModelBadge is the only place a user can tell whether predictions are coming
 * from a trained model or a hardcoded curve. It previously rendered a green
 * "Live Serving" badge unconditionally, so a missing or failing artifact looked
 * identical to a healthy one while the API was reporting the truth that the UI
 * discarded.
 *
 * These tests pin the honesty contract, not the styling.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import ModelBadge from "../components/ModelBadge";
import type { ModelInfo } from "../lib/types";

const healthy: ModelInfo = {
  city: "nyc",
  crowd: { algorithm: "XGBoost", loaded: true, degraded: false, is_kaggle: true, trained_on: "nyc", metrics: { r2: 0.981, mae: 0.029 } },
  demand: { algorithm: "XGBoost", loaded: true, degraded: false, is_kaggle: true, trained_on: "nyc", metrics: { r2: 0.969 } },
  delay: { algorithm: "XGBoost classifier + regressor", loaded: true, metrics: { auc: 0.733 } },
  datasets: { nyc: "eddeng/nyc-subway-traffic-data-20172021" },
};

describe("ModelBadge - healthy serving", () => {
  it("reports a healthy serving state", () => {
    render(<ModelBadge info={healthy} />);
    expect(screen.getByTestId("model-badge")).toHaveAttribute("data-serving-state", "healthy");
    expect(screen.getByText(/Live Serving/)).toBeInTheDocument();
    expect(screen.queryByTestId("model-degraded-banner")).not.toBeInTheDocument();
  });

  it("shows real metrics rather than n/a", () => {
    render(<ModelBadge info={healthy} />);
    expect(screen.getByText("0.981")).toBeInTheDocument();
    expect(screen.getByText("0.969")).toBeInTheDocument();
  });
});

describe("ModelBadge - degraded serving", () => {
  it("flags a model that failed to load", () => {
    const info: ModelInfo = {
      ...healthy,
      crowd: { algorithm: "Rule-based baseline", loaded: false, degraded: true, degraded_reason: "artifact not loaded" },
    };
    render(<ModelBadge info={info} />);
    expect(screen.getByTestId("model-badge")).toHaveAttribute("data-serving-state", "degraded");
    expect(screen.getByTestId("model-degraded-banner")).toBeInTheDocument();
    expect(screen.getByText(/Fallback Active/)).toBeInTheDocument();
    expect(screen.queryByText(/Live Serving/)).not.toBeInTheDocument();
  });

  it("flags a model that loaded but is failing at runtime", () => {
    // The dangerous case: `loaded` is still true, so a UI that only reads
    // `loaded` would show a green badge while the baseline curve answered.
    const info: ModelInfo = {
      ...healthy,
      demand: { algorithm: "Rule-based baseline", loaded: true, degraded: true, degraded_reason: "runtime fallback: ValueError" },
    };
    render(<ModelBadge info={info} />);
    expect(screen.getByTestId("model-badge")).toHaveAttribute("data-serving-state", "degraded");
    expect(screen.getByTestId("model-degraded-banner")).toBeInTheDocument();
    expect(screen.getByText(/runtime fallback: ValueError/)).toBeInTheDocument();
  });

  it("names the degraded task rather than a generic warning", () => {
    const info: ModelInfo = { ...healthy, crowd: { loaded: false, degraded: true } };
    render(<ModelBadge info={info} />);
    expect(screen.getByText(/Crowd model is not serving/)).toBeInTheDocument();
  });

  it("handles two degraded tasks with correct pluralisation", () => {
    const info: ModelInfo = {
      ...healthy,
      crowd: { loaded: false, degraded: true },
      demand: { loaded: false, degraded: true },
    };
    render(<ModelBadge info={info} />);
    expect(screen.getByText(/Crowd and Demand models are not serving/)).toBeInTheDocument();
  });

  it("marks that model's metrics as not describing served values", () => {
    const info: ModelInfo = { ...healthy, crowd: { loaded: false, degraded: true, metrics: { r2: 0.981 } } };
    render(<ModelBadge info={info} />);
    // The metric must not be presented as if it applied to current output.
    expect(screen.queryByText("0.981")).not.toBeInTheDocument();
    expect(screen.getAllByText("offline").length).toBeGreaterThan(0);
  });

  it("does not treat an omitted field as degraded", () => {
    // The API omitting `degraded` is not a claim of health, but it is not proof
    // of failure either. Only report what the backend actually reported.
    const info: ModelInfo = { city: "nyc", crowd: { algorithm: "XGBoost" } };
    render(<ModelBadge info={info} />);
    expect(screen.getByTestId("model-badge")).toHaveAttribute("data-serving-state", "healthy");
  });
});

describe("ModelBadge - no invented numbers", () => {
  it("renders n/a for absent metrics", () => {
    const info: ModelInfo = { city: "nyc", crowd: { loaded: true }, demand: { loaded: true } };
    render(<ModelBadge info={info} />);
    expect(screen.getAllByText("n/a").length).toBe(4);
  });

  it("renders n/a for a non-numeric metric instead of NaN", () => {
    const info: ModelInfo = {
      city: "nyc",
      crowd: { loaded: true, metrics: { r2: "not-a-number" as unknown as number } },
    };
    render(<ModelBadge info={info} />);
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });
});

describe("ModelBadge - loading state", () => {
  it("announces loading to assistive tech", () => {
    render(<ModelBadge info={null} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/Loading active AI model parameters/)).toBeInTheDocument();
  });
});
