import { useState, useEffect } from 'react';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { User, Task } from './types';
import { userService, taskService } from './services/api';

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  // Load initial data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [usersData, tasksData] = await Promise.all([
          userService.getAll(),
          taskService.getAll()
        ]);
        setUsers(usersData);
        setTasks(tasksData);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        加载中...
      </div>
    );
  }

  return (
    <div className="bg-slate-950 min-h-screen text-slate-100 font-sans selection:bg-cyan-500/30">
      {currentUser ? (
        <Dashboard 
          currentUser={currentUser} 
          onLogout={() => setCurrentUser(null)}
          tasks={tasks}
          setTasks={setTasks}
          users={users}
          setUsers={setUsers}
        />
      ) : (
        <Login onLogin={setCurrentUser} users={users} />
      )}
    </div>
  );
}

export default App;
