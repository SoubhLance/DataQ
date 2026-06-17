export interface Operation {
  type: string;
  time: string;
  description: string;
  params?: Record<string, any>;
}

export type TaskStatus = "queued" | "running" | "completed" | "failed";

export interface Task {
  task_id: string;
  session_id: string;
  type: string;
  status: TaskStatus;
  progress: number;
  message: string;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface WebSocketProgressPayload {
  type: "progress";
  task_id: string;
  task_type: string;
  status: TaskStatus;
  progress: number;
  message: string;
  error?: string;
  result?: any;
}
