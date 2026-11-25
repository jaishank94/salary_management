import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Banknote, Briefcase, Building2, Calendar, Mail, MapPin, UserRound } from "lucide-react";
import type { Employee, EmployeeInput, ReferenceData } from "../types";
import { normalizeInput, validateEmployee, type FieldErrors } from "../lib/validate";

type Props = {
  initial?: Employee | null;
  reference: ReferenceData;
  submitting: boolean;
  serverFields?: Record<string, string>;
  serverMessage?: string | null;
  onSubmit: (values: EmployeeInput) => void;
  onCancel: () => void;
};

const EMPTY: EmployeeInput = {
  full_name: "",
  email: "",
  job_title: "",
  department: "",
  country: "",
  city: "",
  salary: "",
  employment_type: "full_time",
  status: "active",
  hire_date: "",
};

function fromEmployee(employee: Employee): EmployeeInput {
  return {
    full_name: employee.full_name,
    email: employee.email,
    job_title: employee.job_title,
    department: employee.department,
    country: employee.country,
    city: employee.city,
    salary: employee.salary,
    employment_type: employee.employment_type,
    status: employee.status,
    hire_date: employee.hire_date,
  };
}

export function EmployeeForm({ initial, reference, submitting, serverFields, serverMessage, onSubmit, onCancel }: Props) {
  const [values, setValues] = useState<EmployeeInput>(initial ? fromEmployee(initial) : EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const country = reference.countries.find((item) => item.name === values.country);
  const cities = country?.cities ?? [];
  const currency = country?.currency ?? "";
  const shown = useMemo(() => ({ ...errors, ...serverFields }), [errors, serverFields]);
  const countryChanged = Boolean(initial && values.country && values.country !== initial.country);

  function update<K extends keyof EmployeeInput>(key: K, value: EmployeeInput[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function changeCountry(next: string) {
    const nextCities = reference.countries.find((item) => item.name === next)?.cities ?? [];
    setValues((current) => ({
      ...current,
      country: next,
      city: nextCities.includes(current.city) ? current.city : "",
    }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const nextErrors = validateEmployee(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    onSubmit(normalizeInput(values, currency));
  }

  return (
    <form className="form" onSubmit={submit} noValidate>
      {serverMessage ? <p className="banner banner-error">{serverMessage}</p> : null}
      <div className="form-grid">
        <Field label="Full name" icon={<UserRound size={16} />} error={shown.full_name} htmlFor="full_name">
          <input id="full_name" value={values.full_name} onChange={(event) => update("full_name", event.target.value)} autoComplete="name" />
        </Field>
        <Field label="Email" icon={<Mail size={16} />} error={shown.email} htmlFor="email">
          <input id="email" type="email" value={values.email} onChange={(event) => update("email", event.target.value)} autoComplete="email" spellCheck={false} />
        </Field>
        <Field label="Job title" icon={<Briefcase size={16} />} error={shown.job_title} htmlFor="job_title">
          <input id="job_title" list="job-titles" value={values.job_title} onChange={(event) => update("job_title", event.target.value)} />
          <datalist id="job-titles">
            {reference.job_titles.map((title) => (
              <option key={title} value={title} />
            ))}
          </datalist>
        </Field>
        <Field label="Department" icon={<Building2 size={16} />} error={shown.department} htmlFor="department">
          <select id="department" value={values.department} onChange={(event) => update("department", event.target.value)}>
            <option value="">Choose a department</option>
            {reference.departments.map((department) => (
              <option key={department} value={department}>
                {department}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Country" icon={<MapPin size={16} />} error={shown.country} htmlFor="country">
          <select id="country" value={values.country} onChange={(event) => changeCountry(event.target.value)}>
            <option value="">Choose a country</option>
            {reference.countries.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="City" icon={<MapPin size={16} />} error={shown.city} htmlFor="city">
          <input id="city" list="cities" value={values.city} onChange={(event) => update("city", event.target.value)} />
          <datalist id="cities">
            {cities.map((city) => (
              <option key={city} value={city} />
            ))}
          </datalist>
        </Field>
        <Field label="Annual salary" icon={<Banknote size={16} />} error={shown.salary} htmlFor="salary">
          <div className="salary-input">
            <span>{currency || "—"}</span>
            <input
              id="salary"
              inputMode="decimal"
              value={values.salary}
              onChange={(event) => update("salary", event.target.value)}
              placeholder="0.00"
            />
          </div>
        </Field>
        <Field label="Hire date" icon={<Calendar size={16} />} error={shown.hire_date} htmlFor="hire_date">
          <input id="hire_date" type="date" value={values.hire_date} onChange={(event) => update("hire_date", event.target.value)} />
        </Field>
        <Field label="Employment type" error={shown.employment_type} htmlFor="employment_type">
          <select id="employment_type" value={values.employment_type} onChange={(event) => update("employment_type", event.target.value)}>
            {reference.employment_types.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Status" error={shown.status} htmlFor="status">
          <select id="status" value={values.status} onChange={(event) => update("status", event.target.value)}>
            {reference.statuses.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <p className="form-note">
        {currency
          ? `This salary is stored in ${currency}. Averages for ${values.country} stay in that currency.`
          : "Choose a country to set the salary currency."}
      </p>
      {countryChanged ? (
        <p className="banner banner-warn">Changing country keeps the number as typed and switches the currency. It does not convert the amount.</p>
      ) : null}
      <div className="form-actions">
        <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Saving…" : initial ? "Save changes" : "Add employee"}
        </button>
      </div>
    </form>
  );
}

function Field({
  label,
  htmlFor,
  error,
  icon,
  children,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  icon?: ReactNode;
  children: ReactNode;
}) {
  const errorId = `${htmlFor}-error`;
  return (
    <label className="field" htmlFor={htmlFor}>
      <span className="field-label">
        {icon}
        {label}
      </span>
      {children}
      {error ? (
        <span className="field-error" id={errorId}>
          {error}
        </span>
      ) : null}
    </label>
  );
}
