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
  status?: Project['status']
): Promise<ProjectCollectionResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  
  if (search) {
    params.append('search', search);
  }
  
  if (status) {
    params.append('status', status);
  }

  const response = await fetch(`${API_BASE}/api/tenant/projects?${params}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to list projects: ${response.status}`);
  }

  return response.json();
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
    throw new Error(error.detail || `Failed to get project: ${response.status}`);
  }

  return response.json();
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
    throw new Error(error.detail || `Failed to create project: ${response.status}`);
  }

  return response.json();
}

/**
 * Update an existing project
 */
export async function updateProject(
  projectId: string,
  payload: ProjectUpdatePayload
): Promise<Project> {
  const response = await fetch(`${API_BASE}/api/tenant/projects/${projectId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please login again.');
    }
    if (response.status === 404) {
      throw new Error('Project not found');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to update project: ${response.status}`);
  }

  return response.json();
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
    throw new Error(error.detail || `Failed to delete project: ${response.status}`);
  }
}

