const API_URL = "http://127.0.0.1:8000/api/employees/";

export type Employee = {
  id: string;
  employee_code: string;
  user: number | null;
  full_name: string;
  preferred_name: string;
  profile_photo: string | null;
  date_of_birth: string | null;
  date_of_joining: string | null;
  employment_type: "PERMANENT" | "CONTRACT" | "TRAINEE" | "CONSULTANT" | "";
  employment_status: "ACTIVE" | "ON_LEAVE" | "SUSPENDED" | "SEPARATED";
  record_status: "DRAFT" | "PENDING_VERIFICATION" | "VERIFIED";
  legal_entity: number | null;
  plant: number | null;
  department: number | null;
  organizational_unit: number | null;
  designation: string;
  reporting_manager: string | null;
  work_location: string;
  personal_email: string;
  personal_mobile: string;
  whatsapp_available: boolean | null;
  current_address: string;
  permanent_address: string;
  emergency_contact_name: string;
  emergency_contact_relationship: string;
  emergency_contact_mobile: string;
  created_by: number;
  verified_by: number | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
};

export type EmployeePayload = {
  legal_entity_id: number;
  plant_id: number;
  full_name: string;
  preferred_name?: string;
  date_of_birth?: string | null;
  date_of_joining?: string | null;
  employment_type: Employee["employment_type"];
  employment_status?: Employee["employment_status"];
  department?: number | null;
  organizational_unit?: number | null;
  designation?: string;
  reporting_manager?: string | null;
  work_location?: string;
  personal_email?: string;
  personal_mobile?: string;
  whatsapp_available?: boolean | null;
  current_address?: string;
  permanent_address?: string;
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_mobile?: string;
};

type EmployeeListResponse = Employee[] | { results: Employee[] };

async function request<T>(
  url: string,
  init: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("iems_token");

  if (!token) {
    throw new Error("Your session has expired. Please sign in again.");
  }

  const response = await fetch(url, {
    ...init,
    headers: {
      Authorization: `Token ${token}`,
      ...(init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  });

  if (!response.ok) {
    let message = "Unable to complete the employee request.";

    try {
      const data = await response.json();
      if (typeof data === "string") {
        message = data;
      } else if (data && typeof data === "object") {
        message = Object.entries(data)
          .map(([field, value]) => {
            const detail = Array.isArray(value)
              ? value.join(", ")
              : typeof value === "string"
                ? value
                : JSON.stringify(value);
            return `${field}: ${detail}`;
          })
          .join(" | ");
      }
    } catch {
      // Keep the default message if the response is not JSON.
    }

    if (response.status === 401) {
      throw new Error("Your session has expired. Please sign in again.");
    }

    if (response.status === 403) {
      throw new Error("You do not have permission to access this plant.");
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}


export async function getEmployees(
  legalEntityId: number,
  plantId: number | null,
): Promise<Employee[]> {
  const params = new URLSearchParams({
    legal_entity_id: String(legalEntityId),
  });

  if (plantId !== null) {
    params.set("plant_id", String(plantId));
  }

  const data = await request<EmployeeListResponse>(
    `${API_URL}?${params.toString()}`,
  );

  return Array.isArray(data) ? data : data.results ?? [];
}


export async function getEmployee(
  employeeId: string,
  legalEntityId: number,
): Promise<Employee> {
  const params = new URLSearchParams({
    legal_entity_id: String(legalEntityId),
  });

  return request<Employee>(
    `${API_URL}${encodeURIComponent(employeeId)}/?${params.toString()}`,
  );
}

export async function createEmployee(
  payload: EmployeePayload,
): Promise<Employee> {
  return request<Employee>(API_URL, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateEmployee(
  employeeId: string,
  legalEntityId: number,
  payload: Partial<EmployeePayload>,
): Promise<Employee> {
  const params = new URLSearchParams({
    legal_entity_id: String(legalEntityId),
  });

  return request<Employee>(
    `${API_URL}${encodeURIComponent(employeeId)}/?${params.toString()}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}
