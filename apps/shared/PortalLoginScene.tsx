import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

export default function PortalLoginScene() {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const canvas = document.createElement("canvas");
    canvas.className = "s2l-auth-webgl";
    canvas.setAttribute("aria-hidden", "true");
    host.appendChild(canvas);

    let renderer: THREE.WebGLRenderer | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let intersectionObserver: IntersectionObserver | null = null;
    let visible = true;
    let disposed = false;
    let lastFrame = 0;
    const geometries = new Set<THREE.BufferGeometry>();
    const materials = new Set<THREE.Material>();

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 50);
    camera.position.set(0, 2.8, 8.2);
    camera.lookAt(0, 0.85, 0);

    const sculpture = new THREE.Group();
    scene.add(sculpture);

    const material = (color: number, roughness = 0.78) => {
      const result = new THREE.MeshStandardMaterial({ color, roughness, metalness: 0.015 });
      materials.add(result);
      return result;
    };

    const addBox = (
      width: number,
      height: number,
      depth: number,
      x: number,
      y: number,
      z: number,
      color: number,
      rotationZ = 0,
    ) => {
      const geometry = new THREE.BoxGeometry(width, height, depth);
      const mesh = new THREE.Mesh(geometry, material(color));
      geometries.add(geometry);
      mesh.position.set(x, y, z);
      mesh.rotation.z = rotationZ;
      sculpture.add(mesh);
      return mesh;
    };

    const addCylinder = (
      radiusTop: number,
      radiusBottom: number,
      height: number,
      x: number,
      y: number,
      z: number,
      color: number,
      segments = 5,
    ) => {
      const geometry = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, segments);
      const mesh = new THREE.Mesh(geometry, material(color));
      geometries.add(geometry);
      mesh.position.set(x, y, z);
      sculpture.add(mesh);
      return mesh;
    };

    const addTorus = (radius: number, tube: number, color: number, rotationX: number, rotationY: number) => {
      const geometry = new THREE.TorusGeometry(radius, tube, 5, 56);
      const mesh = new THREE.Mesh(geometry, material(color));
      geometries.add(geometry);
      mesh.rotation.set(rotationX, rotationY, -0.12);
      mesh.position.set(0, 1.05, -0.62);
      sculpture.add(mesh);
      return mesh;
    };

    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: false,
        powerPreference: "low-power",
        preserveDrawingBuffer: false,
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.35));
      renderer.setClearColor(0x000000, 0);
      renderer.shadowMap.enabled = false;
      renderer.outputColorSpace = THREE.SRGBColorSpace;

      scene.add(new THREE.HemisphereLight(0xfff8e9, 0x869a8b, 2.15));
      const keyLight = new THREE.DirectionalLight(0xffffff, 2.1);
      keyLight.position.set(-3.6, 5.2, 5);
      scene.add(keyLight);
      const fillLight = new THREE.DirectionalLight(0xd8b57d, 0.72);
      fillLight.position.set(4, 2.2, -3);
      scene.add(fillLight);

      addTorus(1.85, 0.016, 0xc8a564, 1.08, 0.18);
      addTorus(1.42, 0.012, 0x9cac98, 0.25, -0.35);

      // A small architectural model sits on a stack of books.
      addBox(2.62, 0.12, 1.48, 0, 0.08, 0, 0x21463d, -0.025);
      addBox(2.38, 0.39, 1.34, 0.02, 0.34, 0, 0xf0e8d7, -0.035);
      addBox(2.56, 0.12, 1.48, 0, 0.59, 0, 0xb36c4e, -0.035);
      addBox(2.06, 0.34, 1.28, 0.03, 0.81, 0, 0xf6efdf, 0.035);
      addBox(2.18, 0.11, 1.38, 0, 1.03, 0, 0x315c50, 0.035);
      addBox(1.68, 0.28, 1.18, -0.02, 1.22, 0, 0xf4ead5, -0.03);
      addBox(1.82, 0.09, 1.28, 0, 1.41, 0, 0xc58d4a, -0.03);

      // Building facade and a low-poly roof.
      addBox(0.88, 0.72, 0.72, 0, 1.82, -0.08, 0xe6dcc7);
      addCylinder(0.78, 0.78, 0.45, 0, 2.38, -0.08, 0x245247, 4).rotation.y = Math.PI / 4;
      addBox(0.19, 0.36, 0.05, 0, 1.65, 0.31, 0x9d6647);
      addBox(0.14, 0.14, 0.04, -0.25, 1.96, 0.31, 0xcaa764);
      addBox(0.14, 0.14, 0.04, 0.25, 1.96, 0.31, 0xcaa764);

      const plinthGeometry = new THREE.CylinderGeometry(1.72, 1.85, 0.24, 8);
      const plinth = new THREE.Mesh(plinthGeometry, material(0x315247));
      geometries.add(plinthGeometry);
      plinth.position.set(0, -0.04, 0);
      sculpture.add(plinth);

      const accentGeometry = new THREE.IcosahedronGeometry(0.16, 0);
      const accent = new THREE.Mesh(accentGeometry, material(0xc58d4a));
      geometries.add(accentGeometry);
      accent.position.set(1.42, 1.48, 0.2);
      sculpture.add(accent);

      const resize = () => {
        if (!renderer || disposed) return;
        const bounds = host.getBoundingClientRect();
        const width = Math.max(1, Math.floor(bounds.width));
        const height = Math.max(1, Math.floor(bounds.height));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.render(scene, camera);
      };

      const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      const renderFrame = (time = 0) => {
        if (!renderer || disposed) return;
        sculpture.rotation.y = Math.sin(time * 0.00022) * 0.075;
        sculpture.rotation.x = Math.sin(time * 0.00017) * 0.018;
        renderer.render(scene, camera);
      };
      const syncAnimation = () => {
        if (!renderer || disposed) return;
        renderer.setAnimationLoop(null);
        if (motionQuery.matches || document.hidden || !visible) {
          host.dataset.animation = motionQuery.matches ? "reduced-motion" : "paused";
          renderFrame(0);
          return;
        }
        host.dataset.animation = "running";
        renderer.setAnimationLoop((time) => {
          if (time - lastFrame < 32) return;
          lastFrame = time;
          renderFrame(time);
        });
      };
      const onMotionChange = () => syncAnimation();
      const onVisibilityChange = () => syncAnimation();
      const onContextLost = (event: Event) => {
        event.preventDefault();
        renderer?.setAnimationLoop(null);
        canvas.classList.remove("is-ready");
        setReady(false);
      };

      canvas.addEventListener("webglcontextlost", onContextLost, { once: true });
      document.addEventListener("visibilitychange", onVisibilityChange);
      if (typeof ResizeObserver !== "undefined") {
        resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(host);
      } else {
        window.addEventListener("resize", resize);
      }
      if (typeof IntersectionObserver !== "undefined") {
        intersectionObserver = new IntersectionObserver((entries) => {
          visible = entries.some((entry) => entry.isIntersecting);
          syncAnimation();
        });
        intersectionObserver.observe(host);
      }
      if (typeof motionQuery.addEventListener === "function") {
        motionQuery.addEventListener("change", onMotionChange);
      } else {
        motionQuery.addListener(onMotionChange);
      }

      resize();
      renderFrame(0);
      canvas.classList.add("is-ready");
      setReady(true);
      syncAnimation();

      return () => {
        disposed = true;
        renderer?.setAnimationLoop(null);
        resizeObserver?.disconnect();
        intersectionObserver?.disconnect();
        document.removeEventListener("visibilitychange", onVisibilityChange);
        window.removeEventListener("resize", resize);
        if (typeof motionQuery.removeEventListener === "function") {
          motionQuery.removeEventListener("change", onMotionChange);
        } else {
          motionQuery.removeListener(onMotionChange);
        }
        canvas.removeEventListener("webglcontextlost", onContextLost);
        for (const geometry of geometries) geometry.dispose();
        for (const sceneMaterial of materials) sceneMaterial.dispose();
        renderer?.dispose();
        renderer?.forceContextLoss();
        canvas.remove();
      };
    } catch {
      for (const geometry of geometries) geometry.dispose();
      for (const sceneMaterial of materials) sceneMaterial.dispose();
      renderer?.dispose();
      canvas.remove();
      return () => {
        resizeObserver?.disconnect();
        intersectionObserver?.disconnect();
      };
    }
  }, []);

  return (
    <div className="s2l-auth-scene-host" ref={hostRef} aria-hidden="true" data-webgl-ready={ready}>
    </div>
  );
}
