import { useState, type FormEvent } from "react";
import { createEmployee } from "./services/employeeMasterApi";
import "./EmployeeMaster.css";

type EmployeeFormProps = {
  legalEntityId: number;
  plantId: number | null;
  onCancel: () => void;
  onCreated: (employee: any) => void;
};

type FormData = {
  full_name: string;
  preferred_name: string;
  date_of_birth: string;
  date_of_joining: string;
  employment_type: string;
  personal_email: string;
  mobile_number: string;
  whatsapp_number: string;
  work_location: string;
};

const initialForm: FormData = {
  full_name: "",
  preferred_name: "",
  date_of_birth: "",
  date_of_joining: "",
  employment_type: "PERMANENT",
  personal_email: "",
  mobile_number: "",
  whatsapp_number: "",
  work_location: "",
};

export default function EmployeeForm({
  legalEntityId,
  plantId,
  onCancel,
  onCreated,
}: EmployeeFormProps) {
  const [form, setForm] = useState<FormData>(initialForm);
  const [centralPlantId, setCentralPlantId] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const selectedPlantId =
    plantId ?? (centralPlantId.trim() ? Number(centralPlantId) : null);

  function updateField<K extends keyof FormData>(
    field: K,
    value: FormData[K],
  ) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!form.full_name.trim()) {
      setError("Enter the employee's full name.");
      return;
    }

    if (!form.date_of_joining) {
      setError("Select the date of joining.");
      return;
    }

    if (!selectedPlantId || !Number.isInteger(selectedPlantId)) {
      setError(
        "A valid plant must be selected. Central HR: enter the authorized plant ID.",
      );
      return;
    }

    setSaving(true);

    try {

      const payload = {
        legal_entity_id: legalEntityId,
        plant_id: selectedPlantId,
        full_name: form.full_name.trim(),
        preferred_name: form.preferred_name.trim() || undefined,
        date_of_birth: form.date_of_birth || null,
        date_of_joining: form.date_of_joining,
        employment_type: form.employment_type as
          | "PERMANENT"
          | "CONTRACT"
          | "TRAINEE"
          | "CONSULTANT",
        personal_email: form.personal_email.trim(),
        personal_mobile: form.mobile_number.trim(),
        work_location: form.work_location.trim(),
      };

      const response = await createEmployee(payload);
      onCreated(response);
    } catch (err: any) {
      const responseData = err?.response?.data;
      const message =
        typeof responseData === "string"
          ? responseData
          : responseData
            ? Object.entries(responseData)
                .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
                .join(" | ")
            : err?.message || "Unable to create the employee record.";

      setError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="employee-page">
    <button
        type="button"
        className="employee-back-button"
        onClick={onCancel}
        disabled={saving}
    >
    ← Back to Employee Master
    </button>

      <div className="employee-page-header">
        <div>
          <h1>Add Employee</h1>
          <p className="employee-subtitle">
            Create a draft employee record. Verify the details before
            proceeding with the employee lifecycle.
          </p>
        </div>
      </div>

      <form className="employee-form" onSubmit={handleSubmit}>
        <section className="employee-form-section">
          <h2>Employment Information</h2>

          <div className="employee-form-grid">
            <label className="employee-field">
              <span>Legal Entity ID</span>
              <input value={legalEntityId} readOnly />
            </label>

            {plantId !== null ? (
              <label className="employee-field">
                <span>Assigned Plant ID</span>
                <input value={plantId} readOnly />
              </label>
            ) : (
              <label className="employee-field">
                <span>Plant ID *</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={centralPlantId}
                  onChange={(event) => setCentralPlantId(event.target.value)}
                  placeholder="Enter an authorized plant ID"
                  required
                />
                <small>
                  Plant selection will be connected to the authorized plant
                  list after the backend endpoint is confirmed.
                </small>
              </label>
            )}

            <label className="employee-field">
              <span>Full Name *</span>
              <input
                value={form.full_name}
                onChange={(event) =>
                  updateField("full_name", event.target.value)
                }
                placeholder="Enter full legal name"
                required
              />
            </label>

            <label className="employee-field">
              <span>Preferred Name</span>
              <input
                value={form.preferred_name}
                onChange={(event) =>
                  updateField("preferred_name", event.target.value)
                }
                placeholder="Name used at work"
              />
            </label>

            <label className="employee-field">
              <span>Date of Joining *</span>
              <input
                type="date"
                value={form.date_of_joining}
                onChange={(event) =>
                  updateField("date_of_joining", event.target.value)
                }
                required
              />
            </label>

            <label className="employee-field">
              <span>Date of Birth</span>
              <input
                type="date"
                value={form.date_of_birth}
                onChange={(event) =>
                  updateField("date_of_birth", event.target.value)
                }
              />
            </label>

            <label className="employee-field">
              <span>Employment Type *</span>
              <select
                value={form.employment_type}
                onChange={(event) =>
                  updateField("employment_type", event.target.value)
                }
                required
              >
                <option value="PERMANENT">Permanent</option>
                <option value="CONTRACT">Contract</option>
                <option value="TRAINEE">Trainee</option>
                <option value="CONSULTANT">Consultant</option>
              </select>
            </label>

            <label className="employee-field">
              <span>Work Location</span>
              <input
                value={form.work_location}
                onChange={(event) =>
                  updateField("work_location", event.target.value)
                }
                placeholder="Building, unit or work location"
              />
            </label>
          </div>
        </section>

        <section className="employee-form-section">
          <h2>Contact Information</h2>

          <div className="employee-form-grid">
            <label className="employee-field">
              <span>Personal Email</span>
              <input
                type="email"
                value={form.personal_email}
                onChange={(event) =>
                  updateField("personal_email", event.target.value)
                }
                placeholder="employee@example.com"
              />
            </label>

            <label className="employee-field">
              <span>Mobile Number</span>
              <input
                type="tel"
                value={form.mobile_number}
                onChange={(event) =>
                  updateField("mobile_number", event.target.value)
                }
                placeholder="Mobile number"
              />
            </label>

            <label className="employee-field">
              <span>WhatsApp Number</span>
              <input
                type="tel"
                value={form.whatsapp_number}
                onChange={(event) =>
                  updateField("whatsapp_number", event.target.value)
                }
                placeholder="WhatsApp number"
              />
            </label>
          </div>
        </section>

        {error && (
          <div className="employee-form-error" role="alert">
            {error}
          </div>
        )}

        <div className="employee-form-actions">
          <button
            type="button"
            className="employee-secondary-button"
            onClick={onCancel}
            disabled={saving}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="employee-primary-button"
            disabled={saving}
          >
            {saving ? "Saving..." : "Create Draft Employee"}
          </button>
        </div>
      </form>
    </section>
  );
}
