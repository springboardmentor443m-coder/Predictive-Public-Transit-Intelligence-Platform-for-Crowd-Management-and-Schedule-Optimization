export interface CsvColumn<R> {
  key?: keyof R;
  label: string;
  get?: (row: R) => string | number | null | undefined;
}

export function toCsv<R>(rows: R[], columns: CsvColumn<R>[]): string {
  const esc = (v: string | number | null | undefined): string => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = columns.map((c) => esc(c.label)).join(",");
  const lines = rows.map((r) =>
    columns
      .map((c) => esc(typeof c.get === "function" ? c.get(r) : String(r[c.key as keyof R])))
      .join(",")
  );
  return [header, ...lines].join("\n");
}

export function downloadCsv<R>(filename: string, rows: R[], columns: CsvColumn<R>[]): void {
  const csv = toCsv(rows, columns);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}