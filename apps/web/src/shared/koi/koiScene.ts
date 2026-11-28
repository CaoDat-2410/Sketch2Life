/**
 * WebGL scene for the Sketch2Life koi. Loaded only through `import()` from KoiHero, so pages
 * without the hero never download three.js or the model.
 */
import type { BufferGeometry, Material, Mesh, Object3D, Texture } from "three";

export type KoiSceneOptions = {
  host: HTMLElement;
  modelUrl: string;
  /** Called once, after the first frame is on screen. */
  onReady: () => void;
  /** Called when WebGL, the model or the shader fails, or the context is lost. */
  onFail: () => void;
};

const POSE_YAW = -0.6;
const POSE_PITCH = 0.1;
const LOOK_YAW = 0.14;
const LOOK_PITCH = 0.08;
const ENTRANCE_SECONDS = 1.4;
const ENTRANCE_START_SCALE = 0.86;
const FIELD_OF_VIEW = 30;
const MAX_PIXEL_RATIO = 2;
const TAIL_WAVE = 0.04;
const FIN_FLAP = 0.018;
const BOB = 0.012;
const FIT_MARGIN = 1.04;

const glsl = (value: number) => value.toFixed(6);

function disposeObject(root: Object3D) {
  root.traverse((node) => {
    const mesh = node as Mesh;
    if (!mesh.isMesh) return;
    (mesh.geometry as BufferGeometry).dispose();
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const material of materials as Material[]) {
      for (const value of Object.values(material)) {
        if (value && typeof value === "object" && (value as Texture).isTexture) (value as Texture).dispose();
      }
      material.dispose();
    }
  });
}

