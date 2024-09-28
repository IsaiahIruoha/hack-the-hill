import { Canvas } from "@react-three/fiber";
import React, { useState } from "react";
import Character from "../components/Character";
import { OrbitControls, useGLTF } from "@react-three/drei";

const Index = () => {
  const GolfCourse = () => {
    const { scene } = useGLTF("/western_trent_golf_course.glb"); // Load the golf course model
    return (
      <primitive
        object={scene}
        scale={[0.2, 0.2, 0.1]}
        position={[0, -25, 0]}
      />
    ); // Adjust scale and position
  };

  const [currentAnimationName, setCurrentAnimationName] = useState("idle");

  const toggleAnimation = () => {
    setCurrentAnimationName((prev) => (prev === "idle" ? "golf" : "idle"));
  };

  return (
    <div className="w-[100vw] h-[100vh] relative">
      <Canvas style={{ 
        background: `url('/sky.jpg')`,
        backgroundSize: 'cover', 
        backgroundPosition: 'center',
        }}>
        <OrbitControls />
        <ambientLight />
        <directionalLight position={[-5, 5, 5]} />
        <Character currentAnimationName={currentAnimationName} />
        <GolfCourse />
      </Canvas>

      <div className="absolute bottom-0 right-3 flex flex-col justify-center">
        <div className="bg-green-500 m-2 rounded-2xl text-center">
          <button onClick={toggleAnimation} className="p-2">
            {currentAnimationName === "idle" ? "Play Golf" : "Switch to Idle"}
          </button>
        </div>
        <div>
          Data Form
        </div>
      </div>
    </div>
  );
};

export default Index;