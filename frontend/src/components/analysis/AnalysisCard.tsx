/** Analysis result visualization component */

import React from 'react';
import Plot from 'react-plotly.js';

interface AnalysisCardProps {
  toolName: string;
  result: {
    success: boolean;
    data?: Record<string, unknown>;
    figure?: Record<string, unknown>;
    message?: string;
    error?: string;
  };
}

export const AnalysisCard: React.FC<AnalysisCardProps> = ({ toolName, result }) => {
  if (!result.success) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500 rounded-lg">
        <h3 className="text-red-400 font-medium mb-2">Analysis Failed</h3>
        <p className="text-red-300 text-sm">{result.error}</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-700 rounded-lg border border-gray-600">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-medium capitalize">
          {toolName.replace('_', ' ')}
        </h3>
        {result.message && (
          <span className="text-green-400 text-sm">{result.message}</span>
        )}
      </div>

      {/* Statistics */}
      {result.data && (
        <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
          {Object.entries(result.data).map(([key, value]) => (
            <div key={key} className="bg-gray-800 p-2 rounded">
              <p className="text-gray-400 capitalize">{key.replace('_', ' ')}</p>
              <p className="text-white font-medium">{String(value)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Plotly Figure */}
      {result.figure && (
        <div className="bg-white rounded-lg p-2">
          <Plot
            data={result.figure.data || []}
            layout={{
              ...result.figure.layout,
              responsive: true,
              displayModeBar: true,
            }}
            config={{
              responsive: true,
              displaylogo: false,
            }}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      )}
    </div>
  );
};

export default AnalysisCard;