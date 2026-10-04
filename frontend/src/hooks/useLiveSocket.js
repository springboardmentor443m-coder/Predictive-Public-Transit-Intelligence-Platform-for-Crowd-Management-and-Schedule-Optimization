import { useEffect, useRef, useState, useCallback } from 'react';
import { liveSocketUrl, fetchLiveSnapshot } from '../services/api';

/**
 * Subscribes to the backend live-crowd WebSocket.
 *
 * The backend advances a simulated clock one minute per pushed frame, so the
 * numbers on screen genuinely move every couple of seconds. If the socket
 * drops we fall back to polling the REST snapshot and keep retrying, so the
 * dashboard degrades instead of freezing.
 */
export function useLiveSocket({ pollIntervalMs = 4000 } = {}) {
  const [snapshot, setSnapshot] = useState(null);
  const [status, setStatus] = useState('connecting'); // connecting | live | polling | error
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const retryRef = useRef(null);
  const pollRef = useRef(null);
  const attemptRef = useRef(0);
  const closedRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    if (pollRef.current || closedRef.current) return;
    setStatus('polling');
    const tick = async () => {
      try {
        const data = await fetchLiveSnapshot();
        setSnapshot(data);
        setStatus('polling');
        setError(null);
      } catch (err) {
        setError(err.message);
        setStatus('error');
      }
    };
    tick();
    pollRef.current = setInterval(tick, pollIntervalMs);
  }, [pollIntervalMs]);

  const connect = useCallback(() => {
    if (closedRef.current) return;
    let ws;
    try {
      ws = new WebSocket(liveSocketUrl());
    } catch (err) {
      setError(err.message);
      startPolling();
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      attemptRef.current = 0;
      setStatus('live');
      setError(null);
      stopPolling();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.error) {
          setError(data.error);
          return;
        }
        setSnapshot(data);
        setStatus('live');
      } catch (err) {
        setError('Malformed live frame');
      }
    };

    ws.onerror = () => {
      // onclose always follows; handle the reconnect there
    };

    ws.onclose = () => {
      if (closedRef.current) return;
      startPolling();
      const delay = Math.min(15000, 1000 * 2 ** attemptRef.current);
      attemptRef.current += 1;
      retryRef.current = setTimeout(connect, delay);
    };
  }, [startPolling, stopPolling]);

  useEffect(() => {
    closedRef.current = false;

    // seed immediately so the UI has data before the socket's first frame
    fetchLiveSnapshot()
      .then(setSnapshot)
      .catch(() => {});

    connect();

    return () => {
      closedRef.current = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      stopPolling();
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect, stopPolling]);

  return { snapshot, status, error };
}