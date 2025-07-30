import React, { useEffect, useRef } from 'react';
import "cubing/twisty";
import './CubeViewer.css';

interface CubeViewerProps {
  moves: string[];
  cubeState?: string;
}

const CubeViewer: React.FC<CubeViewerProps> = ({ moves, cubeState }) => {
  const playerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const player = playerRef.current?.querySelector('twisty-player') as any;
    if (player) {
      if (cubeState) {
        player.alg = cubeState;
      } else {
        player.alg = moves.join(' ');
      }
      player.experimentalDisplay = '2d';
    }
  }, [moves, cubeState]);

  return (
    <div className="cube-viewer" ref={playerRef}>
      {React.createElement('twisty-player', {
        background: 'none',
        'control-panel': 'none',
        puzzle: '3x3x3',
        alg: cubeState ? cubeState : moves.join(' '),
      })}
    </div>
  );
};

export default CubeViewer;
