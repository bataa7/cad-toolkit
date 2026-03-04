export interface Task {
  id: string;
  title: string;
  createdAt?: string;
  deadline?: string;
  category?: string;
  source?: 'AI' | 'Manual' | 'Internal';
  status: 'pending' | 'completed';
  priority: 'important-urgent' | 'important-not-urgent' | 'urgent-not-important' | 'not-important-not-urgent';
  description?: string;
  assigneeId?: string;
  assigneeName?: string;
  completedAt?: string;
  completionNote?: string;
  completionProcess?: string;
  completionAnalysis?: string;
  completedById?: string;
  completedByName?: string;
}

export interface Document {
  id: string;
  title: string;
  type: 'pdf' | 'doc' | 'xls' | 'ppt' | 'image' | 'other';
  size: string;
  uploadedBy: string;
  uploadedAt: string;
  url: string;
  category?: string;
}

export interface User {
  id: string;
  name: string;
  role: '管理员' | '人员';
  department: string;
  status: 'Active' | 'Inactive';
}
