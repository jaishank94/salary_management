export type EmploymentType = "full_time" | "part_time" | "contract";
export type EmployeeStatus = "active" | "on_leave" | "terminated";

export type Employee = {
  id: number;
  employee_code: string;
  full_name: string;
  email: string;
  job_title: string;
  department: string;
  country: string;
  city: string;
  currency: string;
  salary: string;
  employment_type: EmploymentType;
  status: EmployeeStatus;
  hire_date: string;
  created_at: string;
  updated_at: string;
};

export type EmployeeInput = {
  full_name: string;
  email: string;
  job_title: string;
  department: string;
  country: string;
  city: string;
  salary: string;
  employment_type: string;
  status: string;
  hire_date: string;
  currency?: string;
};

export type LabeledValue = { value: string; label: string };

export type CountryRef = { name: string; currency: string; cities: string[] };

export type ReferenceData = {
  countries: CountryRef[];
  job_titles: string[];
  departments: string[];
  employment_types: LabeledValue[];
  statuses: LabeledValue[];
};

export type EmployeeList = {
  items: Employee[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type GroupBreakdown = {
  key: string;
  headcount: number;
  minimum: string | null;
  maximum: string | null;
  average: string | null;
  total_payroll: string;
};

export type SalaryBand = { minimum: string; maximum: string; count: number };

export type CountryInsights = {
  country: string;
  currency: string;
  included_statuses: string[];
  excluded_currency_count: number;
  status_breakdown: Record<string, number>;
  headcount: number;
  minimum: string | null;
  maximum: string | null;
  average: string | null;
  median: string | null;
  p25: string | null;
  p75: string | null;
  total_payroll: string;
  bands: SalaryBand[];
  by_department: GroupBreakdown[];
  by_job_title: GroupBreakdown[];
  by_employment_type: GroupBreakdown[];
};

export type TitleInsights = {
  country: string;
  currency: string;
  job_title: string;
  included_statuses: string[];
  excluded_currency_count: number;
  headcount: number;
  minimum: string | null;
  maximum: string | null;
  average: string | null;
  median: string | null;
  p25: string | null;
  p75: string | null;
  total_payroll: string;
  bands: SalaryBand[];
};

export type CountryRollup = {
  country: string;
  currency: string;
  headcount: number;
  minimum: string | null;
  maximum: string | null;
  average: string | null;
  total_payroll: string;
};

export type Overview = {
  workforce_count: number;
  compensation_headcount: number;
  status_breakdown: Record<string, number>;
  included_statuses: string[];
  countries: CountryRollup[];
};
