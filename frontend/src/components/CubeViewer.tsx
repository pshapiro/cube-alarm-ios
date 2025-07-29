import React from 'react';
import './CubeViewer.css';

interface CubeViewerProps {
  moves: string[];
  cubeState?: string;
}

const CubeViewer: React.FC<CubeViewerProps> = ({ moves, cubeState }) => {
  return (
    <div className="cube-viewer">
      {cubeState ? (
        <pre>{cubeState}</pre>
      ) : (
        <p>Moves: {moves.join(' ')}</p>
      )}
    </div>
  );
};

export default CubeViewer;
