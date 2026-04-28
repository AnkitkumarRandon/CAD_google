import { OrbitControls, Stage } from "@react-three/drei";
import { Canvas, useLoader } from "@react-three/fiber";
import { Suspense } from "react";
import { Color } from "three";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import type { Issue } from "../types";

function Model({ url }: { url: string }) {
  const geometry = useLoader(STLLoader, url);
  geometry.computeVertexNormals();
  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial color="#dce6f8" metalness={0.15} roughness={0.6} />
    </mesh>
  );
}

function HighlightMarkers({ issues, activeIssueId }: { issues: Issue[]; activeIssueId: string | null }) {
  return (
    <>
      {issues.map((issue) => {
        const color =
          issue.severity === "critical"
            ? new Color("#ff5c7a")
            : issue.severity === "warning"
              ? new Color("#facc15")
              : new Color("#60a5fa");

        return (
          <mesh
            key={issue.id}
            position={issue.location.point}
            scale={issue.location.radius * (activeIssueId === issue.id ? 1.35 : 1)}
          >
            <sphereGeometry args={[1, 20, 20]} />
            <meshStandardMaterial
              color={color}
              transparent
              opacity={activeIssueId === issue.id ? 0.55 : 0.3}
              emissive={color}
              emissiveIntensity={0.6}
            />
          </mesh>
        );
      })}
    </>
  );
}

export default function Viewer3D({
  previewUrl,
  issues,
  activeIssueId
}: {
  previewUrl: string | null;
  issues: Issue[];
  activeIssueId: string | null;
}) {
  if (!previewUrl) {
    return (
      <div className="flex h-full items-center justify-center rounded-[28px] border border-white/10 bg-white/5">
        <div className="max-w-sm text-center text-sm text-slate-300">
          Upload a STEP or STL model to generate a tessellated preview and inspect validation highlights here.
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/60 shadow-neon">
      <Canvas camera={{ position: [140, 110, 140], fov: 42 }}>
        <color attach="background" args={["#020617"]} />
        <ambientLight intensity={1.2} />
        <directionalLight position={[70, 110, 55]} intensity={2.1} castShadow />
        <Suspense fallback={null}>
          <Stage intensity={0.4} shadows={false} environment="city">
            <Model url={previewUrl} />
            <HighlightMarkers issues={issues} activeIssueId={activeIssueId} />
          </Stage>
        </Suspense>
        <OrbitControls makeDefault />
      </Canvas>
    </div>
  );
}
