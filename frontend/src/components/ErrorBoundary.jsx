import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * Contains render failures to the component that caused them.
 *
 * Without this, a single thrown error in any tab unmounts the entire React
 * tree and the user stares at a blank page with no clue what happened. Here the
 * header and navigation stay usable so they can switch to another tab.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('MetroFlow render error:', error, info);
  }

  handleReset = () => {
    this.setState({ error: null });
  };

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="glass-panel rounded-2xl border border-red-500/40 p-8 text-center">
        <div className="inline-flex p-3 rounded-xl bg-red-500/10 border border-red-500/30 mb-3">
          <AlertTriangle className="w-6 h-6 text-red-400" />
        </div>
        <h2 className="text-base font-bold text-white mb-1">
          This view failed to render
        </h2>
        <p className="text-xs text-slate-400 mb-4 max-w-lg mx-auto">
          The rest of the dashboard is still working — pick another tab above, or
          retry this one.
        </p>
        <pre className="text-[10px] font-mono text-red-300/80 bg-slate-900/70 border border-slate-800 rounded-lg p-3 mb-4 overflow-x-auto text-left max-w-xl mx-auto">
          {String(error && error.message ? error.message : error)}
        </pre>
        <button
          onClick={this.handleReset}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-xs font-bold hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry this view
        </button>
      </div>
    );
  }
}