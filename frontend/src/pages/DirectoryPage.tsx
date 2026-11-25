import { useEffect, useMemo, useState } from "react";
import { ArrowUpDown, ChevronLeft, ChevronRight, Pencil, Plus, Search, Trash2, Users } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { ApiError, api, useFetch } from "../api";
import { Modal } from "../components/Modal";
import { EmployeeForm } from "../components/EmployeeForm";
import { labelFor, useReference, useToast } from "../context";
import { formatCount, formatDate, formatMoney } from "../lib/format";
import { useDebounced, useMediaQuery } from "../lib/hooks";
import type { Employee, EmployeeInput, EmployeeList } from "../types";

const SORTS = [
  ["full_name", "Name"],
  ["job_title", "Role"],
  ["country", "Location"],
  ["salary", "Salary"],
  ["hire_date", "Hired"],
] as const;

export function DirectoryPage() {
  const reference = useReference();
  const toast = useToast();
  const compact = useMediaQuery("(max-width: 860px)");
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const debounced = useDebounced(query, 250);
  const [draft, setDraft] = useState<Employee | "new" | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Employee | null>(null);
  const [busy, setBusy] = useState(false);
  const [serverFields, setServerFields] = useState<Record<string, string>>({});
  const [serverMessage, setServerMessage] = useState<string | null>(null);

  useEffect(() => {
    setParams(
      (previous) => {
        const current = previous.get("q") ?? "";
        if (current === debounced) return previous;
        const next = new URLSearchParams(previous);
        if (debounced) next.set("q", debounced);
        else next.delete("q");
        next.delete("page");
        return next;
      },
      { replace: true },
    );
  }, [debounced, setParams]);

  const request = useMemo(() => {
    const search = new URLSearchParams();
    const q = params.get("q");
    const country = params.get("country");
    const department = params.get("department");
    const status = params.get("status");
    if (q) search.set("q", q);
    if (country) search.set("country", country);
    if (department) search.set("department", department);
    if (status) search.set("status", status);
    search.set("page", params.get("page") || "1");
    search.set("page_size", "25");
    search.set("sort", params.get("sort") || "full_name");
    search.set("direction", params.get("direction") || "asc");
    return `/employees?${search.toString()}`;
  }, [params]);

  const list = useFetch<EmployeeList>(request);
  const sort = params.get("sort") || "full_name";
  const direction = params.get("direction") || "asc";
  const page = Number(params.get("page") || "1");

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete("page");
    setParams(next);
  }

  function toggleSort(field: string) {
    const next = new URLSearchParams(params);
    const nextDirection = sort === field && direction === "asc" ? "desc" : "asc";
    next.set("sort", field);
    next.set("direction", nextDirection);
    setParams(next);
  }

  function goToPage(nextPage: number) {
    const next = new URLSearchParams(params);
    if (nextPage <= 1) next.delete("page");
    else next.set("page", String(nextPage));
    setParams(next);
  }

  function openCreate() {
    setServerFields({});
    setServerMessage(null);
    setDraft("new");
  }

  function openEdit(employee: Employee) {
    setServerFields({});
    setServerMessage(null);
    setDraft(employee);
  }

  async function save(values: EmployeeInput) {
    setBusy(true);
    setServerFields({});
    setServerMessage(null);
    try {
      if (draft && draft !== "new") {
        await api(`/employees/${draft.id}`, { method: "PATCH", body: JSON.stringify(values) });
        toast(`${values.full_name} updated.`);
      } else {
        await api("/employees", { method: "POST", body: JSON.stringify(values) });
        toast(`${values.full_name} added.`);
      }
      setDraft(null);
      list.reload();
    } catch (error) {
      if (error instanceof ApiError) {
        setServerFields(error.fields);
        setServerMessage(error.message);
      } else {
        setServerMessage("Could not save that employee.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!pendingDelete) return;
    setBusy(true);
    try {
      await api(`/employees/${pendingDelete.id}`, { method: "DELETE" });
      toast(`${pendingDelete.full_name} removed.`);
      setPendingDelete(null);
      list.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "Could not remove that person.", "err");
    } finally {
      setBusy(false);
    }
  }

  const data = list.data;
  const filtersActive = Boolean(params.get("q") || params.get("country") || params.get("department") || params.get("status"));
  const rangeStart = data && data.total > 0 ? (data.page - 1) * data.page_size + 1 : 0;
  const rangeEnd = data ? Math.min(data.total, data.page * data.page_size) : 0;

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Directory</p>
          <h1>People</h1>
          <p className="lede">Add, update, and remove employees. Search stays on the server so the directory stays quick at 10,000 people.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          <Plus size={18} /> Add employee
        </button>
      </header>

      <div className="toolbar">
        <label className="search">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search name, email, title, or code"
            aria-label="Search employees"
          />
        </label>
        <select aria-label="Country" value={params.get("country") ?? ""} onChange={(event) => updateParam("country", event.target.value)}>
          <option value="">All countries</option>
          {reference.countries.map((country) => (
            <option key={country.name} value={country.name}>
              {country.name}
            </option>
          ))}
        </select>
        <select aria-label="Department" value={params.get("department") ?? ""} onChange={(event) => updateParam("department", event.target.value)}>
          <option value="">All departments</option>
          {reference.departments.map((department) => (
            <option key={department} value={department}>
              {department}
            </option>
          ))}
        </select>
        <select aria-label="Status" value={params.get("status") ?? ""} onChange={(event) => updateParam("status", event.target.value)}>
          <option value="">All statuses</option>
          {reference.statuses.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </select>
      </div>

      {list.error ? (
        <p className="banner banner-error">
          {list.error}
          <button type="button" className="btn btn-ghost" onClick={list.reload}>
            Try again
          </button>
        </p>
      ) : null}

      {list.loading && !data ? <DirectorySkeleton /> : null}

      {data && data.total === 0 ? (
        <div className="empty">
          <Users size={28} />
          <h2>{filtersActive ? "No people match these filters" : "The directory is empty"}</h2>
          <p>{filtersActive ? "Try a different search or clear the filters." : "Add the first employee to start the directory."}</p>
          {filtersActive ? (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setQuery("");
                setParams(new URLSearchParams());
              }}
            >
              Clear filters
            </button>
          ) : (
            <button type="button" className="btn btn-primary" onClick={openCreate}>
              <Plus size={18} /> Add employee
            </button>
          )}
        </div>
      ) : null}

      {data && data.total > 0 ? (
        <>
          <p className="result-count">
            {formatCount(rangeStart)}–{formatCount(rangeEnd)} of {formatCount(data.total)}
          </p>
          {compact ? (
            <div className="card-list">
              {data.items.map((employee) => (
                <article key={employee.id} className="person-card">
                  <header>
                    <div>
                      <h2>{employee.full_name}</h2>
                      <p>{employee.employee_code}</p>
                    </div>
                    <Status value={employee.status} label={labelFor(reference.statuses, employee.status)} />
                  </header>
                  <p>{employee.job_title}</p>
                  <p>
                    {employee.city}, {employee.country}
                  </p>
                  <strong>{formatMoney(employee.salary, employee.currency)}</strong>
                  <div className="row-actions">
                    <button type="button" className="btn btn-ghost" onClick={() => openEdit(employee)}>
                      <Pencil size={16} /> Edit
                    </button>
                    <button type="button" className="btn btn-danger" onClick={() => setPendingDelete(employee)}>
                      <Trash2 size={16} /> Remove
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="table-wrap table-card">
              <table>
                <caption className="sr-only">Employees</caption>
                <thead>
                  <tr>
                    {SORTS.map(([field, label]) => (
                      <th key={field} aria-sort={sort === field ? (direction === "asc" ? "ascending" : "descending") : "none"}>
                        <button type="button" className={sort === field ? "sort sort-active" : "sort"} onClick={() => toggleSort(field)}>
                          {label}
                          <ArrowUpDown size={14} />
                        </button>
                      </th>
                    ))}
                    <th>Status</th>
                    <th>
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((employee) => (
                    <tr key={employee.id}>
                      <td>
                        <button type="button" className="person-link" onClick={() => openEdit(employee)}>
                          {employee.full_name}
                        </button>
                        <small>
                          {employee.employee_code} · {employee.email}
                        </small>
                      </td>
                      <td>
                        {employee.job_title}
                        <small>{employee.department}</small>
                      </td>
                      <td>
                        {employee.city}
                        <small>{employee.country}</small>
                      </td>
                      <td className="money">{formatMoney(employee.salary, employee.currency)}</td>
                      <td>{formatDate(employee.hire_date)}</td>
                      <td>
                        <Status value={employee.status} label={labelFor(reference.statuses, employee.status)} />
                      </td>
                      <td>
                        <div className="row-actions">
                          <button type="button" className="icon-btn" aria-label={`Edit ${employee.full_name}`} onClick={() => openEdit(employee)}>
                            <Pencil size={16} />
                          </button>
                          <button type="button" className="icon-btn icon-danger" aria-label={`Remove ${employee.full_name}`} onClick={() => setPendingDelete(employee)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="pager">
            <button type="button" className="btn btn-ghost" onClick={() => goToPage(page - 1)} disabled={page <= 1}>
              <ChevronLeft size={16} /> Previous
            </button>
            <span>
              Page {formatCount(data.page)} of {formatCount(data.pages)}
            </span>
            <button type="button" className="btn btn-ghost" onClick={() => goToPage(page + 1)} disabled={page >= data.pages}>
              Next <ChevronRight size={16} />
            </button>
          </div>
        </>
      ) : null}

      <Modal
        open={draft !== null}
        title={draft && draft !== "new" ? "Edit employee" : "Add employee"}
        wide
        onClose={() => {
          if (!busy) setDraft(null);
        }}
      >
        <EmployeeForm
          key={draft === "new" || draft === null ? "new" : draft.id}
          initial={draft && draft !== "new" ? draft : null}
          reference={reference}
          submitting={busy}
          serverFields={serverFields}
          serverMessage={serverMessage}
          onSubmit={save}
          onCancel={() => setDraft(null)}
        />
      </Modal>

      <Modal open={pendingDelete !== null} title="Remove employee" onClose={() => { if (!busy) setPendingDelete(null); }}>
        <p className="confirm-copy">
          Remove {pendingDelete?.full_name} from the directory? This cannot be undone.
        </p>
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={() => setPendingDelete(null)} disabled={busy}>
            Keep
          </button>
          <button type="button" className="btn btn-danger" onClick={remove} disabled={busy}>
            {busy ? "Removing…" : "Remove"}
          </button>
        </div>
      </Modal>
    </div>
  );
}

function Status({ value, label }: { value: string; label: string }) {
  return <span className={`pill pill-${value}`}>{label}</span>;
}

function DirectorySkeleton() {
  return (
    <div className="skeleton-list">
      {Array.from({ length: 6 }, (_, index) => (
        <div key={index} className="skeleton row-skeleton" />
      ))}
    </div>
  );
}
