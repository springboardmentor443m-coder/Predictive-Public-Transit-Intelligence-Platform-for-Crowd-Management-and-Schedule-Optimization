import { describe, expect, it } from "vitest";
import { dualClock, istClock, nycClock, nycDateHourLabel, nycHourLabel } from "../lib/time";

describe("nycClock", () => {
  it("reports the correct New York wall-clock hour across the UTC day boundary", () => {
    // 2026-07-01T18:30:00Z is 14:30 in New York (EDT, UTC-4).
    const c = nycClock(new Date("2026-07-01T18:30:00Z"));
    expect(c.time).toBe("14:30:00");
    expect(c.zone).toBe("EDT");
    expect(c.offset).toBe("UTC-4");
  });

  it("switches to EST and UTC-5 in winter", () => {
    // 2026-01-15T18:30:00Z is 13:30 in New York (EST, UTC-5).
    const c = nycClock(new Date("2026-01-15T18:30:00Z"));
    expect(c.time).toBe("13:30:00");
    expect(c.zone).toBe("EST");
    expect(c.offset).toBe("UTC-5");
  });

  it("rolls the date over correctly for a late-evening NYC hour", () => {
    // 2026-07-02T02:00:00Z is still 22:00 on 1 July in New York.
    const c = nycClock(new Date("2026-07-02T02:00:00Z"));
    expect(c.time).toBe("22:00:00");
  });
});

describe("istClock", () => {
  it("is always UTC+5:30 with no daylight saving", () => {
    expect(istClock(new Date("2026-07-01T18:30:00Z")).time).toBe("00:00:00");
    expect(istClock(new Date("2026-01-15T18:30:00Z")).time).toBe("00:00:00");
    for (const d of ["2026-01-15T18:30:00Z", "2026-07-01T18:30:00Z"]) {
      expect(istClock(new Date(d)).zone).toBe("IST");
      expect(istClock(new Date(d)).offset).toBe("UTC+5:30");
    }
  });
});

describe("dualClock", () => {
  it("keeps NYC 9h30m behind IST during EDT", () => {
    const { ist, nyc } = dualClock(new Date("2026-07-01T18:30:00Z"));
    expect(nyc.time).toBe("14:30:00");
    expect(ist.time).toBe("00:00:00");
  });

  it("keeps NYC 10h30m behind IST during EST", () => {
    const { ist, nyc } = dualClock(new Date("2026-01-15T18:30:00Z"));
    expect(nyc.time).toBe("13:30:00");
    expect(ist.time).toBe("00:00:00");
  });
});

describe("chart axis labels", () => {
  it("labels data hours in New York time, not the viewer's timezone", () => {
    // A 07:00 NYC hour must render as 07:00 on the axis even though the runtime
    // timezone may be IST - this is the whole point of the helper.
    expect(nycHourLabel(new Date("2026-07-01T11:00:00Z"))).toBe("07:00");
    expect(nycHourLabel(new Date("2026-01-01T12:00:00Z"))).toBe("07:00");
  });

  it("includes the day and month for tooltips", () => {
    expect(nycDateHourLabel(new Date("2026-07-01T11:00:00Z"))).toBe("01 Jul, 07:00");
  });
});