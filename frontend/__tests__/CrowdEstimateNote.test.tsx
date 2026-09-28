import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import CrowdEstimateNote from "../components/CrowdEstimateNote";
import type { LiveCrowdSnapshot } from "../lib/types";

const base: LiveCrowdSnapshot = {
  station_id: "A001",
  station_name: "Times Sq-42 St",
  line: "A",
  occupancy: 300,
  capacity: 1000,
  occupancy_pct: 30,
  congestion_level: "low",
  inflow_rate: 2,
  outflow_rate: 2,
  last_updated: "2026-09-29T00:00:00Z",
};

describe("CrowdEstimateNote", () => {
  it("is empty when there is no live snapshot", () => {
    const { container } = render(<CrowdEstimateNote snapshot={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("explains an interpolated estimate with bucket and progress", () => {
    render(
      <CrowdEstimateNote
        snapshot={{
          ...base,
          is_estimate: true,
          granularity: "hourly_bucket_interpolated",
          bucket_start: "2026-09-29T00:00:00Z",
          hour_elapsed_pct: 45,
        }}
      />
    );
    expect(screen.getByText(/estimated from hourly bucket/i)).toBeInTheDocument();
    expect(screen.getByText(/through the hour/i)).toBeInTheDocument();
  });

  it("clamps the elapsed percentage to 0-100", () => {
    render(
      <CrowdEstimateNote
        snapshot={{ ...base, is_estimate: true, hour_elapsed_pct: 137 }}
      />
    );
    expect(screen.getByText(/100% through the hour/i)).toBeInTheDocument();
  });

  it("omits progress when it is missing", () => {
    render(<CrowdEstimateNote snapshot={{ ...base, is_estimate: true }} />);
    expect(screen.queryByText(/through the hour/i)).not.toBeInTheDocument();
  });

  it("labels a live value as a reading instead of an estimate", () => {
    render(<CrowdEstimateNote snapshot={{ ...base, is_estimate: false }} />);
    expect(screen.getByText(/live reading/i)).toBeInTheDocument();
  });

  it("ignores a malformed bucket timestamp instead of crashing", () => {
    render(
      <CrowdEstimateNote
        snapshot={{ ...base, is_estimate: true, bucket_start: "not-a-date" }}
      />
    );
    expect(screen.getByText(/estimated from hourly bucket/i)).toBeInTheDocument();
  });
});