import streamlit as st
import re
import json
import trimesh
import cadquery as cq
import numpy as np
import os
import math
import pandas as pd
import streamlit.components.v1 as components
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Callable

st.set_page_config(page_title="JARVIS // Industrial CAD/CAM Forge", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# INDUSTRIAL HUD INJECTION (CSS)
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
    
    h1, h2, h3 {
        color: #00f3ff !important;
        font-family: 'Share Tech Mono', monospace;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(0,243,255,0.4);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MATERIALS & DENSITY ANALYTICS
# ==========================================
MATERIAL_DENSITIES = {
    "Aluminum 6061-T6": 2.70,     # g/cm3
    "Stainless Steel 316": 8.00,   # g/cm3
    "Carbon Steel": 7.85,          # g/cm3
    "Titanium Gr5": 4.43,          # g/cm3
    "Brass C360": 8.40             # g/cm3
}

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
    material: str = "Aluminum 6061-T6"

@dataclass
class AssemblyParams:
    base_dim: BoundingBox = field(default_factory=lambda: BoundingBox(200.0, 160.0, 20.0))
    components: List[ComponentSpec] = field(default_factory=list)

# ==========================================
# 2. PARAMETRIC COMPONENT REGISTRY
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
    def match_keywords(cls, prompt: str) -> List[Tuple[str, int]]:
        matched = []
        for key, (_, _, _, keywords) in cls._registry.items():
            for kw in keywords:
                pattern = r'(\d+)?\s*' + re.escape(kw)
                matches = re.findall(pattern, prompt)
                if matches:
                    total_count = sum(int(m) if m else 1 for m in matches)
                    matched.append((key, total_count))
                    break
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

@ComponentRegistry.register("bearing", BoundingBox(22.0, 22.0, 7.0), cq.Color(0.7, 0.75, 0.8), ["bearing", "ball bearing", "roller bearing"])
def build_bearing(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    r_inner = r_outer * 0.35
    outer_ring = cq.Workplane("XY").circle(r_outer).circle(r_outer * 0.85).extrude(bbox.h)
    inner_ring = cq.Workplane("XY").circle(r_inner * 1.4).circle(r_inner).extrude(bbox.h)
    cage = cq.Workplane("XY").workplane(offset=bbox.h / 2.0).circle(r_outer * 0.625).extrude(bbox.h * 0.5)
    return outer_ring.union(inner_ring).union(cage)

@ComponentRegistry.register("brake_rotor", BoundingBox(120.0, 120.0, 12.0), cq.Color(0.5, 0.5, 0.55), ["brake rotor", "rotor"])
def build_brake_rotor(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    r_inner = r_outer * 0.35
    plate_h = 3.5
    bottom_plate = cq.Workplane("XY").circle(r_outer).circle(r_inner).extrude(plate_h)
    top_plate = cq.Workplane("XY").workplane(offset=bbox.h - plate_h).circle(r_outer).circle(r_inner).extrude(plate_h)
    hat = cq.Workplane("XY").circle(r_inner * 1.5).extrude(bbox.h).faces(">Z").hole(r_inner)
    rotor = bottom_plate.union(top_plate).union(hat)
    return rotor.faces(">Z").workplane().polarArray(r_inner * 1.25, 0, 360, 5).hole(6.5)

# ==========================================
# 3. DYNAMIC PROMPT PARSER
# ==========================================
def parse_prompt_dynamic(prompt_text: str, default_material: str) -> AssemblyParams:
    prompt = prompt_text.lower().strip()
    dims_found = re.findall(r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)', prompt)
    w, d, h = map(float, dims_found[0]) if dims_found else (200.0, 160.0, 20.0)
    params = AssemblyParams(base_dim=BoundingBox(w, d, h))

    matched_categories = ComponentRegistry.match_keywords(prompt)
    for category, count in matched_categories:
        reg_entry = ComponentRegistry.get(category)
        if reg_entry:
            _, bbox, color, _ = reg_entry
            for idx in range(count):
                params.components.append(
                    ComponentSpec(name=f"{category}_{idx+1}", category=category, bbox=bbox, color=color, material=default_material)
                )
    return params

# ==========================================
# 4. INDUSTRIAL CAD & ANALYTICS ENGINE
# ==========================================
class IndustrialCadEngine:
    @staticmethod
    def calculate_alignment(base_dim: BoundingBox, comp: ComponentSpec, index: int) -> Tuple[float, float, float, float]:
        grid_cols = max(1, int(math.sqrt(index + 1)))
        spacing_x = base_dim.w / (grid_cols + 1)
        spacing_y = base_dim.d / (grid_cols + 1)
        row = index // grid_cols
        col = index % grid_cols
        tx = -base_dim.w / 2.0 + spacing_x * (col + 1)
        ty = -base_dim.d / 2.0 + spacing_y * (row + 1)
        tz = base_dim.h + (comp.bbox.h / 2.0)
        return tx, ty, tz, 0.0

    @staticmethod
    def calculate_fea_stress(mesh: trimesh.Trimesh) -> List[float]:
        """Simulate Von Mises stress heatmap across mesh vertices."""
        z = mesh.vertices[:, 2]
        z_norm = (z - z.min()) / (z.max() - z.min() + 1e-6)
        r = np.linalg.norm(mesh.vertices[:, :2], axis=1)
        r_norm = r / (r.max() + 1e-6)
        # Higher stress near constraints and bending points
        stress = np.clip(0.75 * (1.0 - z_norm) + 0.45 * (1.0 - r_norm), 0.0, 1.0)
        return stress.tolist()

    @staticmethod
    def build_assembly(params: AssemblyParams) -> Tuple[List[Dict[str, Any]], str, str, List[Dict[str, Any]], List[str]]:
        base_w, base_d, base_h = params.base_dim.w, params.base_dim.d, params.base_dim.h
        assy = cq.Assembly(name="IndustrialAssembly")

        base_solid = cq.Workplane("XY").workplane(offset=base_h / 2.0).box(base_w, base_d, base_h).edges("|Z").fillet(3.0)
        for qx, qy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
            base_solid = base_solid.faces(">Z").workplane().center(qx * (base_w / 2.0 - 16.0), qy * (base_d / 2.0 - 16.0)).hole(5.0)

        assy.add(base_solid, name="chassis_base", color=cq.Color(0.17, 0.21, 0.28))
        
        category_counts: Dict[str, int] = {}
        transformed_solids: Dict[str, cq.Workplane] = {"chassis_base": base_solid}
        bom_records = []

        # Chassis base metrics
        base_vol_mm3 = base_solid.val().Volume()
        base_density = MATERIAL_DENSITIES["Aluminum 6061-T6"]
        base_mass_kg = (base_vol_mm3 * 1e-3) * base_density / 1000.0
        bom_records.append({
            "Part Name": "CHASSIS BASE", "Category": "Chassis", "Qty": 1,
            "Material": "Aluminum 6061-T6", "Volume (cm³)": round(base_vol_mm3 / 1000.0, 2),
            "Mass (kg)": round(base_mass_kg, 3)
        })

        for comp in params.components:
            idx = category_counts.get(comp.category, 0)
            category_counts[comp.category] = idx + 1
            reg_entry = ComponentRegistry.get(comp.category)
            solid = reg_entry[0](comp.bbox) if reg_entry else build_fallback(comp.bbox)
            
            tx, ty, tz, rot = IndustrialCadEngine.calculate_alignment(params.base_dim, comp, idx)
            loc = cq.Location(cq.Vector(tx, ty, tz), cq.Vector(0, 0, 1), rot)
            assy.add(solid, name=comp.name, loc=loc, color=comp.color)
            transformed_solids[comp.name] = solid.val().moved(loc)

            vol_mm3 = solid.val().Volume()
            density = MATERIAL_DENSITIES.get(comp.material, 2.70)
            mass_kg = (vol_mm3 * 1e-3) * density / 1000.0
            bom_records.append({
                "Part Name": comp.name.upper(), "Category": comp.category, "Qty": 1,
                "Material": comp.material, "Volume (cm³)": round(vol_mm3 / 1000.0, 2),
                "Mass (kg)": round(mass_kg, 3)
            })

        # Volumetric Interference Detector
        interferences = []
        solid_names = list(transformed_solids.keys())
        for i in range(len(solid_names)):
            for j in range(i + 1, len(solid_names)):
                n1, n2 = solid_names[i], solid_names[j]
                s1, s2 = transformed_solids[n1], transformed_solids[n2]
                try:
                    overlap = s1.intersect(s2)
                    if overlap.Volume() > 0.1:
                        interferences.append(f"COLLISION: {n1} <-> {n2} ({overlap.Volume():.2f} mm³ overlap)")
                except Exception:
                    pass

        # 1. Export 3D STEP Assembly File
        step_filename = "industrial_assembly.step"
        assy.save(step_filename, exportType="STEP")

        # 2. Export 2D DXF Vector Laser Cutting Profile
        dxf_filename = "laser_profile.dxf"
        try:
            flat_profile = base_solid.section()
            cq.exporters.export(flat_profile, dxf_filename)
        except Exception:
            cq.exporters.export(base_solid, dxf_filename)

        # 3. Generate 3D Meshes & FEA Stress Heatmap Data
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
                
                fea_stresses = IndustrialCadEngine.calculate_fea_stress(mesh)
                
                color_hex = "#00f3ff"
                if item.color:
                    r, g, b = [int(c * 255) for c in item.color.toTuple()[:3]]
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                
                mesh_outputs.append({
                    "id": name, "name": name.replace("_", " ").upper(),
                    "color": color_hex, "vertices": mesh.vertices.flatten().tolist(),
                    "faces": mesh.faces.flatten().tolist(), "fea_stress": fea_stresses
                })
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)

        return mesh_outputs, step_filename, dxf_filename, bom_records, interferences

# ==========================================
# 5. THREE.JS VIEWPORT (CAD & FEA MODES)
# ==========================================
def render_viewport(mesh_list: List[Dict[str, Any]]):
    mesh_payload = json.dumps(mesh_list)
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #030508; font-family: monospace; }}
            #viewport {{ width: 100vw; height: 500px; position: relative; }}
            #hud {{ position: absolute; top: 10px; left: 10px; z-index: 10; display: flex; gap: 10px; }}
            .btn {{ background: rgba(0,243,255,0.1); border: 1px solid #00f3ff; color: #00f3ff; padding: 6px 12px; cursor: pointer; font-family: monospace; }}
            .btn:hover {{ background: #00f3ff; color: #000; }}
        </style>
    </head>
    <body>
        <div id="hud">
            <button class="btn" onclick="setRenderMode('cad')">3D CAD SHADED</button>
            <button class="btn" onclick="setRenderMode('fea')">FEA STRESS HEATMAP</button>
        </div>
        <div id="viewport"></div>
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
            const meshObjects = [];

            function stressToColor(val) {{
                // Blue (low) -> Green -> Yellow -> Red (high stress)
                const r = Math.sin(val * Math.PI - Math.PI / 2) * 0.5 + 0.5;
                const g = Math.sin(val * Math.PI) * 0.5 + 0.5;
                const b = Math.cos(val * Math.PI - Math.PI / 2) * 0.5 + 0.5;
                return [r, g, b];
            }}

            meshData.forEach(part => {{
                const geometry = new THREE.BufferGeometry();
                const verts = new Float32Array(part.vertices);
                geometry.setAttribute('position', new THREE.BufferAttribute(verts, 3));
                geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(part.faces), 1));
                geometry.computeVertexNormals();
                geometry.rotateX(-Math.PI / 2);

                // Cad Material
                const cadMat = new THREE.MeshStandardMaterial({{ 
                    color: parseInt(part.color.replace('#', '0x')), 
                    metalness: 0.8, roughness: 0.2
                }});

                // FEA Material with Vertex Colors
                const colors = [];
                part.fea_stress.forEach(s => {{
                    const [r, g, b] = stressToColor(s);
                    colors.push(r, g, b);
                }});
                const feaGeometry = geometry.clone();
                feaGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
                const feaMat = new THREE.MeshBasicMaterial({{ vertexColors: true, wireframe: false }});

                const mesh = new THREE.Mesh(geometry, cadMat);
                mesh.userData = {{ cadMat, feaMat, feaGeometry, defaultGeometry: geometry }};
                scene.add(mesh);
                meshObjects.push(mesh);
            }});

            window.setRenderMode = function(mode) {{
                meshObjects.forEach(m => {{
                    if (mode === 'fea') {{
                        m.material = m.userData.feaMat;
                        m.geometry = m.userData.feaGeometry;
                    }} else {{
                        m.material = m.userData.cadMat;
                        m.geometry = m.userData.defaultGeometry;
                    }}
                }});
            }};

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=520)

# ==========================================
# 6. APPLICATION INTERFACE
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    prompt_input = st.text_area(
        "PARAMETRIC SPECIFICATION:",
        value="A 250x180x25 mm base plate with 12 hex bolts, 2 vented brake rotors, and 4 bearings.",
        height=140
    )
    material_choice = st.selectbox("PRIMARY ASSEMBLY MATERIAL:", list(MATERIAL_DENSITIES.keys()))
    generate_btn = st.button("EXECUTE CAD/CAM PIPELINE", type="primary")

with col2:
    if generate_btn or prompt_input:
        params = parse_prompt_dynamic(prompt_input, material_choice)
        mesh_data, step_file, dxf_file, bom_data, collisions = IndustrialCadEngine.build_assembly(params)
        
        render_viewport(mesh_data)

        # Summary Metrics
        df_bom = pd.DataFrame(bom_data)
        total_mass = df_bom["Mass (kg)"].sum()
        total_parts = len(df_bom)

        m1, m2, m3 = st.columns(3)
        m1.metric("TOTAL PARTS", f"{total_parts} Units")
        m2.metric("ASSEMBLY MASS", f"{total_mass:.2f} kg")
        m3.metric("CLEARANCE STATUS", "PASS" if not collisions else "INTERFERENCE DETECTED")

        if collisions:
            for c in collisions:
                st.error(c)

        st.subheader("BILL OF MATERIALS (BOM)")
        st.dataframe(df_bom, use_container_width=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            with open(step_file, "rb") as f:
                st.download_button(
                    label="DOWNLOAD STEP (.STEP)",
                    data=f,
                    file_name="industrial_assembly.step",
                    mime="application/octet-stream"
                )
        with d2:
            with open(dxf_file, "rb") as f:
                st.download_button(
                    label="EXPORT 2D DXF (.DXF)",
                    data=f,
                    file_name="laser_profile.dxf",
                    mime="application/octet-stream"
                )
        with d3:
            csv_bom = df_bom.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="EXPORT BOM (.CSV)",
                data=csv_bom,
                file_name="assembly_bom.csv",
                mime="text/csv"
            )