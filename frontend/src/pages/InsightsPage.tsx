import { useEffect, type ReactNode } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, Banknote, ChartColumn, Info, Users } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { useFetch } from "../api";
import { labelFor, useReference } from "../context";
import { formatCount, formatMoney, formatPercent, percentDelta } from "../lib/format";
import { useCountUp } from "../lib/hooks";
import type { CountryInsights, Overview, TitleInsights } from "../types";

export function InsightsPage() {
  const reference = useReference();
  const [params, setParams] = useSearchParams();
  const country = params.get("country") ?? "";
  const title = params.get("title") ?? "";
  const terminated = params.get("terminated") === "1";
  const overview = useFetch<Overview>(`/insights/overview?include_terminated=${terminated ? "true" : "false"}`);
  const detail = useFetch<CountryInsights>(
    country ? `/insights/country?country=${encodeURIComponent(country)}&include_terminated=${terminated ? "true" : "false"}` : null,
  );
  const titleStats = useFetch<TitleInsights>(
    country && title
      ? `/insights/job-title?country=${encodeURIComponent(country)}&job_title=${encodeURIComponent(title)}&include_terminated=${terminated ? "true" : "false"}`
      : null,
  );

  useEffect(() => {
    if (country || !overview.data?.countries.length) return;
    const next = new URLSearchParams(params);
    next.set("country", overview.data.countries[0].country);
    setParams(next, { replace: true });
  }, [country, overview.data, params, setParams]);

  const stats = detail.data?.country === country ? detail.data : null;
  const selectedTitle = titleStats.data?.country === country && titleStats.data.job_title === title ? titleStats.data : null;

  useEffect(() => {
    if (!stats) return;
    const titles = stats.by_job_title;
    if (title && titles.some((item) => item.key === title)) return;
    const next = new URLSearchParams(params);
    if (titles[0]) next.set("title", titles[0].key);
    else next.delete("title");
    if ((next.get("title") ?? "") === title) return;
    setParams(next, { replace: true });
  }, [params, setParams, stats, title]);

  function setCountry(nextCountry: string) {
    const next = new URLSearchParams(params);
    next.set("country", nextCountry);
    next.delete("title");
    setParams(next);
  }

  function setTitle(nextTitle: string) {
    const next = new URLSearchParams(params);
    next.set("title", nextTitle);
    setParams(next);
  }

  const currency = stats?.currency ?? "USD";
  const delta = percentDelta(selectedTitle?.average, stats?.average);
  const maxBand = Math.max(1, ...(stats?.bands.map((band) => band.count) ?? [1]));
  const maxDept = Math.max(1, ...(stats?.by_department.map((item) => Number(item.average ?? 0)) ?? [1]));

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Compensation</p>
          <h1>Salary insights</h1>
          <p className="lede">
            Minimum, maximum, and average pay for one country, and the average for a job title in that country. Figures stay in the local currency.
          </p>
        </div>
        <label className="toggle">
          <input
            type="checkbox"
            checked={terminated}
            onChange={(event) => {
              const next = new URLSearchParams(params);
              if (event.target.checked) next.set("terminated", "1");
              else next.delete("terminated");
              setParams(next);
            }}
          />
          <span>Include terminated</span>
        </label>
      </header>

      {overview.error ? <ErrorNote message={overview.error} onRetry={overview.reload} /> : null}

      <div className="chip-row" role="listbox" aria-label="Countries">
        {(overview.data?.countries ?? []).map((item) => (
          <button
            key={`${item.country}-${item.currency}`}
            type="button"
            role="option"
            aria-selected={item.country === country && item.currency === (stats?.currency ?? item.currency)}
            className={item.country === country ? "chip chip-active" : "chip"}
            onClick={() => setCountry(item.country)}
          >
            <strong>{item.country}</strong>
            <span>
              {item.currency} · {formatCount(item.headcount)}
            </span>
          </button>
        ))}
        {overview.loading && !overview.data ? <div className="skeleton chip-skeleton" /> : null}
      </div>

      {!overview.loading && overview.data && overview.data.countries.length === 0 ? (
        <EmptyInsights />
      ) : null}

      {detail.error ? <ErrorNote message={detail.error} onRetry={detail.reload} /> : null}
      {stats?.excluded_currency_count ? (
        <p className="banner banner-warn">
          <Info size={16} /> {stats.excluded_currency_count} record{stats.excluded_currency_count === 1 ? "" : "s"} in {stats.country} use a different currency and are left out of these averages.
        </p>
      ) : null}

      {detail.loading && !stats ? <StatSkeleton /> : null}

      {stats ? (
        <section aria-live="polite" aria-busy={detail.loading}>
          <motion.div className="stat-grid" initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.05 } } }}>
            <Stat label="Minimum" amount={stats.minimum} currency={currency} icon={<ArrowDownRight size={16} />} />
            <Stat label="Maximum" amount={stats.maximum} currency={currency} icon={<ArrowUpRight size={16} />} />
            <Stat label="Average" amount={stats.average} currency={currency} icon={<ChartColumn size={16} />} featured />
            <Stat label="Median" amount={stats.median} currency={currency} icon={<Banknote size={16} />} />
          </motion.div>
          <div className="stat-grid stat-grid-secondary">
            <article className="stat">
              <span>Headcount</span>
              <strong>{formatCount(stats.headcount)}</strong>
              <small>
                {formatCount(stats.status_breakdown.active ?? 0)} active · {formatCount(stats.status_breakdown.on_leave ?? 0)} on leave
                {terminated ? ` · ${formatCount(stats.status_breakdown.terminated ?? 0)} terminated` : ""}
              </small>
            </article>
            <article className="stat">
              <span>Total payroll</span>
              <strong>{formatMoney(stats.total_payroll, currency)}</strong>
              <small>Sum of annual salaries</small>
            </article>
            <article className="stat">
              <span>25th percentile</span>
              <strong>{formatMoney(stats.p25, currency)}</strong>
              <small>Nearest rank</small>
            </article>
            <article className="stat">
              <span>75th percentile</span>
              <strong>{formatMoney(stats.p75, currency)}</strong>
              <small>Nearest rank</small>
            </article>
          </div>
          <p className="fine-print">
            <Users size={14} /> Includes {humanList(stats.included_statuses.map((status) => (status === "on_leave" ? "on-leave" : labelFor(reference.statuses, status).toLowerCase())))} employees in {stats.country}.
          </p>
        </section>
      ) : null}

      {stats && stats.headcount > 0 ? (
        <div className="split">
          <section className="panel title-panel">
            <header>
              <p className="eyebrow">Job title</p>
              <h2>Average salary for a title</h2>
            </header>
            <label className="field" htmlFor="title-select">
              <span className="field-label">Title in {stats.country}</span>
              <select id="title-select" value={title} onChange={(event) => setTitle(event.target.value)}>
                {stats.by_job_title.map((item) => (
                  <option key={item.key} value={item.key}>
                    {item.key}
                  </option>
                ))}
              </select>
            </label>
            {selectedTitle ? (
              <div className="title-result">
                <p>Average</p>
                <strong>{formatMoney(selectedTitle.average, selectedTitle.currency)}</strong>
                <ul>
                  <li>Minimum {formatMoney(selectedTitle.minimum, selectedTitle.currency)}</li>
                  <li>Maximum {formatMoney(selectedTitle.maximum, selectedTitle.currency)}</li>
                  <li>Median {formatMoney(selectedTitle.median, selectedTitle.currency)}</li>
                  <li>{formatCount(selectedTitle.headcount)} people</li>
                </ul>
                {delta != null ? (
                  <p className={delta >= 0 ? "delta delta-up" : "delta delta-down"}>
                    {delta >= 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                    {formatPercent(delta)} {delta >= 0 ? "above" : "below"} the {stats.country} average
                  </p>
                ) : null}
              </div>
            ) : titleStats.loading ? (
              <div className="skeleton title-skeleton" />
            ) : null}
          </section>

          <section className="panel">
            <header>
              <p className="eyebrow">Departments</p>
              <h2>Average by department</h2>
            </header>
            <div className="bars">
              {stats.by_department.map((item) => (
                <div key={item.key} className="bar-row">
                  <div className="bar-meta">
                    <span>{item.key}</span>
                    <strong>{formatMoney(item.average, currency)}</strong>
                  </div>
                  <div className="bar-track" aria-hidden="true">
                    <span style={{ width: `${(Number(item.average ?? 0) / maxDept) * 100}%` }} />
                  </div>
                  <small>
                    {formatCount(item.headcount)} · {formatMoney(item.minimum, currency)} to {formatMoney(item.maximum, currency)}
                  </small>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      {stats && stats.headcount > 0 ? (
        <div className="split">
          <section className="panel">
            <header>
              <p className="eyebrow">Distribution</p>
              <h2>Salary bands</h2>
            </header>
            <div className="hist" aria-hidden="true">
              {stats.bands.map((band) => (
                <div key={`${band.minimum}-${band.maximum}`} className="hist-col">
                  <div className="hist-bar" style={{ height: `${(band.count / maxBand) * 100}%` }} />
                  <span>{band.count}</span>
                </div>
              ))}
            </div>
            <ul className="band-legend">
              {stats.bands.map((band) => (
                <li key={`${band.minimum}-label`}>
                  {formatMoney(band.minimum, currency)} – {formatMoney(band.maximum, currency)}
                </li>
              ))}
            </ul>
          </section>
          <section className="panel">
            <header>
              <p className="eyebrow">Titles</p>
              <h2>Every title in {stats.country}</h2>
            </header>
            <div className="table-wrap">
              <table>
                <caption className="sr-only">Average salary by job title in {stats.country}</caption>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>People</th>
                    <th>Average</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.by_job_title.map((item) => (
                    <tr key={item.key} className={item.key === title ? "row-selected" : undefined} onClick={() => setTitle(item.key)}>
                      <td>{item.key}</td>
                      <td>{formatCount(item.headcount)}</td>
                      <td>{formatMoney(item.average, currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="type-row">
              {stats.by_employment_type.map((item) => (
                <span key={item.key}>
                  {labelFor(reference.employment_types, item.key)} · {formatMoney(item.average, currency)}
                </span>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

function humanList(items: string[]): string {
  if (items.length <= 1) return items[0] ?? "";
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

function Stat({
  label,
  amount,
  currency,
  icon,
  featured = false,
}: {
  label: string;
  amount: string | null;
  currency: string;
  icon: ReactNode;
  featured?: boolean;
}) {
  const numeric = amount == null ? 0 : Number(amount);
  const animated = useCountUp(numeric, amount != null);
  return (
    <motion.article className={featured ? "stat stat-feature" : "stat"} variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}>
      <span>
        {icon}
        {label}
      </span>
      <strong>{amount == null ? "—" : formatMoney(animated, currency)}</strong>
    </motion.article>
  );
}

function StatSkeleton() {
  return (
    <div className="stat-grid">
      {Array.from({ length: 4 }, (_, index) => (
        <div key={index} className="skeleton stat-skeleton" />
      ))}
    </div>
  );
}

function EmptyInsights() {
  return (
    <div className="empty">
      <ChartColumn size={28} />
      <h2>No salaries to summarize yet</h2>
      <p>Add employees, or run the seed script for a 10,000 person sample.</p>
    </div>
  );
}

function ErrorNote({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <p className="banner banner-error">
      {message}
      <button type="button" className="btn btn-ghost" onClick={onRetry}>
        Try again
      </button>
    </p>
  );
}
