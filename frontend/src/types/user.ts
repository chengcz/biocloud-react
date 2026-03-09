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

/** Brief user info for nested responses */
export interface UserBrief {
  id: number;
  username: string;
  name: string;
  avatar?: string;
}