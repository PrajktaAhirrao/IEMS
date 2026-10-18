
import { useEffect, useState } from "react";
import EnquiryForm from "../commercial/front-desk/EnquiryForm";
import EmployeeRegister from "../corporate-governance/hr/employee-master/EmployeeRegister";
import EmployeeForm from "../corporate-governance/hr/employee-master/EmployeeForm";
import {
  getEmployees,
  type Employee,
} from "../corporate-governance/hr/employee-master/services/employeeMasterApi";
import "./design-tokens.css";
import "./Workspace.css";

type AuthenticatedAppProps = {
  user: {
    first_name: string;
    last_name: string;
    email: string;
  };
  assignments: {
    role: {
      id: number;
      code: string;
      name: string;
      scope_level: string;
    };
    legal_entity_id: number;
    plant_id: number | null;
    organizational_unit_id: number | null;
    is_primary: boolean;
    permissions: string[];
  }[];
  permissions: string[];
  onLogout: () => void;
};

type Enquiry = {
  reference_id: string;
  contact_name: string;
  company_name?: string;
  channel: string;
  intent: string;
  status: string;
  created_at: string;
};

type EnquiryResponse = Enquiry[] | { results: Enquiry[] };

const MODULES = [
  {
    id: "front-desk",
    title: "Front Desk",
    description: "Capture incoming enquiries and route business contacts.",
    permission: "commercial.front_desk.access",
    icon: "▣",
    section: "COMMERCIAL",
  },
  {
    id: "enquiry-register",
    title: "Enquiry Register",
    description: "Search and review registered enquiries.",
    permission: "commercial.front_desk.access",
    icon: "▤",
    section: "COMMERCIAL",
  },
  {
    id: "routing-queue",
    title: "Routing Queue",
    description: "Review enquiries awaiting routing.",
    permission: "commercial.front_desk.access",
    icon: "⇄",
    section: "COMMERCIAL",
  },
  {
    id: "activity-log",
    title: "Activity Log",
    description: "Review enquiry activity.",
    permission: "commercial.front_desk.access",
    icon: "◷",
    section: "COMMERCIAL",
  },
  {
    id: "marketing",
    title: "Marketing",
    description: "Manage prospects, leads and follow-ups.",
    permission: "commercial.marketing.access",
    icon: "↗",
    section: "OTHER MODULES",
  },
  {
    id: "sales",
    title: "Sales",
    description: "Manage sales opportunities and customers.",
    permission: "commercial.sales.access",
    icon: "▧",
    section: "OTHER MODULES",
  },
  {
    id: "contracts",
    title: "Contracts",
    description: "Manage commercial terms and contracts.",
    permission: "commercial.contracts.access",
    icon: "▤",
    section: "OTHER MODULES",
  },
  {
    id: "employee-master",
    title: "Employee Master",
    description: "Create, search and maintain employee records.",
    permission: "employees.employee_master.view",
    icon: "♙",
    section: "CORPORATE GOVERNANCE",
  },
];

const API_URL = "http://127.0.0.1:8000/api/commercial/enquiries/";

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusLabel(status: string) {
  return status.replaceAll("_", " ");
}

