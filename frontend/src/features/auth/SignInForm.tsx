import { FormEvent, useState } from "react";

type LoginResponse = {
  token: string;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    is_superuser: boolean;
  };
};

export default function SignInForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    let isValid = true;

    setEmailError("");
    setPasswordError("");
    setFormError("");
    setSuccessMessage("");

    if (!email.trim()) {
      setEmailError("Work email is required.");
      isValid = false;
    } else if (
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
    ) {
      setEmailError("Enter a valid work email address.");
      isValid = false;
    }

    if (!password) {
      setPasswordError("Password is required.");
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/login/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        },
      );

      const data = (await response.json()) as LoginResponse & {
        detail?: string;
      };

      if (!response.ok) {
        setFormError(
          data.detail || "Unable to sign in.",
        );
        return;
      }

      localStorage.setItem("iems_token", data.token);
      localStorage.setItem(
        "iems_user",
        JSON.stringify(data.user),
      );

      setSuccessMessage(
        `Signed in as ${data.user.email}`,
      );
    } catch {
      setFormError(
        "Unable to connect to the IEMS server.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      className="signin-form"
      onSubmit={handleSubmit}
      noValidate
    >
      <div className="form-field">
        <label htmlFor="email">
          Work email
        </label>

        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) =>
            setEmail(event.target.value)
          }
          className={
            emailError ? "input-error" : ""
          }
          placeholder="name@company.com"
        />

        {emailError && (
          <p className="field-error">
            {emailError}
          </p>
        )}
      </div>

      <div className="form-field">
        <div className="password-label-row">
          <label htmlFor="password">
            Password
          </label>

          <button
            type="button"
            className="text-action"
          >
            Forgot password?
          </button>
        </div>

        <div className="password-input-wrap">
          <input
            id="password"
            type={
              showPassword
                ? "text"
                : "password"
            }
            autoComplete="current-password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            className={
              passwordError
                ? "input-error"
                : ""
            }
            placeholder="Enter your password"
          />

          <button
            type="button"
            className="password-toggle"
            onClick={() =>
              setShowPassword(
                (current) => !current,
              )
            }
          >
            {showPassword
              ? "Hide"
              : "Show"}
          </button>
        </div>

        {passwordError && (
          <p className="field-error">
            {passwordError}
          </p>
        )}
      </div>

      {formError && (
        <div className="form-message error">
          {formError}
        </div>
      )}

      {successMessage && (
        <div className="form-message success">
          {successMessage}
        </div>
      )}

      <button
        type="submit"
        className="signin-button"
        disabled={isSubmitting}
      >
        <span>
          {isSubmitting
            ? "Signing in..."
            : "Sign in"}
        </span>

        {!isSubmitting && (
          <span className="button-arrow">
            →
          </span>
        )}
      </button>
    </form>
  );
}