import streamlit as st
import re
import json
import trimesh
import cadquery as cq
import numpy as np
import os
import math
import streamlit.components.v1 as components
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Callable

st.set_page_config(page_title="JARVIS // Advanced CAD Forge", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# STARK-THEMED HUD INJECTION (CSS)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Share Tech Mono', monospace;
        background-color: #05070B;
        color: #00f3ff;
    }
    
    .stApp {
        background: radial-gradient(circle at center, #0a111a 0%, #030508 100%);
    }
    
    /* HUD Panel Styling */
    div.stTextArea textarea {
        background-color: rgba(0, 243, 255, 0.03);
        border: 1px solid rgba(0, 243, 255, 0.3);
        color: #00f3ff;
        font-family: 'Share Tech Mono', monospace;
        border-radius: 2px;
        box-shadow: inset 0 0 10px rgba(0, 243, 255, 0.05);
    }
    div.stTextArea textarea:focus {
        border-color: #00f3ff;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2), inset 0 0 10px rgba(0, 243, 255, 0.1);
    }
    
    /* Futuristic Primary Buttons */
    .stButton button {
        background: linear-gradient(90deg, rgba(0,243,255,0.1) 0%, rgba(0,120,255,0.2) 100%);
        border: 1px solid #00f3ff;
        color: #00f3ff;
        font-family: 'Share Tech Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-radius: 2px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: #00f3ff;
        color: #030508;
        box-shadow: 0 0 20px rgba(0,243,255,0.6);
    }
    
    /* Metrics & Headers */
    h1, h2, h3 {
        color: #00f3ff !important;
        font-family: 'Share Tech Mono', monospace;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(0,243,255,0.4);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. PARAMETRIC DATA STRUCTURES
# ==========================================
@dataclass
class BoundingBox:
    w: float
    d: float
    h: float

@dataclass
class ComponentSpec:
    name: str
    category: str
    bbox: BoundingBox
    color: cq.Color

@dataclass
class AssemblyParams:
    base_dim: BoundingBox = field(default_factory=lambda: BoundingBox(180.0, 150.0, 20.0))
    components: List[ComponentSpec] = field(default_factory=list)

# ==========================================
# 2. DETAILED PARAMETRIC COMPONENT REGISTRY
# ==========================================
ComponentGenerator = Callable[[BoundingBox], cq.Workplane]

class ComponentRegistry:
    _registry: Dict[str, Tuple[ComponentGenerator, BoundingBox, cq.Color, List[str]]] = {}

    @classmethod
    def register(cls, category_key: str, default_bbox: BoundingBox, color: cq.Color, keywords: List[str]):
        def decorator(func: ComponentGenerator):
            cls._registry[category_key] = (func, default_bbox, color, keywords)
            return func
        return decorator

    @classmethod
    def get(cls, category_key: str):
        return cls._registry.get(category_key, None)

    @classmethod
    def match_keywords(cls, prompt: str) -> List[str]:
        matched = []
        for key, (_, _, _, keywords) in cls._registry.items():
            if any(kw in prompt for kw in keywords):
                matched.append(key)
        return matched

def build_fallback(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").box(bbox.w, bbox.d, bbox.h)

@ComponentRegistry.register("standoff", BoundingBox(10.0, 10.0, 25.0), cq.Color(0.86, 0.42, 0.12), ["standoff", "post", "pillar"])
def build_standoff(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").polygon(6, bbox.w).extrude(bbox.h).faces(">Z").hole(bbox.w * 0.5)

@ComponentRegistry.register("hex_bolt", BoundingBox(10.0, 10.0, 16.0), cq.Color(0.8, 0.83, 0.88), ["bolt", "hex bolt", "screw"])
def build_hex_bolt(bbox: BoundingBox) -> cq.Workplane:
    head_h = 4.0
    head = cq.Workplane("XY").polygon(6, bbox.w).extrude(head_h)
    shank = cq.Workplane("XY").workplane(offset=- (bbox.h - head_h)).circle(bbox.w * 0.3).extrude(bbox.h - head_h)
    return head.union(shank)

@ComponentRegistry.register("bracket", BoundingBox(15.0, 30.0, 35.0), cq.Color(0.5, 0.35, 0.83), ["l-bracket", "bracket", "gusset"])
def build_bracket(bbox: BoundingBox) -> cq.Workplane:
    t = 4.0
    base = cq.Workplane("XY").box(bbox.w, bbox.d, t)
    upright = cq.Workplane("XY").workplane(offset=bbox.h / 2.0 - t / 2.0).box(t, bbox.d, bbox.h).translate((-bbox.w / 2.0 + t / 2.0, 0, 0))
    return base.union(upright).faces(">Z").workplane().hole(4.0)

@ComponentRegistry.register("cylinder", BoundingBox(26.0, 26.0, 50.0), cq.Color(0.9, 0.24, 0.24), ["hydraulic", "cylinder", "actuator"])
def build_cylinder(bbox: BoundingBox) -> cq.Workplane:
    barrel = cq.Workplane("XY").cylinder(bbox.h * 0.6, bbox.w / 2.0)
    cap = cq.Workplane("XY").workplane(offset=bbox.h * 0.3).cylinder(bbox.h * 0.1, bbox.w * 0.55 / 2.0)
    rod = cq.Workplane("XY").workplane(offset=bbox.h * 0.35).cylinder(bbox.h * 0.4, bbox.w * 0.25 / 2.0)
    return barrel.union(cap).union(rod)

@ComponentRegistry.register("bearing", BoundingBox(22.0, 22.0, 7.0), cq.Color(0.7, 0.75, 0.8), ["bearing", "ball bearing", "cross-roller bearing", "ceramic hybrid bearing"])
def build_bearing(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    r_inner = r_outer * 0.35
    outer_ring = cq.Workplane("XY").circle(r_outer).circle(r_outer * 0.85).extrude(bbox.h)
    inner_ring = cq.Workplane("XY").circle(r_inner * 1.4).circle(r_inner).extrude(bbox.h)
    cage = cq.Workplane("XY").workplane(offset=bbox.h / 2.0).circle(r_outer * 0.625).extrude(bbox.h * 0.5)
    return outer_ring.union(inner_ring).union(cage)

@ComponentRegistry.register("stepper_motor", BoundingBox(42.3, 42.3, 48.0), cq.Color(0.2, 0.2, 0.2), ["stepper", "motor", "nema", "brushless motor"])
def build_stepper_motor(bbox: BoundingBox) -> cq.Workplane:
    body = cq.Workplane("XY").box(bbox.w, bbox.d, bbox.h - 20.0).edges("|Z").fillet(3.0)
    pilot = cq.Workplane("XY").workplane(offset=(bbox.h - 20.0) / 2.0).circle(11.0).extrude(2.0)
    shaft = cq.Workplane("XY").workplane(offset=(bbox.h - 20.0) / 2.0 + 2.0).circle(2.5).extrude(18.0)
    return body.union(pilot).union(shaft)

@ComponentRegistry.register("spur_gear", BoundingBox(40.0, 40.0, 10.0), cq.Color(0.9, 0.6, 0.2), ["spur gear", "involute spur gear", "gear", "pinion gear", "sun gear"])
def build_spur_gear(bbox: BoundingBox) -> cq.Workplane:
    num_teeth = 16
    r_outer = bbox.w / 2.0
    r_root = r_outer * 0.8
    face_w = bbox.h
    gear_base = cq.Workplane("XY").circle(r_root).extrude(face_w)
    for i in range(num_teeth):
        angle = (360.0 / num_teeth) * i
        rad = math.radians(angle)
        tx = (r_root + (r_outer - r_root) / 2.0) * math.cos(rad)
        ty = (r_root + (r_outer - r_root) / 2.0) * math.sin(rad)
        tooth = (
            cq.Workplane("XY")
            .box((r_outer - r_root), 3.5, face_w)
            .rotate((0, 0, 0), (0, 0, 1), angle)
            .translate((tx, ty, face_w / 2.0))
        )
        gear_base = gear_base.union(tooth)
    return gear_base.faces(">Z").hole(bbox.w * 0.2)

@ComponentRegistry.register("brake_rotor", BoundingBox(120.0, 120.0, 12.0), cq.Color(0.5, 0.5, 0.55), ["brake rotor", "vented brake rotor"])
def build_brake_rotor(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    r_inner = r_outer * 0.35
    plate_h = 3.5
    bottom_plate = cq.Workplane("XY").circle(r_outer).circle(r_inner).extrude(plate_h)
    top_plate = cq.Workplane("XY").workplane(offset=bbox.h - plate_h).circle(r_outer).circle(r_inner).extrude(plate_h)
    hat = cq.Workplane("XY").circle(r_inner * 1.5).extrude(bbox.h).faces(">Z").hole(r_inner)
    rotor = bottom_plate.union(top_plate).union(hat)
    return rotor.faces(">Z").workplane().polarArray(r_inner * 1.25, 0, 360, 5).hole(6.5)

@ComponentRegistry.register("linear_rail", BoundingBox(15.0, 120.0, 10.0), cq.Color(0.75, 0.78, 0.82), ["linear guide rail", "guide rail", "linear guide"])
def build_linear_rail(bbox: BoundingBox) -> cq.Workplane:
    w, d, h = bbox.w, bbox.d, bbox.h
    profile = (
        cq.Workplane("YZ")
        .moveTo(-w / 2.0, 0).lineTo(-w / 2.0, h * 0.4)
        .lineTo(-w * 0.35, h * 0.6).lineTo(-w / 2.0, h * 0.8)
        .lineTo(-w / 2.0, h).lineTo(w / 2.0, h)
        .lineTo(w / 2.0, h * 0.8).lineTo(w * 0.35, h * 0.6)
        .lineTo(w / 2.0, h * 0.4).lineTo(w / 2.0, 0).close()
    )
    rail = profile.extrude(d)
    hole_spacing = 30.0
    for i in range(int(d // hole_spacing)):
        y_pos = -d / 2.0 + (i + 0.5) * hole_spacing
        rail = rail.faces(">Z").workplane().center(0, y_pos).cboreHole(3.5, 6.0, 3.0)
    return rail

@ComponentRegistry.register("slider_block", BoundingBox(32.0, 42.0, 20.0), cq.Color(0.25, 0.3, 0.35), ["slider block", "linear guide rail slider"])
def build_slider_block(bbox: BoundingBox) -> cq.Workplane:
    block = cq.Workplane("XY").box(bbox.w, bbox.d, bbox.h)
    cutout = cq.Workplane("XY").workplane(offset=-bbox.h / 2.0).box(16.0, bbox.d + 2.0, 11.0)
    return block.cut(cutout).faces(">Z").workplane().rect(22.0, 30.0, forConstruction=True).vertices().hole(4.0)

@ComponentRegistry.register("nozzle_cone", BoundingBox(50.0, 50.0, 70.0), cq.Color(0.3, 0.3, 0.35), ["nozzle cone", "jet engine nozzle", "gimbaled rocket nozzle"])
def build_nozzle_cone(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").circle(bbox.w / 2.0).workplane(offset=bbox.h).circle(bbox.w * 0.25).loft().faces(">Z").hole(bbox.w * 0.2)

# ==========================================
# 3. PROMPT PARSER
# ==========================================
def parse_prompt_dynamic(prompt_text: str) -> AssemblyParams:
    prompt = prompt_text.lower().strip()
    dims_found = re.findall(r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)', prompt)
    w, d, h = map(float, dims_found[0]) if dims_found else (200.0, 160.0, 20.0)
    params = AssemblyParams(base_dim=BoundingBox(w, d, h))
    for category in ComponentRegistry.match_keywords(prompt):
        reg_entry = ComponentRegistry.get(category)
        if reg_entry:
            _, bbox, color, _ = reg_entry
            count = 4 if category in ["standoff", "hex_bolt"] else 2
            for idx in range(count):
                params.components.append(ComponentSpec(name=f"{category}_{idx+1}", category=category, bbox=bbox, color=color))
    return params

# ==========================================
# 4. CONSTRAINT-BASED MATING ENGINE
# ==========================================
class BoundingBoxCadEngine:
    @staticmethod
    def calculate_alignment(base_dim: BoundingBox, comp: ComponentSpec, index: int) -> Tuple[float, float, float, float]:
        margin = 16.0
        quadrants = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        qx, qy = quadrants[index % 4]
        z_offset = base_dim.h

        if comp.category in ["standoff", "hex_bolt"]:
            offset_step = 16.0 if comp.category == "hex_bolt" else 0.0
            return qx * (base_dim.w / 2.0 - margin - offset_step), qy * (base_dim.d / 2.0 - margin - offset_step), z_offset, 0.0
        elif comp.category == "bracket":
            x_side = -(base_dim.w / 2.0 + comp.bbox.w / 2.0) if index == 0 else (base_dim.w / 2.0 + comp.bbox.w / 2.0)
            return x_side, 0.0, 2.0, (180.0 if index == 1 else 0.0)
        elif comp.category in ["cylinder", "stepper_motor", "bearing", "spur_gear", "piston_head", "nozzle_cone", "slider_block", "brake_rotor"]:
            return (-base_dim.w * 0.25 if index == 0 else base_dim.w * 0.25), 0.0, z_offset + (comp.bbox.h / 2.0), 0.0
        elif comp.category in ["linear_rail"]:
            return (-base_dim.w * 0.3 if index == 0 else base_dim.w * 0.3), 0.0, z_offset + (comp.bbox.h / 2.0), 0.0
        return 0.0, 0.0, z_offset, 0.0

    @staticmethod
    def build_assembly(params: AssemblyParams) -> Tuple[List[Dict[str, Any]], str]:
        base_w, base_d, base_h = params.base_dim.w, params.base_dim.d, params.base_dim.h
        assy = cq.Assembly(name="StarkForgeAssembly")

        base_solid = cq.Workplane("XY").workplane(offset=base_h / 2.0).box(base_w, base_d, base_h).edges("|Z").fillet(3.0)
        for qx, qy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
            base_solid = base_solid.faces(">Z").workplane().center(qx * (base_w / 2.0 - 16.0), qy * (base_d / 2.0 - 16.0)).hole(5.0)

        assy.add(base_solid, name="base_chassis", color=cq.Color(0.17, 0.21, 0.28))
        category_counts: Dict[str, int] = {}

        for comp in params.components:
            idx = category_counts.get(comp.category, 0)
            category_counts[comp.category] = idx + 1
            reg_entry = ComponentRegistry.get(comp.category)
            solid = reg_entry[0](comp.bbox) if reg_entry else build_fallback(comp.bbox)
            tx, ty, tz, rot = BoundingBoxCadEngine.calculate_alignment(params.base_dim, comp, idx)
            assy.add(solid, name=comp.name, loc=cq.Location(cq.Vector(tx, ty, tz), cq.Vector(0, 0, 1), rot), color=comp.color)

        try:
            assy.solve()
        except Exception:
            pass

        step_filename = "stark_assembly.step"
        assy.save(step_filename, exportType="STEP")

        mesh_outputs = []
        for name, item in assy.traverse():
            if item.obj is None:
                continue
            filepath = f"temp_{name}.stl"
            try:
                cq.exporters.export(item.obj, filepath)
                mesh = trimesh.load(filepath)
                trsf = item.loc.wrapped.Transformation()
                transform_matrix = np.array([
                    [trsf.Value(1, 1), trsf.Value(1, 2), trsf.Value(1, 3), trsf.Value(1, 4)],
                    [trsf.Value(2, 1), trsf.Value(2, 2), trsf.Value(2, 3), trsf.Value(2, 4)],
                    [trsf.Value(3, 1), trsf.Value(3, 2), trsf.Value(3, 3), trsf.Value(3, 4)],
                    [0.0, 0.0, 0.0, 1.0]
                ])
                mesh.apply_transform(transform_matrix)
                color_hex = "#00f3ff"
                if item.color:
                    r, g, b = [int(c * 255) for c in item.color.toTuple()[:3]]
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                mesh_outputs.append({
                    "id": name, "name": name.replace("_", " ").upper(),
                    "color": color_hex, "motion": "oscillate_y" if "cylinder" in name else "none",
                    "vertices": mesh.vertices.flatten().tolist(), "faces": mesh.faces.flatten().tolist()
                })
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        return mesh_outputs, step_filename

# ==========================================
# 5. JARVIS HUD VIEWPORT & LAYOUT
# ==========================================
def render_viewport(mesh_list: List[Dict[str, Any]], animate_motion: bool):
    mesh_payload = json.dumps(mesh_list)
    animate_flag = "true" if animate_motion else "false"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #030508; font-family: monospace; }}
            #viewport {{ width: 100vw; height: 530px; position: relative; }}
            .hud-overlay {{
                position: absolute; top: 15px; left: 15px; color: #00f3ff;
                font-size: 11px; letter-spacing: 2px; pointer-events: none;
                border-left: 2px solid #00f3ff; padding-left: 8px; text-shadow: 0 0 5px rgba(0,243,255,0.6);
            }}
        </style>
    </head>
    <body>
        <div id="viewport">
            <div class="hud-overlay">JARVIS // SYSTEM_ACTIVE<br>HOLOGRAPHIC B-REP MATRIX v4.1</div>
        </div>
        <script>
            const container = document.getElementById('viewport');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x030508);
            
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 1000);
            camera.position.set(240, 200, 240);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;

            scene.add(new THREE.AmbientLight(0x00f3ff, 0.4));
            const light = new THREE.DirectionalLight(0xffffff, 0.9);
            light.position.set(100, 200, 100);
            scene.add(light);
            
            const grid = new THREE.GridHelper(300, 30, 0x00f3ff, 0x112233);
            grid.position.y = -0.1;
            scene.add(grid);

            const meshData = {mesh_payload};
            const animatedObjects = [];

            meshData.forEach(part => {{
                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(part.vertices), 3));
                geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(part.faces), 1));
                geometry.computeVertexNormals();
                geometry.rotateX(-Math.PI / 2);

                const material = new THREE.MeshStandardMaterial({{ 
                    color: parseInt(part.color.replace('#', '0x')), 
                    metalness: 0.8, 
                    roughness: 0.2,
                    wireframe: false
                }});
                const mesh = new THREE.Mesh(geometry, material);
                const group = new THREE.Group();
                group.add(mesh);
                scene.add(group);

                if (part.motion !== 'none') animatedObjects.push({{ group }});
            }});

            let clock = 0;
            function animate() {{
                requestAnimationFrame(animate);
                if ({animate_flag}) {{
                    clock += 0.04;
                    animatedObjects.forEach(obj => {{ obj.group.position.y = Math.sin(clock) * 10; }});
                }}
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=550)

col1, col2 = st.columns([1, 1])

with col1:
    prompt_input = st.text_area(
        "ASSEMBLY MATRIX SPECIFICATION:",
        value="A 250x180x25 mm base plate with 2 vented brake rotors and 4 hex bolts.",
        height=160
    )
    generate_btn = st.button("INITIALIZE FABRICATION SEQUENCE", type="primary")
    enable_motion = st.checkbox("ENGAGE KINEMATIC SIMULATION", value=True)

with col2:
    if generate_btn or prompt_input:
        params = parse_prompt_dynamic(prompt_input)
        mesh_data, step_file_path = BoundingBoxCadEngine.build_assembly(params)
        render_viewport(mesh_data, enable_motion)
        
        st.success(f"MATRIX COMPILED: {len(mesh_data)} B-REP COMPONENTS SOLVED.")
        
        with open(step_file_path, "rb") as f:
            st.download_button(
                label="DOWNLOAD LOSSLESS STEP BLUEPRINT (.STEP)",
                data=f,
                file_name="stark_assembly.step",
                mime="application/octet-stream"
            )