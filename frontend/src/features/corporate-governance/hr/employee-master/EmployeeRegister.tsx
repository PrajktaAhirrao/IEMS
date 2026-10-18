import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getEmployees,
  type Employee,
} from "./services/employeeMasterApi";
import "./EmployeeMaster.css";

type EmployeeRegisterProps = {
  legalEntityId: number;
  plantId: number | null;
  onCreateEmployee: () => void;
  onViewEmployee: (employeeId: string) => void;
};

const formatDate = (value: string | null) => {
  if (!value) return "—";

  const date = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
};

const statusLabel = (value: string) =>
  value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) =>
    letter.toUpperCase(),
  );

export default function EmployeeRegister({
  legalEntityId,
  plantId,
  onCreateEmployee,
  onViewEmployee,
}: EmployeeRegisterProps) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadEmployees = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");

    try {
      const data = await getEmployees(legalEntityId, plantId);
      setEmployees(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load the employee register.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [legalEntityId, plantId]);

  useEffect(() => {
    void loadEmployees();
  }, [loadEmployees]);

  const filteredEmployees = useMemo(() => {
    const query = search.trim().toLowerCase();

    return employees.filter((employee) => {
      const matchesSearch =
        !query ||
        [
          employee.employee_code,
          employee.full_name,
          employee.preferred_name,
          employee.designation,
          employee.work_location,
        ].some((value) => value?.toLowerCase().includes(query));

      const matchesStatus =
        statusFilter === "ALL" ||
        employee.employment_status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [employees, search, statusFilter]);

  return (
    <section className="employee-master">
      <header className="employee-page-header">
        <div>
          <p className="employee-eyebrow">HUMAN RESOURCES</p>
          <h1>Employee Master</h1>
          <p className="employee-subtitle">
            Maintain and review employee records for the selected plant.
          </p>
        </div>

        <div className="employee-header-actions">
          <button
            type="button"
            className="employee-button employee-button-secondary"
            onClick={() => void loadEmployees(true)}
            disabled={loading || refreshing}
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
          <button
            type="button"
            className="employee-button employee-button-primary"
            onClick={onCreateEmployee}
          >
            + Add Employee
          </button>
        </div>
      </header>

      <div className="employee-summary-grid">
        <article className="employee-summary-card">
          <span>Total Records</span>
          <strong>{employees.length}</strong>
        </article>
        <article className="employee-summary-card">
          <span>Active Employees</span>
          <strong>
            {employees.filter(
              (employee) => employee.employment_status === "ACTIVE",
            ).length}
          </strong>
        </article>
        <article className="employee-summary-card">
          <span>Draft Records</span>
          <strong>
            {employees.filter(
              (employee) => employee.record_status === "DRAFT",
            ).length}
          </strong>
        </article>
        <article className="employee-summary-card">
          <span>Pending Verification</span>
          <strong>
            {employees.filter(
              (employee) =>
                employee.record_status === "PENDING_VERIFICATION",
            ).length}
          </strong>
        </article>
      </div>

      <div className="employee-register-panel">
        <div className="employee-register-toolbar">
          <div>
            <h2>Employee Register</h2>
            <p>{filteredEmployees.length} record(s) displayed</p>
          </div>

          <div className="employee-register-filters">
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search employee, code or designation"
              aria-label="Search employees"
            />

            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              aria-label="Filter by employment status"
            >
              <option value="ALL">All statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="ON_LEAVE">On leave</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="SEPARATED">Separated</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="employee-alert employee-alert-error" role="alert">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => void loadEmployees()}
            >
              Try again
            </button>
          </div>
        )}

        {loading ? (
          <div className="employee-empty-state">Loading employee records…</div>
        ) : !error && filteredEmployees.length === 0 ? (
          <div className="employee-empty-state">
            <strong>
              {employees.length === 0
                ? "No employee records yet"
                : "No matching employees"}
            </strong>
            <p>
              {employees.length === 0
                ? "Add an employee to begin building this plant's register."
                : "Try changing the search term or status filter."}
            </p>
            {employees.length === 0 && (
              <button
                type="button"
                className="employee-button employee-button-primary"
                onClick={onCreateEmployee}
              >
                + Add Employee
              </button>
            )}
          </div>
        ) : !error ? (
          <div className="employee-table-wrap">
            <table className="employee-table">
              <thead>
                <tr>
                  <th>Employee Code</th>
                  <th>Employee</th>
                  <th>Designation</th>
                  <th>Work Location</th>
                  <th>Employment Status</th>
                  <th>Record Status</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((employee) => (
                  <tr key={employee.id}>
                    <td>
                      <span className="employee-code">
                        {employee.employee_code || "Pending"}
                      </span>
                    </td>
                    <td>
                      <div className="employee-name-cell">
                        <strong>{employee.full_name || "Unnamed employee"}</strong>
                        {employee.preferred_name &&
                          employee.preferred_name !== employee.full_name && (
                            <span>Known as {employee.preferred_name}</span>
                          )}
                        {employee.date_of_joining && (
                          <span>
                            Joined {formatDate(employee.date_of_joining)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>{employee.designation || "—"}</td>
                    <td>{employee.work_location || "—"}</td>
                    <td>
                      <span
                        className={`employee-status employee-status-${employee.employment_status.toLowerCase()}`}
                      >
                        {statusLabel(employee.employment_status)}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`employee-record-status employee-record-status-${employee.record_status.toLowerCase()}`}
                      >
                        {statusLabel(employee.record_status)}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="employee-link-button"
                        onClick={() => onViewEmployee(employee.id)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
