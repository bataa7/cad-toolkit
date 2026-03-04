import React, { useState } from 'react';
import { 
  Bot, 
  Briefcase,
  ListTodo,
  Send,
  CheckCircle2,
  FileText,
  Download
} from 'lucide-react';
import * as XLSX from 'xlsx';
import TodoPlan from './TodoPlan';
import InternalManagement from './InternalManagement';
import ReferenceRoom from './ReferenceRoom';
import { Task, User } from '../types';

interface DashboardProps {
  currentUser: User;
  onLogout: () => void;
  tasks: Task[];
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  users: User[];
  setUsers: React.Dispatch<React.SetStateAction<User[]>>;
}

export default function Dashboard({ currentUser, onLogout, tasks, setTasks, users, setUsers }: DashboardProps) {
  const [activeTab, setActiveTab] = useState('my-todos');
  const isAdmin = currentUser.role === '管理员';
  const visibleActiveTab = (!isAdmin && activeTab === 'internal') ? 'my-todos' : activeTab;

  const handleAddTask = (task: Task) => {
    setTasks(prev => [...prev, task]);
  };
  
  return (
    <div className="flex h-screen bg-slate-950">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col">
        <div className="p-4 flex items-center gap-2 mb-2 px-6 justify-between">
          <Bot className="w-8 h-8 text-cyan-400" />
          <span className="font-bold text-lg text-slate-200">待办</span>
        </div>
        <div className="px-6 pb-3 text-xs text-slate-400">
          <div className="flex items-center justify-between">
            <span>{currentUser.name}（{currentUser.role}）</span>
            <button
              onClick={onLogout}
              className="text-slate-400 hover:text-red-400"
            >
              退出
            </button>
          </div>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-2 px-3 space-y-1 custom-scrollbar">
          <SidebarItem 
            icon={<ListTodo size={18} />} 
            label="我的待办" 
            active={activeTab === 'my-todos'} 
            onClick={() => setActiveTab('my-todos')}
          />
          {currentUser.role === '管理员' && (
            <SidebarItem 
              icon={<Briefcase size={18} />} 
              label="内部管理" 
              active={activeTab === 'internal'} 
              onClick={() => setActiveTab('internal')}
            />
          )}
          <SidebarItem 
            icon={<ListTodo size={18} />} 
            label="发布待办计划" 
            active={activeTab === 'publish-plan'} 
            onClick={() => setActiveTab('publish-plan')}
          />
          <SidebarItem  
            icon={<CheckCircle2 size={18} />} 
            label="已完成计划" 
            active={activeTab === 'completed'} 
            onClick={() => setActiveTab('completed')}
          />
          <SidebarItem  
            icon={<FileText size={18} />} 
            label="资料室" 
            active={activeTab === 'reference-room'} 
            onClick={() => setActiveTab('reference-room')}
          />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden bg-white">
        {visibleActiveTab === 'my-todos' ? (
          <TodoPlan tasks={tasks} setTasks={setTasks} currentUser={currentUser} />
        ) : visibleActiveTab === 'internal' ? (
          <InternalManagement 
            onAddTask={handleAddTask} 
            users={users}
            setUsers={setUsers}
          />
        ) : visibleActiveTab === 'publish-plan' ? (
          <TodoPlan 
            tasks={tasks} 
            setTasks={setTasks} 
            currentUser={currentUser} 
            headerTitle="发布待办计划" 
            filterTasks={(t) => t.source === 'Internal'} 
            allowAdd={false}
          />
        ) : visibleActiveTab === 'completed' ? (
          <CompletedView tasks={tasks} setTasks={setTasks} currentUser={currentUser} />
        ) : visibleActiveTab === 'reference-room' ? (
          <ReferenceRoom currentUser={currentUser} />
        ) : visibleActiveTab === 'chat' ? (
          <div className="bg-slate-950 h-full"><ChatView /></div>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-400">
            Feature coming soon...
          </div>
        )}
      </main>
    </div>
  );
}

// Subcomponent for Completed Task Card
function CompletedTaskCard({ task, onClick }: { task: Task, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-slate-300 transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-green-600" />
          <span className="font-semibold text-slate-800 line-clamp-1">
            {task.title}
          </span>
        </div>
        <span className="text-xs text-slate-400">{task.category || '一般'}</span>
      </div>
      <div className="text-sm text-slate-500 flex items-center justify-between">
        <span>{task.deadline || '无截止时间'}</span>
        {task.completedByName ? (
          <span className="text-slate-600 font-medium">完成者：{task.completedByName}</span>
        ) : (
          <span className="text-slate-400">来源：{task.source || '手动'}</span>
        )}
      </div>
    </button>
  );
}

function SidebarItem({ icon, label, active, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors text-sm ${
        active 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  );
}

// --- Chat View (Preserved) ---
function ChatView() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hello! I am Clawdbot, your personal AI digital employee. How can I assist you today?' },
  ]);
  const [input, setInput] = useState('');

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages([...messages, { role: 'user', text: input }]);
    const userMsg = input;
    setInput('');

    // Mock AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: `I've received your request: "${userMsg}". I'm processing this task using my local inference engine...` 
      }]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl ${
              msg.role === 'user' 
                ? 'bg-cyan-600 text-white rounded-tr-none' 
                : 'bg-slate-800 text-slate-200 rounded-tl-none'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Clawdbot to do something..."
            className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 focus:outline-none focus:border-cyan-500 transition-colors text-slate-200"
          />
          <button 
            type="submit"
            className="p-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg transition-colors"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}

