import React, { useState } from 'react';
import { 
  Users, 
  UserPlus, 
  Shield, 
  Send, 
  Search, 
  X,
  CheckCircle2
} from 'lucide-react';
import { User, Task } from '../types';
import { userService, taskService } from '../services/api';

interface InternalManagementProps {
  onAddTask?: (task: Task) => void;
  defaultSubTab?: 'users' | 'tasks';
  users: User[];
  setUsers: React.Dispatch<React.SetStateAction<User[]>>;
}

export default function InternalManagement({ onAddTask, defaultSubTab, users, setUsers }: InternalManagementProps) {
  const [activeSubTab, setActiveSubTab] = useState<'users' | 'tasks'>(defaultSubTab ?? 'users');

  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span>首页</span>
          <span>/</span>
          <span className="text-slate-900 font-medium">内部管理</span>
        </div>
      </header>

      {/* Sub-navigation */}
      <div className="bg-white border-b border-slate-200 px-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveSubTab('users')}
            className={`py-4 px-2 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${
              activeSubTab === 'users'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Users size={18} />
            人员与权限
          </button>
          <button
            onClick={() => setActiveSubTab('tasks')}
            className={`py-4 px-2 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${
              activeSubTab === 'tasks'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Send size={18} />
            发布任务
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden bg-slate-50 p-6">
        {activeSubTab === 'users' ? (
          <UserManagement users={users} setUsers={setUsers} />
        ) : (
          <TaskPublishing users={users} onAddTask={onAddTask} />
        )}
      </div>
    </div>
  );
}

// --- User Management Component ---
interface UserManagementProps {
  users: User[];
  setUsers: React.Dispatch<React.SetStateAction<User[]>>;
}

function UserManagement({ users, setUsers }: UserManagementProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<Partial<User>>({
    role: '人员',
    status: 'Active',
    department: '技术部'
  });

  const handleOpenAdd = () => {
    setEditingUser(null);
    setFormData({ role: '人员', status: 'Active', department: '技术部' });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (user: User) => {
    setEditingUser(user);
    setFormData({ ...user });
    setIsModalOpen(true);
  };

  const handleSaveUser = async () => {
    if (!formData.name) return;
    
    if (editingUser) {
      const updatedUser = { ...editingUser, ...formData } as User;
      try {
        await userService.update(editingUser.id, updatedUser);
        setUsers(users.map(u => u.id === editingUser.id ? updatedUser : u));
      } catch (error) {
        console.error('Failed to update user:', error);
      }
    } else {
      const user: User = {
        id: Date.now().toString(),
        name: formData.name,
        role: formData.role as User['role'],
        department: formData.department || 'General',
        status: formData.status as User['status']
      };
      
      try {
        const createdUser = await userService.create(user);
        setUsers([...users, createdUser]);
      } catch (error) {
        console.error('Failed to create user:', error);
      }
    }
    
    setIsModalOpen(false);
  };

  const handleDeleteUser = async (id: string) => {
    if (window.confirm('确定要删除该用户吗？')) {
      try {
        await userService.delete(id);
        setUsers(users.filter(u => u.id !== id));
      } catch (error) {
        console.error('Failed to delete user:', error);
      }
    }
  };

  return (
    <div className="h-full flex flex-col max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-slate-800">人员列表</h2>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="搜索人员..." 
              className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button 
            onClick={handleOpenAdd}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <UserPlus size={18} />
            添加人员
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex-1">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 font-semibold text-slate-600 text-sm">姓名</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-sm">部门</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-sm">角色/权限</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-sm">状态</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-sm text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users.map(user => (
              <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                      {user.name.slice(0, 1)}
                    </div>
                    <span className="font-medium text-slate-700">{user.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-slate-500 text-sm">{user.department}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user.role === '管理员' ? 'bg-purple-100 text-purple-700' :
                    user.role === '人员' ? 'bg-blue-100 text-blue-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    <Shield size={12} />
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {user.status === 'Active' ? '活跃' : '禁用'}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => handleOpenEdit(user)}
                    className="text-slate-400 hover:text-blue-600 mr-3"
                  >
                    编辑
                  </button>
                  <button 
                    onClick={() => handleDeleteUser(user.id)}
                    className="text-slate-400 hover:text-red-600"
                  >
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-xl shadow-2xl p-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-800">
                {editingUser ? '编辑人员' : '添加新人员'}
              </h3>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">姓名</label>
                <input 
                  type="text" 
                  value={formData.name || ''}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入姓名"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">部门</label>
                  <input 
                    type="text" 
                    value={formData.department || ''}
                    onChange={e => setFormData({...formData, department: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入部门"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">角色权限</label>
                  <select 
                    value={formData.role}
                    onChange={e => setFormData({...formData, role: e.target.value as any})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="人员">人员</option>
                    <option value="管理员">管理员</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  取消
                </button>
                <button 
                  onClick={handleSaveUser}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
                >
                  {editingUser ? '保存修改' : '确认添加'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Task Publishing Component ---
interface TaskPublishingProps {
  users: User[];
  onAddTask?: (task: Task) => void;
}

function TaskPublishing({ users, onAddTask }: TaskPublishingProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignee, setAssignee] = useState('');
  const [deadline, setDeadline] = useState('');
  const [priority, setPriority] = useState<Task['priority']>('important-urgent');
  const [isPublished, setIsPublished] = useState(false);

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !assignee) return;
    
    // Create new task object
    const assigneeUser = users.find(u => u.id === assignee);
    const newTask: Task = {
      id: Date.now().toString(),
      title,
      deadline: deadline || undefined,
      description,
      assigneeId: assignee,
      assigneeName: assigneeUser?.name,
      priority,
      status: 'pending',
      category: '内部管理',
      source: 'Internal',
      createdAt: new Date().toISOString().slice(0, 10)
    };

    // Call the onAddTask callback to update the global task list
    if (onAddTask) {
      // NOTE: In a real app, we would wait for API response first. 
      // But since onAddTask updates local state in App.tsx (which is now just a cache), 
      // we should ideally re-fetch or let App.tsx handle the creation.
      // For now, we'll create it via API here and then update parent state via callback.
      
      try {
        const createdTask = await taskService.create(newTask);
        onAddTask(createdTask);
        
        setIsPublished(true);
        setTitle('');
        setDescription('');
        setAssignee('');
        setDeadline('');
        setPriority('important-urgent');

        setTimeout(() => {
          setIsPublished(false);
        }, 3000);
      } catch (error) {
        console.error('Failed to publish task:', error);
      }
    }
  };

  return (
    <div className="h-full max-w-4xl mx-auto flex flex-col">
       <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-800">发布新任务</h2>
        <p className="text-slate-500 text-sm mt-1">创建并分配任务给团队成员，系统将自动通知相关人员。</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 flex-1 overflow-y-auto">
        {isPublished ? (
          <div className="h-full flex flex-col items-center justify-center text-center animate-in fade-in zoom-in duration-300">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
              <CheckCircle2 size={32} />
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">发布成功！</h3>
            <p className="text-slate-500">任务已成功分配给选定的成员，并同步至待办计划。</p>
            <button 
              onClick={() => setIsPublished(false)}
              className="mt-8 text-blue-600 hover:text-blue-700 font-medium"
            >
              继续发布任务
            </button>
          </div>
        ) : (
          <form onSubmit={handlePublish} className="space-y-6 max-w-2xl mx-auto">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">任务标题</label>
              <input 
                type="text" 
                value={title}
                onChange={e => setTitle(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                placeholder="简明扼要地描述任务..."
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">指派给</label>
                <div className="relative">
                  <select 
                    value={assignee}
                    onChange={e => setAssignee(e.target.value)}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white transition-all"
                    required
                  >
                    <option value="" disabled>选择执行人</option>
                    {users.map(u => (
                      <option key={u.id} value={u.id}>{u.name} ({u.department})</option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                    <Users size={16} />
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">优先级</label>
                <select 
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as Task['priority'])}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white transition-all"
                >
                  <option value="important-urgent">重要紧急</option>
                  <option value="important-not-urgent">重要不紧急</option>
                  <option value="urgent-not-important">紧急不重要</option>
                  <option value="not-important-not-urgent">不重要不紧急</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">截止日期</label>
              <input 
                type="date" 
                value={deadline}
                onChange={e => setDeadline(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">任务详情</label>
              <textarea 
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[150px] transition-all"
                placeholder="详细描述任务要求、背景及交付标准..."
              />
            </div>

            <div className="pt-4 flex items-center justify-end gap-4">
              <button 
                type="button" 
                className="px-6 py-3 text-slate-600 hover:bg-slate-100 rounded-lg font-medium transition-colors"
              >
                存草稿
              </button>
              <button 
                type="submit" 
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-lg shadow-blue-600/20 flex items-center gap-2 transition-all transform active:scale-95"
              >
                <Send size={18} />
                立即发布
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
