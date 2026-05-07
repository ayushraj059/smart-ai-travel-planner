
import { useState } from 'react';
import Sidebar from '../components/layout/Sidebar';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Save, Check } from 'lucide-react';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const stored = JSON.parse(localStorage.getItem('voyonata_user') || '{}');
    stored.name = name;
    localStorage.setItem('voyonata_user', JSON.stringify(stored));
    updateUser({ name });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="flex min-h-screen bg-navy-900">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-lg">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-white mb-1">Edit Profile</h1>
            <p className="text-slate-400 text-sm">Update your personal information.</p>
          </div>

          <div className="bg-navy-600 border border-navy-400 rounded-xl p-6">
            <div className="flex items-center gap-4 mb-6 pb-6 border-b border-navy-400">
              <div className="w-14 h-14 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0">
                <span className="text-indigo-300 font-bold text-xl">
                  {(name || user?.name || '?')[0].toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-white font-medium">{name || user?.name}</p>
                <p className="text-slate-500 text-xs mt-0.5">{user?.email}</p>
              </div>
            </div>
            <form onSubmit={handleSave} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  <span className="flex items-center gap-1.5"><User size={13} />Full Name</span>
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="w-full px-4 py-3 bg-navy-500 border border-navy-400 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  <span className="flex items-center gap-1.5"><Mail size={13} />Email Address</span>
                </label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-4 py-3 bg-navy-700 border border-navy-400 rounded-xl text-slate-500 text-sm cursor-not-allowed"
                />
                <p className="text-xs text-slate-600 mt-1">Email cannot be changed.</p>
              </div>

              <button
                type="submit"
                className={`flex items-center gap-2 px-5 py-2.5 text-white text-sm font-medium rounded-xl transition-colors ${saved ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-indigo-600 hover:bg-indigo-500'}`}
              >
                {saved ? <Check size={14} /> : <Save size={14} />}
                {saved ? 'Saved!' : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
