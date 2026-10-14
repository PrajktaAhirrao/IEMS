import { useState } from "react";
import SignInForm from "./SignInForm";
import AccessHelpModal from "./AccessHelpModal";

export default function SignInPage() {

  const [isAccessHelpOpen, setIsAccessHelpOpen] = useState(false);
  
  return (
    <main className="signin-shell">
      <header className="signin-topbar">
        <div className="topbar-brand">
          <div className="topbar-logo">i</div>
          <span>IEMS</span>
        </div>

        <div className="topbar-company">
          IEMS Manufacturing Industries Pvt. Ltd.
        </div>
      </header>

      <div className="signin-page">
        <section className="signin-container">
          <div className="signin-brand-panel">
            <div className="brand-content">
              <span className="brand-eyebrow">
                Connected Manufacturing
              </span>

              <h1>
                Your enterprise.
                <br />
                One workspace.
              </h1>

              <p className="brand-description">
                Connect your people, plants, and processes through a
                single enterprise manufacturing system.
              </p>

              <div className="brand-tags">
                <span>Steel Wire</span>
                <span>Steel Wire Rope</span>
                <span>Copper Products</span>
              </div>

              <div className="brand-footer">
                <span className="brand-footer-line" />
                <p>Intelligent Enterprise Manufacturing System</p>
              </div>
            </div>
          </div>

          <section className="signin-form-panel">
            <div className="signin-card">
              <div className="signin-header">
                <span className="signin-eyebrow">
                  Employee Access
                </span>

                <h2>Sign in to IEMS</h2>

                <p>
                  Welcome back. Use your company account to continue.
                </p>
              </div>

              <SignInForm />

              <div className="signin-support">
                <div className="support-divider" />

                <p className="support-label">
                  New to the company?
                </p>

                <button
                  type="button"
                  className="support-link"
                  onClick={() => setIsAccessHelpOpen(true)}
                >
                  Get help accessing your account
                </button>

                <p className="support-note">
                  Access is provided by your company administrator.
                </p>
              </div>
            </div>
          </section>
        </section>
      </div>

      <AccessHelpModal
      isOpen={isAccessHelpOpen}
      onClose={() => setIsAccessHelpOpen(false)}
      />

    </main>
  );
}