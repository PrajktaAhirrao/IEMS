
import { useState, type FormEvent } from "react";
import "./EnquiryForm.css";

interface EnquiryFormProps {
  legalEntityId: number;
  onBack: () => void;
}

interface EnquiryResponse {
  reference_id?: string;
  detail?: string;
  [key: string]: unknown;
}

const API_URL = "http://127.0.0.1:8000/api/commercial/enquiries/";

const INITIAL_FORM = {
  contact_name: "",
  company_name: "",
  email: "",
  phone_country_code: "+91",
  phone_number: "",
  whatsapp_available: false,
  channel: "PHONE",
  source: "DIRECT",
  source_details: "",
  intent: "GENERAL_INQUIRY",
  enquiry_details: "",
};

export default function EnquiryForm({
  legalEntityId,
  onBack,
}: EnquiryFormProps) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function updateField(
    field: keyof typeof INITIAL_FORM,
    value: string | boolean
  ) {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    const token = localStorage.getItem("iems_token");

    if (!token) {
      setError("Your session has expired. Please sign in again.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify({
          ...form,
          legal_entity_id: legalEntityId,
        }),
      });

      const data: EnquiryResponse = await response
        .json()
        .catch(() => ({}));

      if (!response.ok) {
        const message =
          typeof data.detail === "string"
            ? data.detail
            : Object.entries(data)
                .map(([field, messages]) => {
                  const readableMessages = Array.isArray(messages)
                    ? messages.join(", ")
                    : String(messages);

                  return `${field}: ${readableMessages}`;
                })
                .join("\n");

        throw new Error(
          message || `Unable to save enquiry (${response.status}).`
        );
      }

      setSuccess(
        `Enquiry created successfully. Reference: ${
          data.reference_id ?? "Created"
        }`
      );

      setForm({ ...INITIAL_FORM });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while saving the enquiry."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="fd-enquiry">
      <button
        type="button"
        className="fd-back-button"
        onClick={onBack}
        disabled={loading}
      >
        ← Back to Commercial Front Desk Dashboard
      </button>

      <header className="fd-page-heading">
        <div>
          <h1>Register New Enquiry</h1>
          <p>
            Capture customer contact details and understand their initial
            business requirement.
          </p>
        </div>

        <span className="fd-screen-code">FD / ENQ-001</span>
      </header>

      {error && (
        <div className="fd-alert fd-alert-error" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="fd-alert fd-alert-success" role="status">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="fd-form-panel">
        <div className="fd-form-panel-header">
          <div>
            <h2>Enquiry Information</h2>
            <p>Enter the available details provided by the contact.</p>
          </div>

          <span className="fd-required-note">
            <span className="fd-required-mark">*</span> Required fields
          </span>
        </div>

        <div className="fd-form-body">
          <section className="fd-form-section">
            <h3 className="fd-section-heading">
              <span className="fd-section-number">01</span>
              Contact Information
            </h3>

            <div className="fd-form-grid">
              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="contact_name">
                  Contact Name <span className="fd-required-mark">*</span>
                </label>
                <input
                  className="fd-form-control"
                  id="contact_name"
                  name="contact_name"
                  value={form.contact_name}
                  onChange={(e) =>
                    updateField("contact_name", e.target.value)
                  }
                  maxLength={200}
                  required
                  autoComplete="name"
                  placeholder="Enter contact person's name"
                />
              </div>

              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="company_name">
                  Company Name
                </label>
                <input
                  className="fd-form-control"
                  id="company_name"
                  name="company_name"
                  value={form.company_name}
                  onChange={(e) =>
                    updateField("company_name", e.target.value)
                  }
                  maxLength={255}
                  autoComplete="organization"
                  placeholder="Enter company name"
                />
              </div>

              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="email">
                  Email Address
                </label>
                <input
                  className="fd-form-control"
                  id="email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={(e) => updateField("email", e.target.value)}
                  autoComplete="email"
                  placeholder="customer@example.com"
                />
              </div>

              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="phone_number">
                  Phone Number
                </label>
                <div className="fd-phone-grid">
                  <input
                    className="fd-form-control"
                    aria-label="Phone country code"
                    id="phone_country_code"
                    name="phone_country_code"
                    value={form.phone_country_code}
                    onChange={(e) =>
                      updateField("phone_country_code", e.target.value)
                    }
                    maxLength={8}
                    placeholder="+91"
                  />
                  <input
                    className="fd-form-control"
                    id="phone_number"
                    name="phone_number"
                    type="tel"
                    value={form.phone_number}
                    onChange={(e) =>
                      updateField("phone_number", e.target.value)
                    }
                    maxLength={30}
                    autoComplete="tel-national"
                    placeholder="Enter phone number"
                  />
                </div>
              </div>

              <div className="fd-form-field fd-form-field-full">
                <label
                  className="fd-checkbox-field"
                  htmlFor="whatsapp_available"
                >
                  <input
                    id="whatsapp_available"
                    name="whatsapp_available"
                    type="checkbox"
                    checked={form.whatsapp_available}
                    onChange={(e) =>
                      updateField("whatsapp_available", e.target.checked)
                    }
                  />
                  <span>WhatsApp available for this contact</span>
                </label>
              </div>
            </div>
          </section>

          <section className="fd-form-section">
            <h3 className="fd-section-heading">
              <span className="fd-section-number">02</span>
              Enquiry Classification
            </h3>

            <div className="fd-form-grid">
              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="channel">
                  Enquiry Channel <span className="fd-required-mark">*</span>
                </label>
                <select
                  className="fd-form-control"
                  id="channel"
                  name="channel"
                  value={form.channel}
                  onChange={(e) => updateField("channel", e.target.value)}
                  required
                >
                  <option value="PHONE">Phone</option>
                  <option value="EMAIL">Email</option>
                  <option value="IN_PERSON">In Person</option>
                  <option value="WEBSITE">Website</option>
                  <option value="ONLINE_MEETING">Online Meeting</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>

              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="source">
                  Enquiry Source <span className="fd-required-mark">*</span>
                </label>
                <select
                  className="fd-form-control"
                  id="source"
                  name="source"
                  value={form.source}
                  onChange={(e) => updateField("source", e.target.value)}
                  required
                >
                  <option value="DIRECT">Direct Enquiry</option>
                  <option value="REFERRAL">Referral</option>
                  <option value="CAMPAIGN">Marketing Campaign</option>
                  <option value="WEBSITE">Website</option>
                  <option value="EXISTING_CUSTOMER">Existing Customer</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>

              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="source_details">
                  Source Details
                </label>
                <input
                  className="fd-form-control"
                  id="source_details"
                  name="source_details"
                  value={form.source_details}
                  onChange={(e) =>
                    updateField("source_details", e.target.value)
                  }
                  maxLength={255}
                  placeholder="Referral name, campaign, etc."
                />
              </div>

              <div className="fd-form-field">
                <label className="fd-form-label" htmlFor="intent">
                  Customer Intent <span className="fd-required-mark">*</span>
                </label>
                <select
                  className="fd-form-control"
                  id="intent"
                  name="intent"
                  value={form.intent}
                  onChange={(e) => updateField("intent", e.target.value)}
                  required
                >
                  <option value="GENERAL_INQUIRY">General Inquiry</option>
                  <option value="PRODUCT_REQUIREMENT">
                    Product Requirement
                  </option>
                  <option value="QUOTATION_REQUEST">Quotation Request</option>
                  <option value="CONTRACTUAL_DISCUSSION">
                    Contractual Discussion
                  </option>
                  <option value="AFTER_SALES">After-Sales Support</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>
          </section>

          <section className="fd-form-section">
            <h3 className="fd-section-heading">
              <span className="fd-section-number">03</span>
              Requirement Notes
            </h3>

            <div className="fd-form-field">
              <label className="fd-form-label" htmlFor="enquiry_details">
                Enquiry Details
              </label>
              <textarea
                className="fd-form-control fd-form-textarea"
                id="enquiry_details"
                name="enquiry_details"
                value={form.enquiry_details}
                onChange={(e) =>
                  updateField("enquiry_details", e.target.value)
                }
                placeholder="Describe the customer's requirement, product, quantity, application, or other relevant details."
              />
            </div>
          </section>
        </div>

        <footer className="fd-form-footer">
          <span className="fd-form-footer-note">
            IEMS / COMMERCIAL / FRONT DESK
          </span>

          <div className="fd-form-actions">
            <button
              type="button"
              className="fd-button fd-button-secondary"
              onClick={onBack}
              disabled={loading}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="fd-button fd-button-primary"
              disabled={loading}
            >
              {loading ? "Saving..." : "Register Enquiry →"}
            </button>
          </div>
        </footer>
      </form>
    </section>
  );
}
