import { formatCount, formatDate, formatMoney, formatPercent, percentDelta } from "./format";

describe("formatMoney", () => {
  it("renders an em dash for missing amounts", () => {
    expect(formatMoney(null, "USD")).toBe("—");
    expect(formatMoney("", "USD")).toBe("—");
    expect(formatMoney("nope", "USD")).toBe("—");
  });

  it("formats USD and JPY with the currency's own fraction digits", () => {
    expect(formatMoney("1840000.5", "USD")).toBe("$1,840,000.50");
    expect(formatMoney(1000, "JPY")).toBe("¥1,000");
  });
});

describe("dates and counts", () => {
  it("formats calendar dates without shifting the day", () => {
    expect(formatDate("2022-04-18")).toBe("Apr 18, 2022");
  });

  it("groups headcount", () => {
    expect(formatCount(10000)).toBe("10,000");
  });
});

describe("percentDelta", () => {
  it("compares a title average with the country average", () => {
    expect(percentDelta("110", "100")).toBeCloseTo(10);
    expect(percentDelta("90", "100")).toBeCloseTo(-10);
    expect(percentDelta(null, "100")).toBeNull();
    expect(percentDelta("10", "0")).toBeNull();
  });

  it("formats the absolute percent for display", () => {
    expect(formatPercent(12.44)).toBe("12%");
    expect(formatPercent(4.26)).toBe("4.3%");
  });
});