/** Starts the scene inside `host` and returns a function that releases everything. */
export function mountKoiScene({ host, modelUrl, onReady, onFail }: KoiSceneOptions): () => void {
  let disposed = false;
  let release: (() => void) | undefined;

  const fail = () => {
    if (disposed) return;
    disposed = true;
    release?.();
    release = undefined;
    onFail();
  };

  void (async () => {
    const [THREE, { GLTFLoader }] = await Promise.all([
      import("three"),
      import("three/examples/jsm/loaders/GLTFLoader.js"),
    ]);
    const gltf = await new GLTFLoader().loadAsync(modelUrl);
    const model = gltf.scene;
    if (disposed) {
      disposeObject(model);
      return;
    }

    let renderer: InstanceType<typeof THREE.WebGLRenderer>;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    } catch (error) {
      disposeObject(model);
      throw error;
    }
    const canvas = renderer.domElement;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.debug.onShaderError = fail;
    canvas.className = "s2l-koi-canvas";
    canvas.setAttribute("aria-hidden", "true");
    canvas.style.opacity = "0";

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(FIELD_OF_VIEW, 1, 0.01, 100);
    scene.add(new THREE.HemisphereLight(0xfffaf6, 0xead9fb, 2.7));
    const lamps: Array<[number, number, number, number, number]> = [
      [0xffe9d6, 1.3, -3, 4, 5],
      [0xe6ccff, 0.8, 4, 1, 2],
      [0xffd9d2, 0.9, 2, 3, -4],
    ];
    for (const [color, intensity, x, y, z] of lamps) {
      const lamp = new THREE.DirectionalLight(color, intensity);
      lamp.position.set(x, y, z);
      scene.add(lamp);
    }

    const group = new THREE.Group();
    const center = new THREE.Box3().setFromObject(model).getCenter(new THREE.Vector3());
    model.position.sub(center);
    group.add(model);
    scene.add(group);

    const time = { value: 0 };
    const samples: number[] = [];
    model.traverse((node) => {
      const mesh = node as Mesh;
      if (!mesh.isMesh) return;
      mesh.frustumCulled = false;
      const geometry = mesh.geometry as BufferGeometry;
      geometry.computeBoundingBox();
      const box = geometry.boundingBox;
      if (!box) return;
      const headZ = glsl(box.max.z);
      const length = glsl(Math.max(box.max.z - box.min.z, 0.001));
      const halfWidth = glsl(Math.max(Math.abs(box.max.x), Math.abs(box.min.x), 0.001));

      const positions = geometry.getAttribute("position");
      const step = Math.max(1, Math.ceil(positions.count / 4000));
      for (let index = 0; index < positions.count; index += step) {
        samples.push(positions.getX(index) - center.x, positions.getY(index) - center.y, positions.getZ(index) - center.z);
      }

      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const material of materials as Material[]) {
        const lit = (material as Material & { isMeshStandardMaterial?: boolean }).isMeshStandardMaterial === true;
        material.transparent = true;
        material.customProgramCacheKey = () => "s2l-koi";
        material.onBeforeCompile = (shader) => {
          // koiTime is declared in the vertex shader only: a uniform shared by both stages must
          // have the same precision in both, or the program does not link.
          shader.uniforms.koiTime = time;
          shader.vertexShader = shader.vertexShader
            .replace("#include <common>", "#include <common>\nuniform float koiTime;\nvarying float vKoiThin;")
            .replace(
              "#include <begin_vertex>",
              `#include <begin_vertex>
              float koiAlong = (${headZ} - position.z) / ${length};
              float koiTail = smoothstep(0.22, 0.95, koiAlong);
              float koiFin = smoothstep(0.28, 0.95, abs(position.x) / ${halfWidth});
              float koiHeadGuard = smoothstep(0.02, 0.28, koiAlong);
              transformed.x += sin(koiTime * 1.8 + position.z * 7.0) * ${glsl(TAIL_WAVE)} * koiTail * koiTail;
              transformed.y += sin(koiTime * 2.1 + abs(position.x) * 5.0) * ${glsl(FIN_FLAP)} * koiFin * koiHeadGuard;
              vKoiThin = max(koiTail * koiTail, koiFin * koiHeadGuard);`,
            );
          shader.fragmentShader = shader.fragmentShader
            .replace("#include <common>", "#include <common>\nvarying float vKoiThin;")
            .replace(
              "#include <map_fragment>",
              `#include <map_fragment>
              float koiLuma = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
              // Dark texels (pupils, lashes) keep their contrast; everything else gets the pastel lift.
              float koiMask = smoothstep(0.035, 0.22, koiLuma);
              vec3 koiRich = mix(vec3(koiLuma), diffuseColor.rgb, 1.3);
              koiRich = mix(koiRich, vec3(1.0, 0.8, 0.86), 0.16);
              diffuseColor.rgb = mix(diffuseColor.rgb, max(koiRich, vec3(0.0)), koiMask);
              diffuseColor.a *= mix(1.0, 0.8, vKoiThin * koiMask);`,
            );
          if (lit) {
            shader.fragmentShader = shader.fragmentShader.replace(
              "#include <opaque_fragment>",
              `float koiRim = pow(1.0 - clamp(abs(dot(normalize(normal), normalize(vViewPosition))), 0.0, 1.0), 2.6);
              outgoingLight += koiMask * koiRim * vec3(1.0, 0.86, 0.93) * 0.2;
              #include <opaque_fragment>`,
            );
          }
        };
        material.needsUpdate = true;
      }
    });

    /* Fit the camera to the real silhouette in every pose the fish can take, so fins and tail are never cut off. */
    const posed: number[] = [];
    const frameBox = new THREE.Box2();
    const probe = new THREE.Vector3();
    const euler = new THREE.Euler();
    for (const [pitch, yaw] of [[0, 0], [LOOK_PITCH, LOOK_YAW], [LOOK_PITCH, -LOOK_YAW], [-LOOK_PITCH, LOOK_YAW], [-LOOK_PITCH, -LOOK_YAW]]) {
      euler.set(POSE_PITCH + pitch, POSE_YAW + yaw, 0);
      for (let index = 0; index < samples.length; index += 3) {
        probe.set(samples[index], samples[index + 1], samples[index + 2]).applyEuler(euler);
        posed.push(probe.x, probe.y, probe.z);
        frameBox.expandByPoint(new THREE.Vector2(probe.x, probe.y));
      }
    }
    const sway = TAIL_WAVE + BOB;
    const tangent = Math.tan(THREE.MathUtils.degToRad(FIELD_OF_VIEW / 2));
    camera.position.x = (frameBox.max.x + frameBox.min.x) / 2;
    camera.position.y = (frameBox.max.y + frameBox.min.y) / 2;
    /** Smallest camera distance at which every sampled point stays inside the frustum for this aspect ratio. */
    const fitDistance = (aspect: number) => {
      let distance = 0;
      for (let index = 0; index < posed.length; index += 3) {
        const x = Math.abs(posed[index] - camera.position.x) + sway;
        const y = Math.abs(posed[index + 1] - camera.position.y) + sway;
        distance = Math.max(distance, Math.max(y, x / aspect) / tangent + posed[index + 2]);
      }
      return distance * FIT_MARGIN;
    };

    let visible = false;
    let frame = 0;
    let elapsed = 0;
    let last = 0;
    let entrance = 0;
    let announced = false;
    let targetX = 0;
    let targetY = 0;
    let lookX = 0;
    let lookY = 0;

    const resize = () => {
      const width = Math.max(host.clientWidth, 1);
      const height = Math.max(host.clientHeight, 1);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.position.z = fitDistance(camera.aspect);
      camera.updateProjectionMatrix();
    };

    const active = () => !disposed && visible && !document.hidden;

    const draw = (now: number) => {
      frame = 0;
      if (!active()) {
        last = 0;
        return;
      }
      const delta = last ? Math.min((now - last) / 1000, 0.05) : 0;
      last = now;
      elapsed += delta;
      entrance = Math.min(1, entrance + delta / ENTRANCE_SECONDS);
      const eased = 1 - Math.pow(1 - entrance, 3);
      time.value = elapsed;
      lookX += (targetX - lookX) * 0.04;
      lookY += (targetY - lookY) * 0.04;
      group.rotation.set(POSE_PITCH + lookY * LOOK_PITCH, POSE_YAW + lookX * LOOK_YAW, 0);
      group.position.y = Math.sin(elapsed * 1.1) * BOB;
      group.scale.setScalar(ENTRANCE_START_SCALE + eased * (1 - ENTRANCE_START_SCALE));
      renderer.render(scene, camera);
      if (disposed) return;
      canvas.style.opacity = String(eased);
      if (!announced) {
        announced = true;
        onReady();
      }
      schedule();
    };

    function schedule() {
      if (!frame && active()) frame = requestAnimationFrame(draw);
    }

    const syncActivity = () => {
      host.dataset.koiPaused = active() ? "false" : "true";
      last = 0;
      schedule();
    };
    const onPointerMove = (event: PointerEvent) => {
      targetX = Math.max(-1, Math.min(1, (event.clientX / window.innerWidth - 0.5) * 2));
      targetY = Math.max(-1, Math.min(1, (event.clientY / window.innerHeight - 0.5) * 2));
    };
    const onContextLost = (event: Event) => {
      event.preventDefault();
      fail();
    };
    const onResize = () => {
      resize();
      schedule();
    };

    const resizeObserver = typeof ResizeObserver === "function" ? new ResizeObserver(onResize) : null;
    const intersectionObserver = typeof IntersectionObserver === "function"
      ? new IntersectionObserver((entries) => {
          visible = entries[entries.length - 1]?.isIntersecting ?? false;
          syncActivity();
        })
      : null;

    release = () => {
      // Also reached from fail(): mark the scene dead so a frame in flight cannot draw or reschedule.
      disposed = true;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", syncActivity);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      resizeObserver?.disconnect();
      intersectionObserver?.disconnect();
      disposeObject(model);
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
      delete host.dataset.koiPaused;
    };

    canvas.addEventListener("webglcontextlost", onContextLost);
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    document.addEventListener("visibilitychange", syncActivity);
    if (resizeObserver) resizeObserver.observe(host);
    else window.addEventListener("resize", onResize);
    host.prepend(canvas);
    resize();
    if (intersectionObserver) intersectionObserver.observe(host);
    else {
      visible = true;
      syncActivity();
    }
  })().catch(fail);

  return () => {
    disposed = true;
    release?.();
    release = undefined;
  };
}
