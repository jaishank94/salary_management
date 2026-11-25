import { validateEmployee } from "./validate";
import type { EmployeeInput } from "../types";

const TODAY = new Date(2026, 10, 25);

function input(overrides: Partial<EmployeeInput> = {}): EmployeeInput {
  return {
    full_name: "Priya Sharma",
    email: "priya.sharma@northstar.example",
    job_title: "Software Engineer",
    department: "Engineering",
    country: "India",
    city: "Bengaluru",
    salary: "1840000.50",
    employment_type: "full_time",
    status: "active",
    hire_date: "2022-04-18",
    ...overrides,
  };
}

describe("validateEmployee", () => {
  it("accepts a complete record", () => {
    expect(validateEmployee(input(), TODAY)).toEqual({});
  });

  it("accepts unicode names, commas in salary, and a title with digits", () => {
    expect(validateEmployee(input({ full_name: "José Álvarez", salary: "120,000.50", job_title: "Engineer II" }), TODAY)).toEqual({});
  });

  it("requires the fields an HR manager must fill", () => {
    const errors = validateEmployee(
      input({
        full_name: " ",
        email: "nope",
        job_title: "",
        department: "",
        country: "",
        city: "",
        salary: "",
        employment_type: "",
        status: "",
        hire_date: "",
      }),
      TODAY,
    );
    expect(errors.full_name).toMatch(/required/i);
    expect(errors.email).toMatch(/valid email/i);
    expect(errors.job_title).toBeTruthy();
    expect(errors.country).toBeTruthy();
    expect(errors.salary).toBeTruthy();
    expect(errors.hire_date).toBeTruthy();
  });

  it("rejects zero, negative, and over-precise salaries", () => {
    expect(validateEmployee(input({ salary: "0" }), TODAY).salary).toBeTruthy();
    expect(validateEmployee(input({ salary: "-5" }), TODAY).salary).toBeTruthy();
    expect(validateEmployee(input({ salary: "10.999" }), TODAY).salary).toBeTruthy();
  });

  it("rejects a future hire date and a date before 1950", () => {
    expect(validateEmployee(input({ hire_date: "2026-11-26" }), TODAY).hire_date).toMatch(/future/i);
    expect(validateEmployee(input({ hire_date: "1949-12-31" }), TODAY).hire_date).toBeTruthy();
  });

  it("rejects digits in a person's name", () => {
    expect(validateEmployee(input({ full_name: "Priya 3" }), TODAY).full_name).toBeTruthy();
  });
});
