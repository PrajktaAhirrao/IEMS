type AccessHelpModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

export default function AccessHelpModal({
  isOpen,
  onClose,
}: AccessHelpModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="access-help-overlay"
      role="presentation"
      onMouseDown={onClose}
    >
      <section
        className="access-help-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="access-help-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="access-help-header">
          <div>
            <span className="access-help-eyebrow">
              IEMS Access Guide
            </span>

            <h2 id="access-help-title">
              Getting access to IEMS
            </h2>

            <p>
              IEMS accounts are created and managed by your
              company administrator.
            </p>
          </div>

          <button
            type="button"
            className="access-help-close"
            onClick={onClose}
            aria-label="Close access guide"
          >
            ×
          </button>
        </div>

        <div className="access-help-content">
          <div className="access-help-step">
            <span className="access-help-number">1</span>

            <div>
              <h3>Request an IEMS account</h3>
              <p>
                Contact your company administrator or authorized
                department manager and request access to IEMS.
              </p>
            </div>
          </div>

          <div className="access-help-step">
            <span className="access-help-number">2</span>

            <div>
              <h3>Use your registered work email</h3>
              <p>
                Sign in using the work email address registered
                against your employee account.
              </p>
            </div>
          </div>

          <div className="access-help-step">
            <span className="access-help-number">3</span>

            <div>
              <h3>If your email is not recognized</h3>
              <p>
                Confirm that your employee account has been created,
                activated, and assigned access by an administrator.
              </p>
            </div>
          </div>

          <div className="access-help-step">
            <span className="access-help-number">4</span>

            <div>
              <h3>If you forgot your password</h3>
              <p>
                Use the Forgot password option or contact the system
                administrator if password recovery is unavailable.
              </p>
            </div>
          </div>

          <div className="access-help-step">
            <span className="access-help-number">5</span>

            <div>
              <h3>If your account is inactive</h3>
              <p>
                Access may have been disabled or may still be awaiting
                activation. Contact your administrator for review.
              </p>
            </div>
          </div>
        </div>

        <div className="access-help-security">
          <strong>Security reminder</strong>
          <p>
            Never share your IEMS password with another employee.
            Access permissions are assigned individually.
          </p>
        </div>

        <div className="access-help-actions">
          <button
            type="button"
            className="access-help-primary"
            onClick={onClose}
          >
            Back to sign in
          </button>
        </div>
      </section>
    </div>
  );
}