export default function AuthenticatedApp({
  user,
  assignments,
  permissions,
  onLogout,
}: AuthenticatedAppProps) {
  const [activeScreen, setActiveScreen] = useState("dashboard");
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [loadingEnquiries, setLoadingEnquiries] = useState(false);
  const [enquiryError, setEnquiryError] = useState("");
  const [search, setSearch] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [employeeError, setEmployeeError] = useState("");

  const displayName =
    `${user.first_name} ${user.last_name}`.trim() || user.email;

  const initials =
    `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase() ||
    user.email.charAt(0).toUpperCase();

  const primaryAssignment =
    assignments.find((assignment) => assignment.is_primary) ??
    assignments[0];

  const hrAssignment = assignments.find(
    (assignment) =>
      [
        "CENTRAL_HR",
        "PLANT_HR_MANAGER",
        "PLANT_HR_EXECUTIVE",
      ].includes(assignment.role.code) &&
      assignment.permissions.includes("employees.employee_master.view")
  );

  const employeeMasterLegalEntityId = hrAssignment?.legal_entity_id;
  const employeeMasterPlantId = hrAssignment?.plant_id ?? null;

  const legalEntityId = primaryAssignment?.legal_entity_id;

  const visibleModules = MODULES.filter((module) =>
    permissions.includes(module.permission)
  );

  const canAccessFrontDesk = permissions.includes(
    "commercial.front_desk.access"
  );

  const frontDeskScreens = [
    "front-desk",
    "enquiry-register",
    "routing-queue",
    "activity-log",
  ];

  const activeModule = visibleModules.find(
    (module) => module.id === activeScreen
  );

  useEffect(() => {
    if (!canAccessFrontDesk || !legalEntityId) {
      setEnquiries([]);
      return;
    }

    if (
      activeScreen !== "dashboard" &&
      !frontDeskScreens.includes(activeScreen)
    ) {
      return;
    }

    let cancelled = false;

    async function loadEnquiries() {
      setLoadingEnquiries(true);
      setEnquiryError("");

      try {
        const token = localStorage.getItem("iems_token");

        if (!token) {
          throw new Error("Your session has expired. Please sign in again.");
        }

        const response = await fetch(
          `${API_URL}?legal_entity_id=${legalEntityId}`,
          {
            headers: {
              Authorization: `Token ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error(
            response.status === 403
              ? "You do not have permission to view these enquiries."
              : "Unable to load enquiries. Please try again."
          );
        }

        const data: EnquiryResponse = await response.json();
        const rows = Array.isArray(data) ? data : data.results ?? [];

        if (!cancelled) {
          setEnquiries(rows);
        }
      } catch (error) {
        if (!cancelled) {
          setEnquiryError(
            error instanceof Error
              ? error.message
              : "Unable to load enquiries."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingEnquiries(false);
        }
      }
    }

    void loadEnquiries();

    return () => {
      cancelled = true;
    };
  }, [activeScreen, canAccessFrontDesk, legalEntityId]);

  useEffect(() => {
    if (
      !permissions.includes("employees.employee_master.view") ||
      !hrAssignment ||
      employeeMasterLegalEntityId == null
    ) {
      setEmployees([]);
      return;
    }

    let cancelled = false;
    async function loadEmployeeSummary() {
      setLoadingEmployees(true);
      setEmployeeError("");
      try {
        const rows = await getEmployees(
          employeeMasterLegalEntityId!,
          employeeMasterPlantId,
        );
        if (!cancelled) setEmployees(rows);
      } catch (error) {
        if (!cancelled) {
          setEmployeeError(
            error instanceof Error ? error.message : "Unable to load employee summary.",
          );
        }
      } finally {
        if (!cancelled) setLoadingEmployees(false);
      }
    }

    void loadEmployeeSummary();
    return () => {
      cancelled = true;
    };
  }, [permissions, hrAssignment, employeeMasterLegalEntityId, employeeMasterPlantId]);

  const filteredEnquiries = enquiries.filter((enquiry) => {
    const query = search.trim().toLowerCase();

    if (!query) return true;

    return [
      enquiry.reference_id,
      enquiry.contact_name,
      enquiry.company_name ?? "",
      enquiry.channel,
      enquiry.intent,
      enquiry.status,
    ].some((value) => value.toLowerCase().includes(query));
  });

  const statusCounts = {
    NEW: enquiries.filter((item) => item.status === "NEW").length,
    UNDER_REVIEW: enquiries.filter(
      (item) => item.status === "UNDER_REVIEW"
    ).length,
    ROUTED: enquiries.filter((item) => item.status === "ROUTED").length,
    CLOSED: enquiries.filter((item) => item.status === "CLOSED").length,
  };

  function navigate(screen: string) {
    setActiveScreen(screen);
    setProfileOpen(false);
  }

  function renderRecentEnquiries() {
    if (loadingEnquiries) {
      return <p className="iems-empty-state">Loading enquiries…</p>;
    }

    if (enquiryError) {
      return (
        <div className="iems-inline-error" role="alert">
          {enquiryError}
        </div>
      );
    }

    if (filteredEnquiries.length === 0) {
      return (
        <p className="iems-empty-state">
          {search
            ? "No enquiries match your search."
            : "No enquiries have been registered yet."}
        </p>
      );
    }

    return (
      <div className="iems-table-wrap">
        <table className="iems-data-table">
          <thead>
            <tr>
              <th>Reference ID</th>
              <th>Contact Name</th>
              <th>Company</th>
              <th>Channel</th>
              <th>Intent</th>
              <th>Status</th>
              <th>Created On</th>
            </tr>
          </thead>
          <tbody>
            {filteredEnquiries.slice(0, 8).map((enquiry) => (
              <tr key={enquiry.reference_id}>
                <td className="iems-reference">
                  {enquiry.reference_id.slice(0, 8).toUpperCase()}
                </td>
                <td>{enquiry.contact_name}</td>
                <td>{enquiry.company_name || "—"}</td>
                <td>{enquiry.channel.replaceAll("_", " ")}</td>
                <td>{enquiry.intent.replaceAll("_", " ")}</td>
                <td>
                  <span
                    className={`iems-status iems-status-${enquiry.status.toLowerCase()}`}
                  >
                    {statusLabel(enquiry.status)}
                  </span>
                </td>
                <td>{formatDate(enquiry.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  function renderDashboard() {
    return (
      <>
        <section className="iems-page-heading">
          <div className="iems-heading-icon">▣</div>
          <div>
            <h1>Commercial Front Desk</h1>
            <p>Handle initial enquiries and route incoming business contacts.</p>
          </div>
          <div className="iems-heading-meta">
            <span>WORKSPACE / FD-001</span>
            <strong>{new Date().toLocaleDateString("en-IN")}</strong>
          </div>
        </section>

        <section className="iems-metric-grid" aria-label="Enquiry summary">
          {[
            {
              label: "New Enquiries",
              value: statusCounts.NEW,
              status: "new",
              screen: "enquiry-register",
            },
            {
              label: "Under Review",
              value: statusCounts.UNDER_REVIEW,
              status: "review",
              screen: "enquiry-register",
            },
            {
              label: "Routed",
              value: statusCounts.ROUTED,
              status: "routed",
              screen: "routing-queue",
            },
            {
              label: "Closed",
              value: statusCounts.CLOSED,
              status: "closed",
              screen: "enquiry-register",
            },
          ].map((metric) => (
            <button
              type="button"
              className={`iems-metric-card iems-metric-${metric.status}`}
              key={metric.label}
              onClick={() => navigate(metric.screen)}
            >
              <span>{metric.label}</span>
              <strong>{loadingEnquiries ? "—" : metric.value}</strong>
              <span className="iems-metric-arrow">→</span>
            </button>
          ))}
        </section>

        <div className="iems-dashboard-grid">
          <section className="iems-panel iems-recent-panel">
            <header className="iems-panel-heading">
              <h2>Recent Enquiries</h2>
              <button
                type="button"
                className="iems-text-button"
                onClick={() => navigate("enquiry-register")}
              >
                View Register →
              </button>
            </header>
            {renderRecentEnquiries()}
            <footer className="iems-panel-footer">
              Showing up to 8 enquiries from the available results.
            </footer>
          </section>

          <aside className="iems-dashboard-aside">
            <section className="iems-panel">
              <header className="iems-panel-heading">
                <h2>Quick Actions</h2>
              </header>
              <div className="iems-quick-actions">
                <button
                  type="button"
                  className="iems-button-primary"
                  onClick={() => navigate("new-enquiry")}
                >
                  ＋ Register New Enquiry
                </button>
                <button
                  type="button"
                  className="iems-button-secondary"
                  onClick={() => navigate("enquiry-register")}
                >
                  ▤ View Enquiry Register
                </button>
                <button
                  type="button"
                  className="iems-button-secondary"
                  onClick={() => navigate("routing-queue")}
                >
                  ⇄ Open Routing Queue
                </button>
                <button
                  type="button"
                  className="iems-button-secondary"
                  onClick={() => navigate("activity-log")}
                >
                  ◷ View Activity Log
                </button>
              </div>
            </section>

            <section className="iems-panel">
              <header className="iems-panel-heading">
                <h2>Workspace Summary</h2>
              </header>
              <div className="iems-summary-row">
                <span>Available enquiry results</span>
                <strong>{loadingEnquiries ? "…" : enquiries.length}</strong>
              </div>
              <div className="iems-summary-row">
                <span>Assigned role</span>
                <strong>{primaryAssignment?.role.name ?? "Unassigned"}</strong>
              </div>
            </section>
          </aside>
        </div>
      </>
    );
  }


  function renderHrDashboard() {
    const draftCount = employees.filter((employee) => employee.record_status === "DRAFT").length;
    const pendingCount = employees.filter((employee) => employee.record_status === "PENDING_VERIFICATION").length;
    const verifiedCount = employees.filter((employee) => employee.record_status === "VERIFIED").length;

    return (
      <>
        <section className="iems-page-heading">
          <div className="iems-heading-icon">♙</div>
          <div>
            <h1>Human Resources</h1>
            <p>Manage employee master records and employee information.</p>
          </div>
          <div className="iems-heading-meta">
            <span>WORKSPACE / HR-001</span>
            <strong>{new Date().toLocaleDateString("en-IN")}</strong>
          </div>
        </section>

        <section className="iems-metric-grid" aria-label="Employee summary">
          {[
            { label: "Total Employees", value: employees.length, status: "new" },
            { label: "Draft Records", value: draftCount, status: "review" },
            { label: "Pending Verification", value: pendingCount, status: "routed" },
            { label: "Verified Records", value: verifiedCount, status: "closed" },
          ].map((metric) => (
            <button
              type="button"
              className={`iems-metric-card iems-metric-${metric.status}`}
              key={metric.label}
              onClick={() => navigate("employee-master")}
            >
              <span>{metric.label}</span>
              <strong>{loadingEmployees ? "—" : metric.value}</strong>
              <span className="iems-metric-arrow">→</span>
            </button>
          ))}
        </section>

        <div className="iems-dashboard-grid">
          <section className="iems-panel iems-recent-panel">
            <header className="iems-panel-heading">
              <h2>Employee Master Overview</h2>
              <button type="button" className="iems-text-button" onClick={() => navigate("employee-master")}>
                View Register →
              </button>
            </header>
            {employeeError ? (
              <div className="iems-inline-error" role="alert">{employeeError}</div>
            ) : (
              <div className="iems-summary-row">
                <span>{loadingEmployees ? "Loading employee records…" : "Employee records available in your authorized scope"}</span>
                <strong>{loadingEmployees ? "…" : employees.length}</strong>
              </div>
            )}
            <footer className="iems-panel-footer">
              Records shown are limited by your active HR assignment and permissions.
            </footer>
          </section>

          <aside className="iems-dashboard-aside">
            <section className="iems-panel">
              <header className="iems-panel-heading"><h2>Quick Actions</h2></header>
              <div className="iems-quick-actions">
                <button type="button" className="iems-button-primary" onClick={() => navigate("employee-master")}>
                  ♙ Open Employee Master
                </button>
                {permissions.includes("employees.employee_master.manage") && (
                  <button type="button" className="iems-button-secondary" onClick={() => navigate("employee-create")}>
                    ＋ Add Employee
                  </button>
                )}
              </div>
            </section>
            <section className="iems-panel">
              <header className="iems-panel-heading"><h2>Workspace Summary</h2></header>
              <div className="iems-summary-row">
                <span>Assigned role</span>
                <strong>{hrAssignment?.role.name ?? primaryAssignment?.role.name ?? "Unassigned"}</strong>
              </div>
              <div className="iems-summary-row">
                <span>Plant scope</span>
                <strong>{employeeMasterPlantId == null ? "All authorized plants" : `Plant ${employeeMasterPlantId}`}</strong>
              </div>
            </section>
          </aside>
        </div>
      </>
    );
  }

  function renderScreen() {
    if (activeScreen === "new-enquiry") {
      if (!canAccessFrontDesk || !legalEntityId) {
        return (
          <section className="iems-panel">
            <h1>Access unavailable</h1>
            <p>
              A valid Front Desk permission and legal entity assignment
              are required to register an enquiry.
            </p>
          </section>
        );
      }

      return (
        <EnquiryForm
          legalEntityId={legalEntityId}
          onBack={() => navigate("dashboard")}
        />
      );
    }

    if (activeScreen === "dashboard") {
      // Choose the default dashboard from the user's primary assignment.
      // HR users land on HR; Commercial users retain the Front Desk dashboard.
      const primaryRoleCode = primaryAssignment?.role.code ?? "";
      const primaryAssignmentIsHr = [
        "CENTRAL_HR",
        "PLANT_HR_MANAGER",
        "PLANT_HR_EXECUTIVE",
      ].includes(primaryRoleCode);

      if (
        primaryAssignmentIsHr &&
        permissions.includes("employees.employee_master.view") &&
        hrAssignment
      ) {
        return renderHrDashboard();
      }
      if (canAccessFrontDesk) return renderDashboard();
      if (permissions.includes("employees.employee_master.view") && hrAssignment) {
        return renderHrDashboard();
      }
      return (
        <section className="iems-panel iems-welcome-panel">
          <h1>Enterprise Workspace</h1>
          <p>Select an authorized module from the sidebar to continue.</p>
          {visibleModules.length === 0 && (
            <p>No department modules are available for your account.</p>
          )}
        </section>
      );
    }

    // Handle Employee Master BEFORE the generic module placeholder.
    if (activeScreen === "employee-master") {
      if (
        !permissions.includes("employees.employee_master.view") ||
        !hrAssignment ||
        employeeMasterLegalEntityId == null
      ) {
        return (
          <section className="iems-panel">
            <h1>Access unavailable</h1>
            <p>
              An authorized HR assignment and Employee Master permission
              are required to access this register.
            </p>
          </section>
        );
      }

      return (
        <EmployeeRegister
          legalEntityId={employeeMasterLegalEntityId}
          plantId={employeeMasterPlantId}
          onCreateEmployee={() => navigate("employee-create")}
          onViewEmployee={(employeeId) =>
            navigate(`employee-view:${employeeId}`)
          }
        />
      );
    }

    // Employee creation is a separate screen and requires the manage permission.
    if (activeScreen === "employee-create") {
      if (
        !permissions.includes("employees.employee_master.manage") ||
        !hrAssignment ||
        employeeMasterLegalEntityId == null
      ) {
        return (
          <section className="iems-panel">
            <h1>Access unavailable</h1>
            <p>
              An authorized HR assignment and Employee Master management
              permission are required to create an employee record.
            </p>
            <button
              type="button"
              className="iems-button-secondary"
              onClick={() => navigate("employee-master")}
            >
              ← Back to Employee Register
            </button>
          </section>
        );
      }

      return (
        <EmployeeForm
          legalEntityId={employeeMasterLegalEntityId}
          plantId={employeeMasterPlantId}
          onCancel={() => navigate("employee-master")}
          onCreated={() => navigate("employee-master")}
        />
      );
    }

    if (activeScreen.startsWith("employee-view:")) {
      return (
        <section className="iems-panel">
          <h1>Employee details</h1>
          <p>The employee detail screen has not been implemented yet.</p>
          <button
            type="button"
            className="iems-button-secondary"
            onClick={() => navigate("employee-master")}
          >
            ← Back to Employee Register
          </button>
        </section>
      );
    }

    if (activeScreen === "front-desk" && canAccessFrontDesk) {
      return renderDashboard();
    }

    if (activeModule) {
      return (
        <section className="iems-panel iems-module-placeholder">
          <span className="iems-screen-code">
            IEMS / {activeScreen.toUpperCase()}
          </span>
          <h1>{activeModule.title}</h1>
          <p>{activeModule.description}</p>
          <p>
            This screen is not connected yet. Its navigation is in place;
            we will implement its workflow next.
          </p>
          <button
            type="button"
            className="iems-button-secondary"
            onClick={() => navigate("dashboard")}
          >
            ← Back to Dashboard
          </button>
        </section>
      );
    }

    return (
      <section className="iems-panel">
        <h1>Module unavailable</h1>
        <p>Your account does not have access to this workspace.</p>
        <button
          type="button"
          className="iems-button-secondary"
          onClick={() => navigate("dashboard")}
        >
          Back to Dashboard
        </button>
      </section>
    );
  }


  const sidebarSections = [
    "COMMERCIAL",
    "CORPORATE GOVERNANCE",
    "OTHER MODULES",
  ];

  return (
    <main className="iems-workspace">
      <aside className="iems-sidebar">
        <button
          type="button"
          className="iems-brand"
          onClick={() => navigate("dashboard")}
          aria-label="Go to IEMS dashboard"
        >
          <span className="iems-brand-mark">i</span>
          <span className="iems-brand-copy">
            <strong>IEMS</strong>
            <small>Manufacturing Industries Pvt. Ltd.</small>
          </span>
        </button>

        <nav className="iems-sidebar-nav" aria-label="Main navigation">
          <div className="iems-nav-section">
            <p className="iems-nav-section-title">WORKSPACE</p>
            <button
              type="button"
              className={`iems-nav-item ${
                activeScreen === "dashboard" ? "iems-nav-item-active" : ""
              }`}
              onClick={() => navigate("dashboard")}
              aria-current={activeScreen === "dashboard" ? "page" : undefined}
            >
              <span className="iems-nav-icon">⌂</span>
              <span>Dashboard</span>
            </button>
          </div>
          {sidebarSections.map((section) => {
            const sectionModules = visibleModules.filter(
              (module) =>
                module.section === section && module.id !== "front-desk"
            );

            if (sectionModules.length === 0) return null;

            return (
              <div className="iems-nav-section" key={section}>
                <p className="iems-nav-section-title">{section}</p>
                {sectionModules.map((module) => (
                  <button
                    type="button"
                    key={module.id}
                    className={`iems-nav-item ${
                      activeScreen === module.id ||
                      (activeScreen === "new-enquiry" &&
                        module.id === "front-desk") ||
                      ((activeScreen === "employee-create" ||
                        activeScreen.startsWith("employee-view:")) &&
                        module.id === "employee-master")
                        ? "iems-nav-item-active"
                        : ""
                    }`}
                    aria-current={
                      activeScreen === module.id ||
                      (activeScreen === "new-enquiry" &&
                        module.id === "front-desk") ||
                      ((activeScreen === "employee-create" ||
                        activeScreen.startsWith("employee-view:")) &&
                        module.id === "employee-master")
                        ? "page"
                        : undefined
                    }
                    onClick={() =>
                      navigate(
                        module.id === "front-desk" ? "dashboard" : module.id
                      )
                    }
                  >
                    <span className="iems-nav-icon">{module.icon}</span>
                    <span>{module.title}</span>
                  </button>
                ))}
              </div>
            );
          })}
        </nav>

        <footer className="iems-sidebar-footer">
          <span>VERSION 1.0.0</span>
          <span>INTELLIGENT ENTERPRISE SYSTEM</span>
        </footer>
      </aside>

      <div className="iems-main-area">
        <header className="iems-topbar">
          <div className="iems-company-name">
            IEMS Manufacturing Industries Pvt. Ltd.
          </div>

          <label className="iems-global-search">
            <span aria-hidden="true">⌕</span>
            <input
              type="search"
              placeholder="Search this screen…"
              aria-label="Search enquiries"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <kbd>Ctrl K</kbd>
          </label>

          <div className="iems-profile-area">
            <button
              type="button"
              className="iems-profile-trigger"
              onClick={() => setProfileOpen((open) => !open)}
              aria-expanded={profileOpen}
            >
              <span className="iems-avatar">{initials || "U"}</span>
              <span className="iems-profile-copy">
                <strong>{displayName}</strong>
                <small>{primaryAssignment?.role.name ?? "Employee"}</small>
              </span>
              <span aria-hidden="true">⌄</span>
            </button>

            {profileOpen && (
              <div className="iems-profile-menu">
                <strong>{displayName}</strong>
                <span>{user.email}</span>
                <button type="button" onClick={onLogout}>
                  Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        <section className="iems-workspace-content">
          {renderScreen()}
        </section>
      </div>
    </main>
  );
}