// --- Completed Plans View ---
function CompletedView({ tasks, setTasks, currentUser }: { tasks: Task[], setTasks: React.Dispatch<React.SetStateAction<Task[]>>, currentUser: User }) {
  const [selected, setSelected] = useState<Task | null>(null);
  
  const completed = tasks.filter(t => {
    if (t.status !== 'completed') return false;
    // Admins see all completed tasks
    if (currentUser.role === '管理员') return true;
    
    // Internal (Published) tasks are visible to everyone when completed
    if (t.source === 'Internal') return true;

    // Private (Manual/AI) tasks are only visible to the assignee (owner) OR the completer
    return t.assigneeId === currentUser.id || t.completedById === currentUser.id;
  });
  const handleRestore = (taskId: string) => {
    if (!window.confirm('确认将该任务恢复为待办吗？')) return;
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: 'pending' } : t));
    setSelected(null);
  };
  const myCompleted = completed.filter(t => t.completedById === currentUser.id);
  const internalCompleted = completed.filter(t => t.source === 'Internal' && t.completedById !== currentUser.id);

  const handleExport = () => {
    // Format data for Excel
    const dataToExport = completed.map(task => ({
      '标题': task.title,
      '任务内容': task.description || '-',
      '优先级': task.priority === 'important-urgent' ? '重要紧急' :
                task.priority === 'important-not-urgent' ? '重要不紧急' :
                task.priority === 'urgent-not-important' ? '紧急不重要' : '不重要不紧急',
      '截止日期': task.deadline || '无',
      '分类': task.category || '一般',
      '来源': task.source || 'Manual',
      '完成时间': task.completedAt || '-',
      '完成者': task.completedByName || '-',
      '处理情况': task.completionProcess || '-',
      '问题分析': task.completionAnalysis || '-',
      '备注': task.completionNote || '-'
    }));

    // Generate file name with date
    const date = new Date().toISOString().slice(0, 10);
    
    // Export as CSV with BOM for Chinese support
    const worksheet = XLSX.utils.json_to_sheet(dataToExport);
    const csv = XLSX.utils.sheet_to_csv(worksheet);
    const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `已完成计划_${date}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-800 relative">
      <header className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span>首页</span>
          <span>/</span>
          <span className="text-slate-900 font-medium">已完成计划</span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
            title="导出 Excel"
          >
            <Download size={16} />
            导出
          </button>
          <div className="flex items-center gap-2 text-slate-500">
            <CheckCircle2 size={18} className="text-green-600" />
            <span>已完成：{completed.length}</span>
          </div>
        </div>
      </header>
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {completed.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400">
            暂无已完成任务
          </div>
        ) : (
          <>
            {/* My Completed Tasks Section */}
            {myCompleted.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4 text-slate-700 font-bold border-l-4 border-blue-500 pl-3">
                  我的完成 ({myCompleted.length})
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {myCompleted.map(task => (
                    <CompletedTaskCard key={task.id} task={task} onClick={() => setSelected(task)} />
                  ))}
                </div>
              </div>
            )}

            {/* Other Internal Completed Tasks Section */}
            {internalCompleted.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4 text-slate-700 font-bold border-l-4 border-purple-500 pl-3">
                  发布的任务 ({internalCompleted.length})
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {internalCompleted.map(task => (
                    <CompletedTaskCard key={task.id} task={task} onClick={() => setSelected(task)} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
      {selected && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-xl shadow-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800">任务详情</h3>
              <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600">关闭</button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="font-medium text-slate-800">
                {selected.title}
              </div>
              <div className="text-slate-500">类别：{selected.category || '一般'}</div>
              <div className="text-slate-500">截止：{selected.deadline || '无'}</div>
              <div className="text-slate-500">来源：{selected.source || '手动'}</div>
              <div className="text-slate-500">优先级：{
                selected.priority === 'important-urgent' ? '重要紧急' :
                selected.priority === 'important-not-urgent' ? '重要不紧急' :
                selected.priority === 'urgent-not-important' ? '紧急不重要' : '不重要不紧急'
              }</div>
              <div className="text-slate-500">完成者：{selected.completedByName || '未知'}</div>
              
              {selected.completionProcess && (
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mt-2">
                  <div className="text-xs font-semibold text-slate-500 mb-1">处理情况</div>
                  <div className="text-slate-700 whitespace-pre-wrap">{selected.completionProcess}</div>
                </div>
              )}
              
              {selected.completionAnalysis && (
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mt-2">
                  <div className="text-xs font-semibold text-slate-500 mb-1">问题分析</div>
                  <div className="text-slate-700 whitespace-pre-wrap">{selected.completionAnalysis}</div>
                </div>
              )}

              {selected.completionNote && (
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mt-2">
                  <div className="text-xs font-semibold text-slate-500 mb-1">备注</div>
                  <div className="text-slate-700 whitespace-pre-wrap">{selected.completionNote}</div>
                </div>
              )}
              
              {selected.description && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <div className="text-xs font-semibold text-slate-500 mb-1">原任务详情</div>
                  <div className="text-slate-600 whitespace-pre-wrap">{selected.description}</div>
                </div>
              )}
            </div>
            <div className="pt-4 flex justify-end gap-3">
              <button onClick={() => setSelected(null)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg">取消</button>
              <button
                onClick={() => handleRestore(selected.id)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
              >
                恢复为待办
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
