import React from 'react';
import { ArrowRight, Bot, Cpu, MessageCircle, Terminal, Zap } from 'lucide-react';

interface LandingPageProps {
  onStart: () => void;
}

export default function LandingPage({ onStart }: LandingPageProps) {
  return (
    <div className="relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute -top-1/2 -left-1/4 w-[800px] h-[800px] bg-cyan-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <nav className="flex justify-between items-center p-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <Bot className="w-8 h-8 text-cyan-400" />
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-400">
            Clawdbot
          </span>
        </div>
        <button className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
          Documentation
        </button>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-20">
        <div className="flex flex-col items-center text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-cyan-400 mb-6 animate-fade-in">
            <Zap className="w-3 h-3" />
            <span>2026 Edition Now Available</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
            Your Personal <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500">
              AI Digital Employee
            </span>
          </h1>
          
          <p className="text-lg text-slate-400 max-w-2xl mb-10 leading-relaxed">
            Experience the future of work with Clawdbot. Self-evolving, infinite memory, 
            and fully autonomous. Handles programming, scheduling, and remote control via WhatsApp.
          </p>
          
          <button 
            onClick={onStart}
            className="group relative px-8 py-4 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-lg transition-all hover:scale-105 active:scale-95 flex items-center gap-2"
          >
            Deploy Agent
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard 
            icon={<Terminal className="w-6 h-6 text-cyan-400" />}
            title="Auto Programming"
            description="Generates, tests, and deploys code autonomously. Your 24/7 senior engineer."
          />
          <FeatureCard 
            icon={<MessageCircle className="w-6 h-6 text-green-400" />}
            title="WhatsApp Control"
            description="Send commands remotely. Manage your desktop from anywhere in the world."
          />
          <FeatureCard 
            icon={<Cpu className="w-6 h-6 text-purple-400" />}
            title="Self-Evolving"
            description="Learns from your habits. Infinite memory context ensures it never forgets a detail."
          />
        </div>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
      <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}
