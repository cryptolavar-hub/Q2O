/**
 * Project Management API Client
 * 
 * Handles all project-related API calls for the Tenant Portal.
 */

const API_BASE = process.env.NEXT_PUBLIC_LIC_API || '';
import { getStoredSessionToken } from './auth';

export interface Project {
  id: string;
  name: string;
  client_name?: string;
  description?: string;
  objectives?: string;
  status: 'pending' | 'active' | 'completed' | 'paused' | 'failed';
  activation_code_id?: string;
  execution_status?: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  show_completion_modal?: boolean;  // Whether to show completion modal (default: true)
  created_at: string;
  updated_at: string;
}

export interface ProjectCreatePayload {
  name: string;
  client_name?: string;
  description?: string;
  objectives?: string;
}

export interface ProjectUpdatePayload {
  name?: string;
  client_name?: string;
  description?: string;
  objectives?: string;
  status?: Project['status'];
}

export interface ProjectCollectionResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Get authentication headers
 */
function getAuthHeaders(): HeadersInit {
  const token = getStoredSessionToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  
  return {
    'Content-Type': 'application/json',
    'X-Session-Token': token,
  };
}

/**
 * List all projects for the authenticated tenant
 */
export async function listProjects(
  page: number = 1,
  pageSize: number = 20,
  search?: string,
  status?: Project['status'] | 'all'
): Promise<ProjectCollectionResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  
  if (search) {
    params.append('search', search);
  }
  
  // Note: Backend doesn't support status filtering yet
  // Status filtering is done on the frontend after receiving data

  const response = await fetch(`${API_BASE}/api/tenant/projects?${params}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    
    // Handle FastAPI validation errors (422)
    if (response.status === 422 && Array.isArray(error.detail)) {
      const validationErrors = error.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'field';
        return `${field}: ${err.msg || err.type || 'Invalid value'}`;
      }).join(', ');
      throw new Error(validationErrors || 'Validation failed');
    }
    
    // Handle other error formats
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.detail && typeof error.detail === 'object' && 'message' in error.detail)
        ? String(error.detail.message)
        : (error.message || response.statusText || `Failed to list projects: ${response.status}`);
    throw new Error(errorMessage);
  }

  const data = await response.json();
  
  // Map backend projects to frontend format
  let mappedItems = data.items?.map((item: any) => mapBackendProjectToFrontend(item)) || [];
  
  // Frontend filtering by status (backend doesn't support it yet)
  if (status && status !== 'all') {
    mappedItems = mappedItems.filter((item: Project) => item.status === status);
  }
  
  return {
    ...data,
    items: mappedItems,
    total: status && status !== 'all' ? mappedItems.length : data.total,
  };
}

/**
 * Map backend ProjectResponse to frontend Project format
 * 
 * Backend returns (with camelCase aliases due to alias_generator):
 * - project_id or projectId (string)
 * - client_name or clientName (string) - this is the project name
 * - description (string)
 * - custom_instructions or customInstructions (string) - this maps to objectives
 * - is_active or isActive (boolean) - true = active, false = paused
 * - priority (string)
 * 
 * Note: Backend doesn't support pending/completed/failed statuses,
 * only active (is_active=true) and paused (is_active=false)
 */
function mapBackendProjectToFrontend(backendProject: any): Project {
  // Handle both snake_case and camelCase from backend (due to alias_generator)
  const clientName = backendProject.client_name || backendProject.clientName || '';
  const projectId = backendProject.project_id || backendProject.projectId || backendProject.id || '';
  const description = backendProject.description || '';
  const customInstructions = backendProject.custom_instructions || backendProject.customInstructions || '';
  const isActive = backendProject.is_active !== undefined ? backendProject.is_active : (backendProject.isActive !== undefined ? backendProject.isActive : true);
  
  // Use client_name/clientName as the project name, fallback to project_id if client_name is empty/null
  const projectName = clientName?.trim() || projectId || 'Unnamed Project';
  
  // Map is_active/isActive boolean to status string
  // Backend only supports active/paused, so we map:
  // - is_active=true → 'active'
  // - is_active=false → 'paused'
  // Frontend statuses like 'pending', 'completed', 'failed' are not supported by backend
  const status: Project['status'] = isActive === false ? 'paused' : 'active';
  
  // Handle execution_status (from backend execution tracking)
  const executionStatus = backendProject.execution_status || backendProject.executionStatus;
  
  // Handle show_completion_modal (from backend UI preferences)
  const showCompletionModal = backendProject.show_completion_modal !== undefined 
    ? backendProject.show_completion_modal 
    : (backendProject.showCompletionModal !== undefined ? backendProject.showCompletionModal : true);
  
  return {
    id: projectId,
    name: projectName,
    client_name: clientName || undefined,  // Preserve original client_name for editing
    description: description || undefined,
    objectives: customInstructions || undefined,  // Map custom_instructions/customInstructions to objectives
    status: status,
    activation_code_id: backendProject.activation_code_id || backendProject.activationCodeId,
    execution_status: executionStatus || undefined,
    show_completion_modal: showCompletionModal,
    created_at: backendProject.created_at || backendProject.createdAt || new Date().toISOString(),
    updated_at: backendProject.updated_at || backendProject.updatedAt || backendProject.created_at || backendProject.createdAt || new Date().toISOString(),
  };
}

/**
 * Get a single project by ID
 */
export async function getProject(projectId: string): Promise<Project> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    if (response.status === 404) {
      throw new Error('Project not found');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    
    // Handle FastAPI validation errors (422)
    if (response.status === 422 && Array.isArray(error.detail)) {
      const validationErrors = error.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'field';
        return `${field}: ${err.msg || err.type || 'Invalid value'}`;
      }).join(', ');
      throw new Error(validationErrors || 'Validation failed');
    }
    
    // Handle other error formats
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.detail && typeof error.detail === 'object' && 'message' in error.detail)
        ? String(error.detail.message)
        : (error.message || response.statusText || `Failed to get project: ${response.status}`);
    throw new Error(errorMessage);
  }

  const backendProject = await response.json();
  return mapBackendProjectToFrontend(backendProject);
}

/**
 * Create a new project
 */
export async function createProject(payload: ProjectCreatePayload): Promise<Project> {
  const response = await fetch(`${API_BASE}/api/tenant/projects`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    
    // Handle FastAPI validation errors (422)
    if (response.status === 422 && Array.isArray(error.detail)) {
      const validationErrors = error.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'field';
        return `${field}: ${err.msg || err.type || 'Invalid value'}`;
      }).join(', ');
      throw new Error(validationErrors || 'Validation failed');
    }
    
    // Handle 500 errors with detailed messages
    if (response.status === 500) {
      // Check if it's a project ID conflict
      const errorDetail = typeof error.detail === 'string' ? error.detail : '';
      if (errorDetail.includes('already exists') || errorDetail.includes('Project with ID')) {
        throw new Error('A project with this name already exists. Please choose a different project name.');
      }
      // Check for other specific error messages
      if (errorDetail) {
        throw new Error(errorDetail);
      }
    }
    
    // Handle other error formats
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.detail && typeof error.detail === 'object' && 'message' in error.detail)
        ? String(error.detail.message)
        : (error.message || response.statusText || `Failed to create project: ${response.status}`);
    throw new Error(errorMessage);
  }

  const backendProject = await response.json();
  return mapBackendProjectToFrontend(backendProject);
}

/**
 * Update an existing project
 */
export async function updateProject(
  projectId: string,
  payload: ProjectUpdatePayload
): Promise<Project> {
  // Map frontend payload to backend format
  // Backend expects: client_name, description, custom_instructions, is_active (boolean)
  const backendPayload: any = {};
  
  // Map name to client_name (name takes precedence if both provided)
  if (payload.name !== undefined && payload.name.trim()) {
    backendPayload.client_name = payload.name.trim();
  } else if (payload.client_name !== undefined && payload.client_name.trim()) {
    backendPayload.client_name = payload.client_name.trim();
  }
  
  if (payload.description !== undefined) {
    backendPayload.description = payload.description.trim() || null;
  }
  
  if (payload.objectives !== undefined) {
    // Backend uses custom_instructions, not objectives
    backendPayload.custom_instructions = payload.objectives.trim() || null;
  }
  
  if (payload.status !== undefined) {
    // Backend uses is_active boolean, not status string
    // Only 'active' maps to is_active=true, all others map to is_active=false (paused)
    // Note: Backend doesn't support pending/completed/failed, only active/paused
    backendPayload.is_active = payload.status === 'active';
  }

  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(backendPayload),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    if (response.status === 404) {
      throw new Error('Project not found');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    
    // Handle FastAPI validation errors (422)
    if (response.status === 422 && Array.isArray(error.detail)) {
      const validationErrors = error.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'field';
        return `${field}: ${err.msg || err.type || 'Invalid value'}`;
      }).join(', ');
      throw new Error(validationErrors || 'Validation failed');
    }
    
    // Handle other error formats
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.detail && typeof error.detail === 'object' && 'message' in error.detail)
        ? String(error.detail.message)
        : (error.message || response.statusText || `Failed to update project: ${response.status}`);
    throw new Error(errorMessage);
  }

  const backendProject = await response.json();
  return mapBackendProjectToFrontend(backendProject);
}

/**
 * Delete a project
 */
export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    if (response.status === 404) {
      throw new Error('Project not found');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    
    // Handle FastAPI validation errors (422)
    if (response.status === 422 && Array.isArray(error.detail)) {
      const validationErrors = error.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'field';
        return `${field}: ${err.msg || err.type || 'Invalid value'}`;
      }).join(', ');
      throw new Error(validationErrors || 'Validation failed');
    }
    
    // Handle other error formats
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.detail && typeof error.detail === 'object' && 'message' in error.detail)
        ? String(error.detail.message)
        : (error.message || response.statusText || `Failed to delete project: ${response.status}`);
    throw new Error(errorMessage);
  }
}

/**
 * Assign an activation code to a project
 */
export async function assignActivationCode(projectId: string, activationCode: string): Promise<Project> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}/assign-activation-code`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ activation_code: activationCode }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.message || response.statusText || `Failed to assign activation code: ${response.status}`);
    throw new Error(errorMessage);
  }

  const backendProject = await response.json();
  return mapBackendProjectToFrontend(backendProject);
}

/**
 * Run a project execution
 */
export async function runProject(projectId: string): Promise<{
  success: boolean;
  message: string;
  execution_id?: number;
  status?: string;
  output_folder_path?: string;
}> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}/run`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.message || response.statusText || `Failed to run project: ${response.status}`);
    throw new Error(errorMessage);
  }

  return await response.json();
}

/**
 * Update completion modal preference for a project
 */
export async function updateCompletionModalPreference(
  projectId: string,
  showModal: boolean
): Promise<{ success: boolean; project_id: string; show_completion_modal: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}/completion-modal-preference?show_modal=${showModal}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    if (response.status === 404) {
      throw new Error('Project not found');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.message || response.statusText || `Failed to update completion modal preference: ${response.status}`);
    throw new Error(errorMessage);
  }

  return await response.json();
}

/**
 * Restart a failed project execution
 */
export async function restartProject(projectId: string): Promise<{
  success: boolean;
  message: string;
  execution_id?: number;
  status?: string;
  output_folder_path?: string;
}> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}/restart`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const errorMessage = typeof error.detail === 'string' 
      ? error.detail 
      : (error.message || response.statusText || `Failed to restart project: ${response.status}`);
    throw new Error(errorMessage);
  }

  return await response.json();
}

