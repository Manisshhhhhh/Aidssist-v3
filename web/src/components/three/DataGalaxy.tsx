import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

import { DataGalaxyFallback } from "./DataGalaxyFallback";
import { WebGLGuard } from "./WebGLGuard";

const PARTICLE_COUNT = 104;

type DataGalaxyProps = {
  className?: string;
  compact?: boolean;
};

export function DataGalaxy({ className = "", compact = false }: DataGalaxyProps) {
  const fallback = <DataGalaxyFallback className={className} compact={compact} />;

  return (
    <WebGLGuard fallback={fallback}>
      <div
        aria-hidden="true"
        className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
      >
        <Canvas
          camera={{ fov: compact ? 36 : 42, position: [0, 0, compact ? 8 : 7] }}
          dpr={[1, 1.35]}
          gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
        >
          <ambientLight intensity={0.45} />
          <DataGalaxyScene compact={compact} />
        </Canvas>
      </div>
    </WebGLGuard>
  );
}

function DataGalaxyScene({ compact }: { compact: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const pointsRef = useRef<THREE.Points>(null);
  const linesRef = useRef<THREE.LineSegments>(null);

  const { linePositions, particlePositions } = useMemo(() => createGalaxyGeometry(compact), [compact]);

  useFrame(({ clock }) => {
    const elapsed = clock.getElapsedTime();

    if (groupRef.current) {
      groupRef.current.rotation.y = elapsed * (compact ? 0.012 : 0.018);
      groupRef.current.rotation.x = Math.sin(elapsed * 0.12) * (compact ? 0.018 : 0.035);
    }

    if (pointsRef.current) {
      pointsRef.current.rotation.z = elapsed * 0.008;
    }

    if (linesRef.current) {
      linesRef.current.rotation.z = -elapsed * 0.005;
    }
  });

  return (
    <group
      ref={groupRef}
      position={[compact ? 1.6 : 0.2, compact ? 0.1 : 0, compact ? -1.15 : -0.35]}
      rotation={[0.18, -0.28, -0.08]}
      scale={compact ? 0.72 : 1}
    >
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[particlePositions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          color="#64B5F6"
          depthWrite={false}
          opacity={compact ? 0.42 : 0.55}
          size={compact ? 0.024 : 0.03}
          sizeAttenuation
          transparent
        />
      </points>

      <lineSegments ref={linesRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
        </bufferGeometry>
        <lineBasicMaterial color="#74B9A3" opacity={compact ? 0.1 : 0.16} transparent />
      </lineSegments>
    </group>
  );
}

function createGalaxyGeometry(compact: boolean) {
  const random = seededRandom(compact ? 17 : 42);
  const particles: number[] = [];
  const coordinates: THREE.Vector3[] = [];
  const count = compact ? 68 : PARTICLE_COUNT;

  for (let index = 0; index < count; index += 1) {
    const band = index % 3;
    const angle = index * 0.48 + random() * 0.28;
    const radius = 1.05 + band * 0.48 + random() * 0.24;
    const height = (random() - 0.5) * (compact ? 1.35 : 1.8);
    const coordinate = new THREE.Vector3(
      Math.cos(angle) * radius,
      height + Math.sin(index * 0.22) * 0.16,
      Math.sin(angle) * radius * 0.46 + (random() - 0.5) * 0.38,
    );

    coordinates.push(coordinate);
    particles.push(coordinate.x, coordinate.y, coordinate.z);
  }

  const lines: number[] = [];
  for (let index = 0; index < coordinates.length; index += 1) {
    const nextIndex = index + 3;
    if (nextIndex < coordinates.length && index % 2 === 0) {
      lines.push(...coordinates[index].toArray(), ...coordinates[nextIndex].toArray());
    }
  }

  return {
    linePositions: new Float32Array(lines),
    particlePositions: new Float32Array(particles),
  };
}

function seededRandom(seed: number) {
  let value = seed;

  return () => {
    value = (value * 1664525 + 1013904223) % 4294967296;
    return value / 4294967296;
  };
}
