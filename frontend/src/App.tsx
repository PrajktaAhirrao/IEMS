
import { useCallback, useEffect, useState } from "react";
import SignInPage from "./features/auth/SignInPage";
import AuthenticatedApp from "./features/shell/AuthenticatedApp";
import "./styles/global.css";

type User = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
};

type Assignment = {
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
};

type AuthContext = {
  user: User;
  assignments: Assignment[];
  permissions: string[];
};

const API_URL = "http://127.0.0.1:8000/api/auth";

function App() {
  const [auth, setAuth] = useState<AuthContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [accessError, setAccessError] = useState("");

  const loadSession = useCallback(async () => {
    const token = localStorage.getItem("iems_token");

    if (!token) {
      setAuth(null);
      setLoading(false);
      return;
    }

    setAccessError("");

    try {
      const response = await fetch(`${API_URL}/me/`, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (response.status === 401) {
        localStorage.removeItem("iems_token");
        localStorage.removeItem("iems_user");
        setAuth(null);
        return;
      }

      if (!response.ok) {
        throw new Error("Unable to verify your session.");
      }

      const data = (await response.json()) as AuthContext;

      localStorage.setItem("iems_user", JSON.stringify(data.user));
      setAuth(data);
    } catch {
      setAccessError(
        "Unable to verify your session. Check the IEMS server and try again.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const handleLoginSuccess = () => {
    setLoading(true);
    void loadSession();
  };

  const handleLogout = () => {
    localStorage.removeItem("iems_token");
    localStorage.removeItem("iems_user");
    setAuth(null);
    setAccessError("");
    setLoading(false);
  };

  if (loading) {
    return <main className="signin-shell">Loading IEMS...</main>;
  }

  if (accessError) {
    return (
      <main className="signin-shell">
        <p>{accessError}</p>
        <button
          onClick={() => {
            setLoading(true);
            void loadSession();
          }}
        >
          Retry
        </button>
        <button onClick={handleLogout}>Sign out</button>
      </main>
    );
  }

  if (!auth) {
    return <SignInPage onLoginSuccess={handleLoginSuccess} />;
  }

  if (auth.assignments.length === 0) {
    return (
      <main className="signin-shell">
        <h1>Access not configured</h1>
        <p>
          Your account is authenticated, but no active organizational
          assignment was found. Contact your system administrator.
        </p>
        <button onClick={handleLogout}>Sign out</button>
      </main>
    );
  }

  return (
    <AuthenticatedApp
      user={auth.user}
      assignments={auth.assignments}
      permissions={auth.permissions}
      onLogout={handleLogout}
    />
  );
}

export default App;
