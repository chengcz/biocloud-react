/** User-related types */

export interface User {
  id: number;
  username: string;
  name: string;
  email?: string;
  phone?: string;
  avatar?: string;
  sex?: string;
  dept_id?: number;
  post_id?: number;
  leader_id?: number;
  status: string;
  login_ip?: string;
  login_date?: string;
  create_time: string;
}

export interface UserCreate {
  username: string;
  password: string;
  name: string;
  email?: string;
  phone?: string;
  dept_id?: number;
  post_id?: number;
  leader_id?: number;
  role_ids?: number[];
}

export interface UserUpdate {
  name?: string;
  email?: string;
  phone?: string;
  sex?: string;
  avatar?: string;
  dept_id?: number;
  post_id?: number;
  leader_id?: number;
  role_ids?: number[];
  status?: string;
}

// Department types
export interface Department {
  id: number;
  name: string;
  parent_id?: number;
  dept_path: string;
  leader_user_id?: number;
  order_num: number;
  status: string;
  create_time: string;
  children?: Department[];
  leader?: UserBrief;
  user_count?: number;
}

export interface DepartmentCreate {
  name: string;
  parent_id?: number;
  leader_user_id?: number;
  order_num?: number;
}

export interface DepartmentUpdate {
  name?: string;
  parent_id?: number;
  leader_user_id?: number;
  order_num?: number;
  status?: string;
}

// Role types
export interface Role {
  id: number;
  name: string;
  role_key: string;
  parent_id?: number;
  is_admin: boolean;
  data_scope_type: string;
  remark?: string;
  status: string;
  create_time: string;
}

export interface RoleCreate {
  name: string;
  role_key: string;
  parent_id?: number;
  data_scope_type?: string;
  remark?: string;
  permission_ids?: number[];
  dept_ids?: number[];
}

// Permission types
export interface Permission {
  id: number;
  key: string;
  name: string;
  description?: string;
  status: string;
}

// Brief user info
export interface UserBrief {
  id: number;
  username: string;
  name: string;
  avatar?: string;
}