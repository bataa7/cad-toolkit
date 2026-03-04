import React, { useState } from 'react';
import { 
  Search, 
  Plus, 
  Filter, 
  Flame, 
  Calendar, 
  Users, 
  Leaf, 
  CheckCircle2, 
  Circle,
  Clock,
  Briefcase,
  Bot,
  X,
  Trash2,
  Edit2,
  Download,
  List as ListIcon,
  Columns
} from 'lucide-react';
import * as XLSX from 'xlsx';
import { Task, User } from '../types';
import { taskService } from '../services/api';

interface TodoPlanProps {
  tasks: Task[];
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  currentUser: User;
  headerTitle?: string;
  filterTasks?: (t: Task) => boolean;
  allowAdd?: boolean;
}

export default function TodoPlan({ tasks, setTasks, currentUser, headerTitle, filterTasks, allowAdd = true }: TodoPlanProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [isCompleteOpen, setIsCompleteOpen] = useState(false);
  const [completingTask, setCompletingTask] = useState<Task | null>(null);
  const [completionNote, setCompletionNote] = useState('');
  const [completionProcess, setCompletionProcess] = useState('');
  const [completionAnalysis, setCompletionAnalysis] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [groupingMode, setGroupingMode] = useState<'month' | 'assignee'>('month');

  // Form State
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState<Task['priority']>('important-urgent');
  const [deadline, setDeadline] = useState('');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');

  const handleAddTask = () => {
    setEditingTask(null);
    setTitle('');
    setPriority('important-urgent');
    setDeadline('');
    setCategory('');
    setDescription('');
    setIsModalOpen(true);
  };

  const handleEditTask = (task: Task) => {
    // If masked, do nothing
    // if (shouldMaskContent(task)) return; // No longer block opening, just mask content inside

    // For internal tasks, if not admin, open in read-only mode (effectively just viewing details)
    // or if the user is the assignee, they can view but not edit core fields.
    // We'll handle read-only in the modal rendering.
    
    setEditingTask(task);
    setTitle(task.title);
    setPriority(task.priority);
    setDeadline(task.deadline || '');
    setCategory(task.category || '');
    setDescription(task.description || '');
    setIsModalOpen(true);
  };

  const saveTask = async () => {
    if (!title.trim()) return;

    if (editingTask) {
      const updatedTask = {
        ...editingTask,
        title,
        priority,
        deadline: deadline || undefined,
        category: category || undefined,
        description: description || undefined
      };
      
      try {
        await taskService.update(editingTask.id, updatedTask);
        setTasks(tasks.map(t => t.id === editingTask.id ? updatedTask : t));
      } catch (error) {
        console.error('Failed to update task:', error);
      }
    } else {
      const newTask: Task = {
        id: Date.now().toString(),
        title,
        priority,
        deadline: deadline || undefined,
        category: category || undefined,
        description: description || undefined,
        status: 'pending',
        source: 'Manual',
        assigneeId: currentUser.id,
        assigneeName: currentUser.name,
        createdAt: new Date().toISOString().slice(0, 10)
      };
      
      try {
        const createdTask = await taskService.create(newTask);
        setTasks([...tasks, createdTask]);
      } catch (error) {
        console.error('Failed to create task:', error);
      }
    }
    setIsModalOpen(false);
  };

  const openComplete = (task: Task) => {
    setCompletingTask(task);
    setCompletionNote('');
    setCompletionProcess('');
    setCompletionAnalysis('');
    setIsCompleteOpen(true);
  };

  const confirmComplete = async () => {
    if (!completingTask) return;
    const today = new Date().toISOString().slice(0, 10);
    const updatedTask = { 
      ...completingTask, 
      status: 'completed' as const, 
      completedAt: today, 
      completionNote: completionNote || undefined,
      completionProcess: completionProcess || undefined,
      completionAnalysis: completionAnalysis || undefined,
      completedById: currentUser.id,
      completedByName: currentUser.name
    };

    try {
      await taskService.update(completingTask.id, updatedTask);
      setTasks(tasks.map(t => t.id === completingTask.id ? updatedTask : t));
    } catch (error) {
      console.error('Failed to complete task:', error);
    }

    setIsCompleteOpen(false);
    setCompletingTask(null);
    setCompletionNote('');
    setCompletionProcess('');
    setCompletionAnalysis('');
  };

  const deleteTask = async (id: string) => {
    if (window.confirm('确定要删除这个任务吗？')) {
      try {
        await taskService.delete(id);
        setTasks(tasks.filter(t => t.id !== id));
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    }
  };

  const defaultMinePredicate = (t: Task) => t.assigneeId === currentUser.id || (!t.assigneeId && t.source !== 'Internal');
  const visibleTasks = tasks
    .filter(filterTasks ? filterTasks : defaultMinePredicate)
    .sort((a, b) => {
      // Sort by deadline ascending (earliest first)
      // Tasks without deadline go to the bottom
      if (!a.deadline && !b.deadline) return 0;
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return a.deadline.localeCompare(b.deadline);
    });
  const pendingCount = visibleTasks.filter(t => t.status === 'pending').length;
  // Calculate completed count for CURRENT USER, not just visible tasks
  // This ensures "Total Tasks" logic (pending + completed) makes sense for the user's personal view
  const myCompletedCount = tasks.filter(t => t.status === 'completed' && t.completedById === currentUser.id).length;
  // Just a mock for stats
  const urgentCount = visibleTasks.filter(t => t.priority.includes('urgent')).length;
  const shouldMaskContent = (task: Task) => {
    // If it's a new task (no ID yet), do not mask
    if (!task.id) return false;

    // If it's a private task (Manual/AI), only show to assignee
    if (task.source !== 'Internal' && task.assigneeId !== currentUser.id) {
      return true;
    }
    // Internal tasks are now visible to everyone
    return false;
  };
  const canEdit = (task: Task) => {
    if (task.source !== 'Internal') return true;
    return currentUser.role === '管理员';
  };

  const handleExport = () => {
    // Format data for Excel
    const dataToExport = visibleTasks.map(task => ({
      '标题': task.title,
      '任务内容': task.description || '-',
      '优先级': task.priority === 'important-urgent' ? '重要紧急' :
                task.priority === 'important-not-urgent' ? '重要不紧急' :
                task.priority === 'urgent-not-important' ? '紧急不重要' : '不重要不紧急',
      '截止日期': task.deadline || '无',
      '分类': task.category || '一般',
      '来源': task.source || 'Manual',
      '状态': task.status === 'pending' ? '待办' : '已完成',
      '指派给': task.assigneeName || task.assigneeId || '未分配',
      '创建时间': task.createdAt || '-'
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
    a.download = `待办计划_${date}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };


  const getTasksByMonth = () => {
    const grouped: Record<string, Task[]> = {};
    const noDateTasks: Task[] = [];

    visibleTasks.forEach(task => {
      if (task.status === 'completed') return; 
      
      if (!task.deadline) {
        noDateTasks.push(task);
        return;
      }

      // Extract "YYYY-MM" from deadline "YYYY-MM-DD"
      const month = task.deadline.slice(0, 7); // "2024-05"
      if (!grouped[month]) {
        grouped[month] = [];
      }
      grouped[month].push(task);
    });

    // Sort months ascending
    const sortedMonths = Object.keys(grouped).sort();
    
    return { grouped, sortedMonths, noDateTasks };
  };

  const getTasksByAssignee = () => {
    const grouped: Record<string, Task[]> = {};
    const unassignedTasks: Task[] = [];

    visibleTasks.forEach(task => {
      if (task.status === 'completed') return;
      
      const assigneeName = task.assigneeName || task.assigneeId;
      if (!assigneeName) {
        unassignedTasks.push(task);
        return;
      }

      if (!grouped[assigneeName]) {
        grouped[assigneeName] = [];
      }
      grouped[assigneeName].push(task);
    });

    const sortedAssignees = Object.keys(grouped).sort();
    return { grouped, sortedAssignees, unassignedTasks };
  };

  const { grouped: monthGrouped, sortedMonths, noDateTasks } = getTasksByMonth();
  const { grouped: assigneeGrouped, sortedAssignees, unassignedTasks } = getTasksByAssignee();


  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-800 relative">
      {/* Header / Breadcrumbs */}
      <header className="px-6 py-4 border-b border-slate-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span>首页</span>
          <span>/</span>
          <span className="text-slate-900 font-medium">{headerTitle ?? '我的待办'}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-slate-100 rounded-lg p-1 gap-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-md transition-colors flex items-center gap-2 text-xs font-medium ${
                viewMode === 'list' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <ListIcon size={16} />
              列表
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`p-1.5 rounded-md transition-colors flex items-center gap-2 text-xs font-medium ${
                viewMode === 'kanban' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Columns size={16} />
              看板
            </button>
          </div>
          
          {viewMode === 'kanban' && (
            <div className="flex items-center bg-slate-100 rounded-lg p-1 gap-1">
              <button
                onClick={() => setGroupingMode('month')}
                className={`px-2 py-1.5 rounded-md transition-colors text-xs font-medium ${
                  groupingMode === 'month' 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                按月份
              </button>
              <button
                onClick={() => setGroupingMode('assignee')}
                className={`px-2 py-1.5 rounded-md transition-colors text-xs font-medium ${
                  groupingMode === 'assignee' 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                按人员
              </button>
            </div>
          )}

          <button 
            onClick={handleExport}
            className="p-2 hover:bg-slate-100 rounded-full text-slate-500"
            title="导出Excel"
          >
            <Download size={20} />
          </button>
          <button className="p-2 hover:bg-slate-100 rounded-full text-slate-500">
            <Search size={20} />
          </button>
          <button className="p-2 hover:bg-slate-100 rounded-full text-slate-500">
            <Bot size={20} />
          </button>
          {allowAdd && (
            <button 
              onClick={handleAddTask}
              className="bg-emerald-500 hover:bg-emerald-600 text-white p-2 rounded-lg"
            >
              <Plus size={20} />
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Column: Task List */}
        <div className="w-1/2 flex flex-col border-r border-slate-200 bg-white">
          {/* Stats & Filters */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex gap-4">
              <div className="flex items-center gap-1">
                <span className="text-blue-600 font-bold text-lg">{pendingCount + myCompletedCount}</span>
                <span className="text-slate-400 text-xs">总任务</span>
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle2 size={16} className="text-green-500" />
                <span className="text-slate-600 font-bold text-lg">{myCompletedCount}</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock size={16} className="text-orange-400" />
                <span className="text-slate-600 font-bold text-lg">{pendingCount}</span>
              </div>
              <div className="flex items-center gap-1">
                <Flame size={16} className="text-red-500" />
                <span className="text-slate-600 font-bold text-lg">{urgentCount}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button className="p-2 text-slate-400 hover:text-slate-600">
                <Search size={18} />
              </button>
              <button className="p-2 text-slate-400 hover:text-slate-600">
                <Filter size={18} />
              </button>
              {allowAdd && (
                <button 
                  onClick={handleAddTask}
                  className="p-2 text-emerald-500 hover:bg-emerald-50 rounded-full"
                >
                  <Plus size={18} />
                </button>
              )}
            </div>
          </div>

          {/* Task List Items */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {visibleTasks.filter(t => t.status === 'pending').map((task) => (
              <div key={task.id} className="group flex items-start gap-3 p-3 hover:bg-slate-50 rounded-lg border border-transparent hover:border-slate-100 transition-all relative">
                <button 
                  onClick={() => { if (!shouldMaskContent(task)) openComplete(task); }}
                  className="mt-1 text-slate-400 hover:text-emerald-500"
                  disabled={shouldMaskContent(task)}
                >
                  {task.status === 'completed' ? (
                    <CheckCircle2 className="text-emerald-500" />
                  ) : (
                    <Circle />
                  )}
                </button>
                <div className="flex-1 min-w-0 cursor-pointer" onClick={() => handleEditTask(task)}>
                  <h3 className={`font-medium text-slate-700 truncate ${task.status === 'completed' ? 'line-through text-slate-400' : ''}`}>
                    {task.title}
                  </h3>
                  <div className="flex items-center gap-3 mt-1 text-xs">
                    {task.createdAt && (
                      <span className="flex items-center gap-1 text-slate-400">
                        <Clock size={12} />
                        创建：{task.createdAt}
                      </span>
                    )}
                    {task.deadline && (
                      <span className={`flex items-center gap-1 ${
                        task.deadline.includes('昨天') ? 'text-red-500' : 
                        task.deadline.includes('前') ? 'text-red-500' : 'text-orange-500'
                      }`}>
                        <Clock size={12} />
                        {task.deadline}
                      </span>
                    )}
                    {task.category && (
                      <span className="flex items-center gap-1 text-slate-500">
                        <Briefcase size={12} />
                        {task.category}
                      </span>
                    )}
                    {task.source === 'AI' && (
                      <span className="flex items-center gap-1 text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                        <Bot size={10} />
                        AI创建
                      </span>
                    )}
                    {task.source === 'Internal' && (
                      <>
                        <span className="flex items-center gap-1 text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">
                          <Users size={10} />
                          内部派发
                        </span>
                        {task.assigneeName && (
                          <span className="flex items-center gap-1 text-slate-600">
                            <Users size={12} />
                            执行人：{task.assigneeName}
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </div>
                
                {/* Hover Actions */}
                <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex gap-1 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border border-slate-100">
                  {canEdit(task) && (
                    <button 
                      onClick={() => handleEditTask(task)}
                      className="p-1.5 text-slate-500 hover:text-blue-500 hover:bg-blue-50 rounded"
                      title="编辑"
                    >
                      <Edit2 size={14} />
                    </button>
                  )}
                  {canEdit(task) && (
                    <button 
                      onClick={() => deleteTask(task.id)}
                      className="p-1.5 text-slate-500 hover:text-red-500 hover:bg-red-50 rounded"
                      title="删除"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Matrix or Kanban */}
        {viewMode === 'kanban' ? (
          <div className="w-1/2 flex flex-col bg-slate-50 p-6 overflow-x-auto">
            <div className="flex items-center justify-center mb-6">
              {groupingMode === 'month' ? (
                <>
                  <Calendar className="mr-2 text-slate-700" />
                  <h2 className="font-bold text-lg text-slate-800">按月份看板</h2>
                </>
              ) : (
                <>
                  <Users className="mr-2 text-slate-700" />
                  <h2 className="font-bold text-lg text-slate-800">按人员看板</h2>
                </>
              )}
            </div>
            <div className="flex gap-4">
              {groupingMode === 'month' ? (
                // Month Grouping
                <>
                  {sortedMonths.map((month) => {
                    const monthTasks = monthGrouped[month];
                    const label = `${Number(month.split('-')[1])}月`;
                    return (
                      <div key={month} className="min-w-[300px] bg-white rounded-xl shadow-sm border border-slate-200 h-fit">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                          <div className="flex items-center gap-2">
                            <Calendar className="text-slate-700" size={16} />
                            <span className="font-semibold text-slate-800">{label}</span>
                          </div>
                          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{monthTasks.length}</span>
                        </div>
                        <div className="p-3 space-y-3">
                          {monthTasks.map(task => (
                            <div key={task.id} className="group relative p-3 rounded-lg border border-slate-200 hover:border-slate-300 shadow-sm bg-white">
                              <div className="font-medium text-slate-700 mb-1 line-clamp-2">{task.title}</div>
                              <div className="text-xs text-slate-500 flex items-center gap-3">
                                {task.deadline && (
                                  <span className="flex items-center gap-1">
                                    <Clock size={12} />
                                    {task.deadline}
                                  </span>
                                )}
                                {task.category && (
                                  <span className="flex items-center gap-1">
                                    <Briefcase size={12} />
                                    {task.category}
                                  </span>
                                )}
                                {task.source === 'AI' && (
                                  <span className="flex items-center gap-1 text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                                    <Bot size={10} />
                                    AI创建
                                  </span>
                                )}
                                {task.source === 'Internal' && (
                                  <>
                                    <span className="flex items-center gap-1 text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                      <Users size={10} />
                                      内部派发
                                    </span>
                                    {task.assigneeName && (
                                      <span className="flex items-center gap-1 text-slate-600">
                                        <Users size={12} />
                                        执行人：{task.assigneeName}
                                      </span>
                                    )}
                                  </>
                                )}
                              </div>
                              <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex gap-1 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border border-slate-100">
                                <button 
                                  onClick={() => handleEditTask(task)}
                                  className="p-1.5 text-slate-500 hover:text-blue-500 hover:bg-blue-50 rounded"
                                  title="编辑"
                                >
                                  <Edit2 size={14} />
                                </button>
                                <button 
                                  onClick={() => deleteTask(task.id)}
                                  className="p-1.5 text-slate-500 hover:text-red-500 hover:bg-red-50 rounded"
                                  title="删除"
                                >
                                  <Trash2 size={14} />
                                </button>
                                <button 
                                  onClick={() => { if (!shouldMaskContent(task)) openComplete(task); }}
                                  className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded"
                                  title="完成"
                                  disabled={shouldMaskContent(task)}
                                >
                                  <CheckCircle2 size={14} />
                                </button>
                              </div>
                            </div>
                          ))}
                          {monthTasks.length === 0 && (
                            <div className="text-slate-400 text-xs italic px-2 py-8 text-center">暂无任务</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Tasks with no deadline */}
                  {noDateTasks.length > 0 && (
                    <div className="min-w-[300px] bg-white rounded-xl shadow-sm border border-slate-200 h-fit">
                      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <Calendar className="text-slate-400" size={16} />
                          <span className="font-semibold text-slate-500">无截止日期</span>
                        </div>
                        <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{noDateTasks.length}</span>
                      </div>
                      <div className="p-3 space-y-3">
                        {noDateTasks.map(task => (
                          <div key={task.id} className="group relative p-3 rounded-lg border border-slate-200 hover:border-slate-300 shadow-sm bg-white">
                            <div className="font-medium text-slate-700 mb-1 line-clamp-2">{task.title}</div>
                            <div className="text-xs text-slate-500 flex items-center gap-3">
                              {task.category && (
                                <span className="flex items-center gap-1">
                                  <Briefcase size={12} />
                                  {task.category}
                                </span>
                              )}
                              {task.source === 'AI' && (
                                <span className="flex items-center gap-1 text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                                  <Bot size={10} />
                                  AI创建
                                </span>
                              )}
                              {task.source === 'Internal' && (
                                <>
                                  <span className="flex items-center gap-1 text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                    <Users size={10} />
                                    内部派发
                                  </span>
                                  {task.assigneeName && (
                                    <span className="flex items-center gap-1 text-slate-600">
                                      <Users size={12} />
                                      执行人：{task.assigneeName}
                                    </span>
                                  )}
                                </>
                              )}
                            </div>
                            <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex gap-1 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border border-slate-100">
                              <button 
                                onClick={() => handleEditTask(task)}
                                className="p-1.5 text-slate-500 hover:text-blue-500 hover:bg-blue-50 rounded"
                                title="编辑"
                              >
                                <Edit2 size={14} />
                              </button>
                              <button 
                                onClick={() => deleteTask(task.id)}
                                className="p-1.5 text-slate-500 hover:text-red-500 hover:bg-red-50 rounded"
                                title="删除"
                              >
                                <Trash2 size={14} />
                              </button>
                              <button 
                                onClick={() => { if (!shouldMaskContent(task)) openComplete(task); }}
                                className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded"
                                title="完成"
                                disabled={shouldMaskContent(task)}
                              >
                                <CheckCircle2 size={14} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                // Assignee Grouping
                <>
                  {sortedAssignees.map((assignee) => {
                    const tasks = assigneeGrouped[assignee];
                    return (
                      <div key={assignee} className="min-w-[300px] bg-white rounded-xl shadow-sm border border-slate-200 h-fit">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                          <div className="flex items-center gap-2">
                            <Users className="text-slate-700" size={16} />
                            <span className="font-semibold text-slate-800">{assignee}</span>
                          </div>
                          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{tasks.length}</span>
                        </div>
                        <div className="p-3 space-y-3">
                          {tasks.map(task => (
                            <div key={task.id} className="group relative p-3 rounded-lg border border-slate-200 hover:border-slate-300 shadow-sm bg-white">
                              <div className="font-medium text-slate-700 mb-1 line-clamp-2">{task.title}</div>
                              <div className="text-xs text-slate-500 flex items-center gap-3">
                                {task.deadline && (
                                  <span className="flex items-center gap-1">
                                    <Clock size={12} />
                                    {task.deadline}
                                  </span>
                                )}
                                {task.category && (
                                  <span className="flex items-center gap-1">
                                    <Briefcase size={12} />
                                    {task.category}
                                  </span>
                                )}
                                {task.source === 'AI' && (
                                  <span className="flex items-center gap-1 text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                                    <Bot size={10} />
                                    AI创建
                                  </span>
                                )}
                                {task.source === 'Internal' && (
                                  <>
                                    <span className="flex items-center gap-1 text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                      <Users size={10} />
                                      内部派发
                                    </span>
                                  </>
                                )}
                              </div>
                              <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex gap-1 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border border-slate-100">
                                <button 
                                  onClick={() => handleEditTask(task)}
                                  className="p-1.5 text-slate-500 hover:text-blue-500 hover:bg-blue-50 rounded"
                                  title="编辑"
                                >
                                  <Edit2 size={14} />
                                </button>
                                <button 
                                  onClick={() => deleteTask(task.id)}
                                  className="p-1.5 text-slate-500 hover:text-red-500 hover:bg-red-50 rounded"
                                  title="删除"
                                >
                                  <Trash2 size={14} />
                                </button>
                                <button 
                                  onClick={() => { if (!shouldMaskContent(task)) openComplete(task); }}
                                  className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded"
                                  title="完成"
                                  disabled={shouldMaskContent(task)}
                                >
                                  <CheckCircle2 size={14} />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Unassigned Tasks */}
                  {unassignedTasks.length > 0 && (
                    <div className="min-w-[300px] bg-white rounded-xl shadow-sm border border-slate-200 h-fit">
                      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <Users className="text-slate-400" size={16} />
                          <span className="font-semibold text-slate-500">未分配</span>
                        </div>
                        <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{unassignedTasks.length}</span>
                      </div>
                      <div className="p-3 space-y-3">
                        {unassignedTasks.map(task => (
                          <div key={task.id} className="group relative p-3 rounded-lg border border-slate-200 hover:border-slate-300 shadow-sm bg-white">
                            <div className="font-medium text-slate-700 mb-1 line-clamp-2">{task.title}</div>
                            <div className="text-xs text-slate-500 flex items-center gap-3">
                              {task.deadline && (
                                <span className="flex items-center gap-1">
                                  <Clock size={12} />
                                  {task.deadline}
                                </span>
                              )}
                              {task.category && (
                                <span className="flex items-center gap-1">
                                  <Briefcase size={12} />
                                  {task.category}
                                </span>
                              )}
                              {task.source === 'AI' && (
                                <span className="flex items-center gap-1 text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                                  <Bot size={10} />
                                  AI创建
                                </span>
                              )}
                              {task.source === 'Internal' && (
                                <>
                                  <span className="flex items-center gap-1 text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                    <Users size={10} />
                                    内部派发
                                  </span>
                                </>
                              )}
                            </div>
                            <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex gap-1 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm border border-slate-100">
                              {canEdit(task) && (
                                <button 
                                  onClick={() => handleEditTask(task)}
                                  className="p-1.5 text-slate-500 hover:text-blue-500 hover:bg-blue-50 rounded"
                                  title="编辑"
                                >
                                  <Edit2 size={14} />
                                </button>
                              )}
                              {canEdit(task) && (
                                <button 
                                  onClick={() => deleteTask(task.id)}
                                  className="p-1.5 text-slate-500 hover:text-red-500 hover:bg-red-50 rounded"
                                  title="删除"
                                >
                                  <Trash2 size={14} />
                                </button>
                              )}
                              <button 
                                onClick={() => { if (!shouldMaskContent(task)) openComplete(task); }}
                                className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded"
                                title="完成"
                                disabled={shouldMaskContent(task)}
                              >
                                <CheckCircle2 size={14} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="w-1/2 flex flex-col bg-slate-50 p-6 overflow-y-auto">
            <div className="flex items-center justify-center mb-6">
              <LayoutGridIcon className="mr-2" />
              <h2 className="font-bold text-lg text-slate-800">十字管理矩阵</h2>
            </div>
            <div className="flex-1 grid grid-cols-2 gap-4 min-h-[600px]">
              <Quadrant 
                title="重要紧急" 
                icon={<Flame className="text-red-500" size={18} />} 
                colorClass="red"
                tasks={visibleTasks.filter(t => t.status === 'pending' && t.priority === 'important-urgent')}
                onTaskClick={handleEditTask}
                viewerId={currentUser.id}
              />
              <Quadrant 
                title="重要不紧急" 
                icon={<Calendar className="text-blue-500" size={18} />} 
                colorClass="blue"
                tasks={visibleTasks.filter(t => t.status === 'pending' && t.priority === 'important-not-urgent')}
                onTaskClick={handleEditTask}
                viewerId={currentUser.id}
                onHeaderClick={() => { setViewMode('kanban'); setGroupingMode('month'); }}
              />
              <Quadrant 
                title="紧急不重要" 
                icon={<Users className="text-orange-500" size={18} />} 
                colorClass="orange"
                tasks={visibleTasks.filter(t => t.status === 'pending' && t.priority === 'urgent-not-important')}
                onTaskClick={handleEditTask}
                viewerId={currentUser.id}
                onHeaderClick={() => { setViewMode('kanban'); setGroupingMode('assignee'); }}
              />
              <Quadrant 
                title="不重要不紧急" 
                icon={<Leaf className="text-emerald-500" size={18} />} 
                colorClass="green"
                tasks={visibleTasks.filter(t => t.status === 'pending' && t.priority === 'not-important-not-urgent')}
                onTaskClick={handleEditTask}
                viewerId={currentUser.id}
              />
            </div>
          </div>
        )}
      </div>

      {/* Task Modal */}
      {isModalOpen && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-xl shadow-2xl p-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-800">
                {editingTask ? '编辑任务' : '新建任务'}
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
                <label className="block text-sm font-medium text-slate-700 mb-1">任务内容</label>
                  <input 
                    type="text" 
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="请输入任务内容"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100 disabled:text-slate-500"
                    autoFocus
                    disabled={!canEdit(editingTask || {} as Task)}
                  />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">优先级</label>
                <select 
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as Task['priority'])}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100 disabled:text-slate-500"
                  disabled={!canEdit(editingTask || {} as Task)}
                >
                  <option value="important-urgent">重要紧急</option>
                  <option value="important-not-urgent">重要不紧急</option>
                  <option value="urgent-not-important">紧急不重要</option>
                  <option value="not-important-not-urgent">不重要不紧急</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">截止时间</label>
                  <input 
                    type="date" 
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100 disabled:text-slate-500"
                    disabled={!canEdit(editingTask || {} as Task)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">分类</label>
                  <input 
                    type="text" 
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="如：财务法务"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100 disabled:text-slate-500"
                    disabled={!canEdit(editingTask || {} as Task)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">任务详情</label>
                {shouldMaskContent(editingTask || {} as Task) ? (
                   <div className="w-full px-3 py-2 bg-slate-100 text-slate-500 rounded-lg italic border border-slate-200 min-h-[100px] flex items-center justify-center">
                     内容已隐藏
                   </div>
                ) : (
                  <textarea 
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="任务详细描述..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100 disabled:text-slate-500 min-h-[100px]"
                    disabled={!canEdit(editingTask || {} as Task)}
                  />
                )}
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  取消
                </button>
                {canEdit(editingTask || {} as Task) && (
                  <button 
                    onClick={saveTask}
                    className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium"
                  >
                    保存
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Complete Confirmation Modal */}
      {isCompleteOpen && completingTask && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-xl shadow-2xl p-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-800">完成任务</h3>
              <button 
                onClick={() => { setIsCompleteOpen(false); setCompletingTask(null); }}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="text-sm">
                <div className="font-medium text-slate-800 mb-1">{completingTask.title}</div>
                <div className="text-slate-500 flex items-center gap-3">
                  {completingTask.deadline && (
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      截止：{completingTask.deadline}
                    </span>
                  )}
                  {completingTask.category && (
                    <span className="flex items-center gap-1">
                      <Briefcase size={12} />
                      类别：{completingTask.category}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">处理情况</label>
                <textarea 
                  value={completionProcess}
                  onChange={e => setCompletionProcess(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 min-h-[80px]"
                  placeholder="具体做了哪些工作..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">问题分析</label>
                <textarea 
                  value={completionAnalysis}
                  onChange={e => setCompletionAnalysis(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 min-h-[80px]"
                  placeholder="遇到的问题及原因分析..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">其他备注（可选）</label>
                <textarea 
                  value={completionNote}
                  onChange={e => setCompletionNote(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 min-h-[60px]"
                  placeholder="补充说明..."
                />
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button 
                  onClick={() => { setIsCompleteOpen(false); setCompletingTask(null); }}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  取消
                </button>
                <button 
                  onClick={confirmComplete}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium"
                >
                  确认完成
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Subcomponent for Matrix Quadrant
function Quadrant({ 
  title, 
  icon, 
  colorClass, 
  tasks,
  onTaskClick,
  onHeaderClick
}: { 
  title: string, 
  icon: React.ReactNode, 
  colorClass: 'red' | 'blue' | 'orange' | 'green', 
  tasks: Task[],
  onTaskClick: (task: Task) => void,
  viewerId: string,
  onHeaderClick?: () => void
}) {
  const styles = {
    red: 'bg-red-50 border-red-100 hover:border-red-200',
    blue: 'bg-blue-50 border-blue-100 hover:border-blue-200',
    orange: 'bg-orange-50 border-orange-100 hover:border-orange-200',
    green: 'bg-emerald-50 border-emerald-100 hover:border-emerald-200',
  };

  const titleStyles = {
    red: 'text-red-700',
    blue: 'text-blue-700',
    orange: 'text-orange-700',
    green: 'text-emerald-700',
  };

  return (
    <div className={`rounded-xl p-4 border ${styles[colorClass]} transition-colors flex flex-col`}>
      <div 
        className={`flex items-center gap-2 mb-4 ${onHeaderClick ? 'cursor-pointer hover:opacity-70 transition-opacity' : ''}`} 
        onClick={onHeaderClick}
        title={onHeaderClick ? "点击切换视图" : undefined}
      >
        {icon}
        <h3 className={`font-bold ${titleStyles[colorClass]}`}>{title}</h3>
      </div>
      
      <div className="space-y-2 flex-1">
        {tasks.map(task => (
          <div 
            key={task.id} 
            onClick={() => onTaskClick(task)}
            className="bg-white/60 p-3 rounded-lg text-sm shadow-sm hover:shadow-md hover:bg-white transition-all cursor-pointer"
          >
            <div className={`font-medium text-slate-700 mb-1 line-clamp-2 ${task.status === 'completed' ? 'line-through opacity-50' : ''}`}>
              {task.title}
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center gap-2">
                 {task.deadline && <span>{task.deadline}</span>}
                 {task.category && <span>{task.category}</span>}
              </div>
              {task.source === 'AI' && <span className="opacity-70">AI创建</span>}
              {task.source === 'Internal' && (
                <span className="opacity-70 text-blue-600">
                  内部派发{task.assigneeName ? ` · 执行人：${task.assigneeName}` : ''}
                </span>
              )}
            </div>
          </div>
        ))}
        {tasks.length === 0 && (
          <div className="h-full flex items-center justify-center text-slate-400 text-xs italic">
            暂无任务
          </div>
        )}
      </div>
    </div>
  );
}

function LayoutGridIcon({ className }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" 
      height="24" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <rect width="7" height="7" x="3" y="3" rx="1" />
      <rect width="7" height="7" x="14" y="3" rx="1" />
      <rect width="7" height="7" x="14" y="14" rx="1" />
      <rect width="7" height="7" x="3" y="14" rx="1" />
    </svg>
  )
}
