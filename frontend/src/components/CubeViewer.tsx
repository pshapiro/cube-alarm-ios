import React, { useEffect, useRef } from 'react';
import "cubing/twisty";
import './CubeViewer.css';

interface CubeViewerProps {
  moves: string[];
}

const CubeViewer: React.FC<CubeViewerProps> = ({ moves }) => {
  const playerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const player = playerRef.current?.querySelector('twisty-player') as any;
    if (player) {
      player.alg = moves.join(' ');
      player.experimentalDisplay = '2d';
    }
  }, [moves]);

  return (
    <div className="cube-viewer" ref={playerRef}>
      <twisty-player
        background="none"
        control-panel="none"
        puzzle="3x3x3"
        playback="manual"
      ></twisty-player>
    </div>
  );
};

export default CubeViewer;
