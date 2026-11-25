import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmployeeForm } from "./EmployeeForm";
import type { ReferenceData } from "../types";

const reference: ReferenceData = {
  countries: [{ name: "India", currency: "INR", cities: ["Bengaluru", "Mumbai"] }],
  job_titles: ["Software Engineer"],
  departments: ["Engineering"],
  employment_types: [{ value: "full_time", label: "Full-time" }],
  statuses: [{ value: "active", label: "Active" }],
};

describe("EmployeeForm", () => {
  it("shows field errors and does not submit an empty record", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <EmployeeForm
        reference={reference}
        submitting={false}
        onSubmit={onSubmit}
        onCancel={() => {}}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Add employee" }));
    expect(screen.getByText("Full name is required.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits a normalized employee", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<EmployeeForm reference={reference} submitting={false} onSubmit={onSubmit} onCancel={() => {}} />);
    await user.type(screen.getByLabelText("Full name"), "Priya Sharma");
    await user.type(screen.getByLabelText("Email"), "Priya.Sharma@Northstar.Example");
    await user.type(screen.getByLabelText("Job title"), "Software Engineer");
    await user.selectOptions(screen.getByLabelText("Department"), "Engineering");
    await user.selectOptions(screen.getByLabelText("Country"), "India");
    await user.type(screen.getByLabelText("City"), "Bengaluru");
    await user.type(screen.getByLabelText(/annual salary/i), "120,000.50");
    await user.type(screen.getByLabelText("Hire date"), "2022-04-18");
    await user.click(screen.getByRole("button", { name: "Add employee" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        full_name: "Priya Sharma",
        email: "priya.sharma@northstar.example",
        salary: "120000.50",
        currency: "INR",
        country: "India",
      }),
    );
  });
});
