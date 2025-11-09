'use client';

import { useState, useEffect } from 'react';

interface BottleStatus {
  id: number;
  present: boolean;
  last_seen: string | null;
  missing_for: number;
  movement_detected: boolean;
  missing_alerted: boolean;
  position?: {
    x: number;
    y: number;
  };
}

interface ObjectStatus {
  object_present: boolean;
  last_seen: string | null;
  movement_detected: boolean;
  last_movement: string | null;
  status_message: string;
  bottles: BottleStatus[];
  total_bottles: number;
  present_count: number;
  missing_count: number;
  max_bottles_seen: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function Dashboard() {
  const [status, setStatus] = useState<ObjectStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/status`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: ObjectStatus = await response.json();
        
        if (!cancelled) {
          setStatus(data);
          setLoading(false);
          setError(null);
          setLastUpdate(Date.now());
          setIsConnected(true);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setLoading(false);
          setIsConnected(false);
        }
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll every 500ms (matching the original implementation)
    const interval = setInterval(fetchStatus, 500);

    // Check connection status based on update frequency
    const connectionCheck = setInterval(() => {
      if (lastUpdate && Date.now() - lastUpdate > 5000) {
        setIsConnected(false);
      }
    }, 1000);

    return () => {
      cancelled = true;
      clearInterval(interval);
      clearInterval(connectionCheck);
    };
  }, [lastUpdate]);

  const getOverallStatusColor = () => {
    if (!status) return 'border-zinc-300 dark:border-zinc-700';
    if (status.missing_count > 0) {
      return 'border-red-500 bg-red-50 dark:bg-red-950/20 animate-pulse';
    }
    if (status.present_count > 0) {
      return 'border-green-500 bg-green-50 dark:bg-green-950/20';
    }
    return 'border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/50';
  };

  const getOverallStatusIcon = () => {
    if (!status) return '⏳';
    if (status.missing_count > 0) return '🚨';
    if (status.present_count > 0) return '✅';
    return '⏳';
  };

  const getOverallStatusText = () => {
    if (!status) return 'Loading...';
    if (status.missing_count > 0) return `${status.missing_count} Object(s) Missing`;
    if (status.present_count > 0) return `All Objects Present`;
    return 'No Objects Detected';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 via-white to-zinc-100 dark:from-black dark:via-zinc-950 dark:to-zinc-900">
      <main className="mx-auto max-w-7xl px-8 py-16 sm:px-16">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-black dark:text-white sm:text-5xl">
            Object Monitor Dashboard
          </h1>
          <p className="mt-2 text-lg text-zinc-600 dark:text-zinc-400">
            Real-time monitoring and status updates for all tracked objects
          </p>
        </div>

        {/* Connection Status */}
        <div
          className={`mb-6 rounded-lg border px-4 py-3 text-center text-sm font-medium ${
            isConnected && !error
              ? 'border-green-500 bg-green-50 text-green-800 dark:bg-green-950/20 dark:text-green-300'
              : 'border-red-500 bg-red-50 text-red-800 dark:bg-red-950/20 dark:text-red-300'
          }`}
        >
          {isConnected && !error ? (
            <>✓ Connected to detection script</>
          ) : (
            <>⚠️ {error || 'Detection script not responding'}</>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="rounded-lg border border-zinc-200 bg-white/50 p-12 text-center backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
            <div className="text-4xl mb-4">⏳</div>
            <p className="text-lg text-zinc-600 dark:text-zinc-400">
              Loading status...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="rounded-lg border border-red-500 bg-red-50 p-12 text-center backdrop-blur-sm dark:bg-red-950/20">
            <div className="text-4xl mb-4">❌</div>
            <p className="text-lg font-semibold text-red-800 dark:text-red-300 mb-2">
              Connection Error
            </p>
            <p className="text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
            <p className="mt-4 text-xs text-zinc-600 dark:text-zinc-400">
              Make sure the Flask server is running on {API_URL}
            </p>
          </div>
        )}

        {/* Status Display */}
        {status && !loading && (
          <div className="space-y-6">
            {/* Overall Status and Summary Cards */}
            <div className="grid gap-6 md:grid-cols-3">
              {/* Overall Status Card */}
              <div
                className={`rounded-lg border-4 p-6 transition-all duration-300 ${getOverallStatusColor()}`}
              >
                <div className="text-center">
                  <div className="mb-3 text-5xl">{getOverallStatusIcon()}</div>
                  <h2
                    className={`text-2xl font-bold mb-2 ${
                      status.missing_count > 0
                        ? 'text-red-700 dark:text-red-400'
                        : status.present_count > 0
                        ? 'text-green-700 dark:text-green-400'
                        : 'text-zinc-700 dark:text-zinc-300'
                    }`}
                  >
                    {getOverallStatusText()}
                  </h2>
                  <p className="text-xs text-zinc-600 dark:text-zinc-400">
                    {status.status_message}
                  </p>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="rounded-lg border border-zinc-200 bg-white/50 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
                <h3 className="mb-4 text-lg font-semibold text-black dark:text-white">
                  Summary
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-zinc-600 dark:text-zinc-400">Total Objects:</span>
                    <span className="font-bold text-black dark:text-white">
                      {status.total_bottles}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-600 dark:text-zinc-400">Present:</span>
                    <span className="font-bold text-green-600 dark:text-green-400">
                      {status.present_count}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-600 dark:text-zinc-400">Missing:</span>
                    <span className="font-bold text-red-600 dark:text-red-400">
                      {status.missing_count}
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-zinc-200 pt-3 dark:border-zinc-700">
                    <span className="text-zinc-600 dark:text-zinc-400">Max Seen:</span>
                    <span className="font-bold text-blue-600 dark:text-blue-400">
                      {status.max_bottles_seen}
                    </span>
                  </div>
                </div>
              </div>

              {/* Movement Status */}
              <div className="rounded-lg border border-zinc-200 bg-white/50 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
                <h3 className="mb-4 text-lg font-semibold text-black dark:text-white">
                  Activity
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-zinc-600 dark:text-zinc-400">Movement:</span>
                    <span
                      className={`font-semibold ${
                        status.movement_detected
                          ? 'text-orange-600 dark:text-orange-400'
                          : 'text-zinc-500 dark:text-zinc-400'
                      }`}
                    >
                      {status.movement_detected ? 'Detected' : 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-600 dark:text-zinc-400">Last Movement:</span>
                    <span className="text-sm text-black dark:text-white">
                      {status.last_movement || 'Never'}
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-zinc-200 pt-3 dark:border-zinc-700">
                    <span className="text-zinc-600 dark:text-zinc-400">Last Seen:</span>
                    <span className="text-sm text-black dark:text-white">
                      {status.last_seen || 'Never'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Individual Objects Display */}
            {status.bottles && status.bottles.length > 0 && (
              <div>
                <h2 className="mb-4 text-2xl font-bold text-black dark:text-white">
                  Individual Objects
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {status.bottles.map((bottle) => (
                    <div
                      key={bottle.id}
                      className={`rounded-lg border-2 p-4 transition-all duration-300 ${
                        bottle.present
                          ? 'border-green-500 bg-green-50/50 dark:bg-green-950/10'
                          : 'border-red-500 bg-red-50/50 dark:bg-red-950/10 animate-pulse'
                      }`}
                    >
                      <div className="mb-3 flex items-center justify-between">
                        <h3 className="text-lg font-bold text-black dark:text-white">
                          Object #{bottle.id}
                        </h3>
                        <span className="text-2xl">
                          {bottle.present ? '✅' : '🚨'}
                        </span>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-zinc-600 dark:text-zinc-400">Status:</span>
                          <span
                            className={`font-semibold ${
                              bottle.present
                                ? 'text-green-600 dark:text-green-400'
                                : 'text-red-600 dark:text-red-400'
                            }`}
                          >
                            {bottle.present ? 'Present' : 'Missing'}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-zinc-600 dark:text-zinc-400">Last Seen:</span>
                          <span className="text-black dark:text-white">
                            {bottle.last_seen || 'Never'}
                          </span>
                        </div>

                        {!bottle.present && bottle.missing_for > 0 && (
                          <div className="flex justify-between">
                            <span className="text-zinc-600 dark:text-zinc-400">Missing For:</span>
                            <span className="font-semibold text-red-600 dark:text-red-400">
                              {bottle.missing_for.toFixed(1)}s
                            </span>
                          </div>
                        )}

                        {bottle.movement_detected && (
                          <div className="rounded bg-orange-100 px-2 py-1 text-center text-xs font-semibold text-orange-800 dark:bg-orange-950/30 dark:text-orange-300">
                            ⚠️ Movement Detected
                          </div>
                        )}

                        {bottle.missing_alerted && (
                          <div className="rounded bg-red-100 px-2 py-1 text-center text-xs font-semibold text-red-800 dark:bg-red-950/30 dark:text-red-300">
                            🚨 Alert Sent
                          </div>
                        )}

                        {bottle.position && (
                          <div className="flex justify-between border-t border-zinc-200 pt-2 dark:border-zinc-700">
                            <span className="text-zinc-600 dark:text-zinc-400">Position:</span>
                            <span className="text-xs text-black dark:text-white">
                              ({bottle.position.x}, {bottle.position.y})
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Objects Message */}
            {(!status.bottles || status.bottles.length === 0) && (
              <div className="rounded-lg border border-zinc-200 bg-white/50 p-12 text-center backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
                <div className="text-4xl mb-4">🔍</div>
                <p className="text-lg text-zinc-600 dark:text-zinc-400">
                  No objects detected yet. Waiting for detection...
                </p>
              </div>
            )}

            {/* Monitoring Details Footer */}
            <div className="rounded-lg border border-zinc-200 bg-white/50 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <h3 className="mb-4 text-xl font-semibold text-black dark:text-white">
                System Information
              </h3>
              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
                <div className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800">
                  <div className="text-2xl font-bold text-black dark:text-white">
                    {status.total_bottles}
                  </div>
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">
                    Total Objects
                  </div>
                </div>
                <div className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {status.present_count}
                  </div>
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">
                    Present
                  </div>
                </div>
                <div className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800">
                  <div className="text-2xl font-bold text-black dark:text-white">
                    {isConnected ? '✓' : '✗'}
                  </div>
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">
                    System Status
                  </div>
                </div>
                <div className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800">
                  <div className="text-2xl font-bold text-black dark:text-white">
                    500ms
                  </div>
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">
                    Update Rate
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
