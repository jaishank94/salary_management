import type { EmployeeInput } from "../types";

const NAME = /^(?=.{2,120}$)[\p{L}][\p{L}\s.'’-]*[\p{L}.]$/u;
const CITY = /^(?=.{2,60}$)[\p{L}][\p{L}\s.'’-]*[\p{L}.]$/u;
const TITLE = /^(?=.{2,80}$)[\p{L}][\p{L}\p{N}\s.'’&/+-]*[\p{L}\p{N}.]$/u;
const DEPARTMENT = /^(?=.{2,40}$)[\p{L}][\p{L}\s.'’&/-]*[\p{L}.]$/u;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SALARY = /^\d+(\.\d{1,2})?$/;

export type FieldErrors = Partial<Record<keyof EmployeeInput, string>>;

function collapse(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function parseDay(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null;
  return date;
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function validateEmployee(values: EmployeeInput, today = new Date()): FieldErrors {
  const errors: FieldErrors = {};
  const name = collapse(values.full_name ?? "");
  if (!name) errors.full_name = "Full name is required.";
  else if (/\d/.test(name) || /[.'’-]{2,}/u.test(name) || !NAME.test(name)) {
    errors.full_name = "Use letters, spaces, apostrophes, or hyphens (2–120 characters).";
  }

  const email = (values.email ?? "").trim();
  if (!email) errors.email = "Email is required.";
  else if (!EMAIL.test(email)) errors.email = "Enter a valid email address.";

  const title = collapse(values.job_title ?? "");
  if (!title) errors.job_title = "Job title is required.";
  else if (/[.'’&/+-]{2,}/u.test(title) || !TITLE.test(title)) {
    errors.job_title = "Enter a job title of 2–80 characters.";
  }

  const department = collapse(values.department ?? "");
  if (!department) errors.department = "Department is required.";
  else if (!DEPARTMENT.test(department)) errors.department = "Enter a department of 2–40 characters.";

  if (!values.country) errors.country = "Choose a country.";

  const city = collapse(values.city ?? "");
  if (!city) errors.city = "City is required.";
  else if (/\d/.test(city) || /[.'’-]{2,}/u.test(city) || !CITY.test(city)) {
    errors.city = "Enter a city name using letters.";
  }

  const salary = (values.salary ?? "").replace(/[, ]/g, "");
  if (!salary) errors.salary = "Salary is required.";
  else if (!SALARY.test(salary) || Number(salary) <= 0) errors.salary = "Enter a salary greater than zero, with at most 2 decimal places.";
  else if (Number(salary) > 1_000_000_000) errors.salary = "Salary must be 1,000,000,000 or less.";

  if (!values.employment_type) errors.employment_type = "Choose an employment type.";
  if (!values.status) errors.status = "Choose a status.";

  const hired = parseDay(values.hire_date ?? "");
  if (!hired) errors.hire_date = "Use a calendar date.";
  else if (hired < new Date(1950, 0, 1)) errors.hire_date = "Hire date must be on or after 1950.";
  else if (hired > startOfDay(today)) errors.hire_date = "Hire date cannot be in the future.";

  return errors;
}

export function normalizeInput(values: EmployeeInput, currency: string): EmployeeInput {
  return {
    full_name: collapse(values.full_name),
    email: values.email.trim().toLowerCase(),
    job_title: collapse(values.job_title),
    department: collapse(values.department),
    country: values.country,
    city: collapse(values.city),
    salary: values.salary.replace(/[, ]/g, ""),
    employment_type: values.employment_type,
    status: values.status,
    hire_date: values.hire_date,
    currency,
  };
}
