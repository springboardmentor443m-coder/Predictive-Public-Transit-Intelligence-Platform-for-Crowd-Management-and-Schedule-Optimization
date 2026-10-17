import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { AlertOctagon, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-4">
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-rose-400 mb-4">
        <AlertOctagon className="w-12 h-12" />
      </div>
      <h1 className="text-4xl font-extrabold font-mono text-slate-100 mb-2">404</h1>
      <p className="text-sm text-slate-400 font-mono mb-6 max-w-sm">
        The requested MetroFlow operational route does not exist or has been relocated.
      </p>
      <Button variant="primary" onClick={() => navigate('/dashboard')}>
        <ArrowLeft className="w-4 h-4 mr-1" />
        Return to Overview Dashboard
      </Button>
    </div>
  );
};
