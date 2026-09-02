import json
import subprocess
import os

# ---------------------------------------------------------
# Step 1: OpenSCAD Compiler Functions (Deterministic CAD)
# ---------------------------------------------------------
def compile_box(spec: dict) -> str:
    """Compiles a parametric shelled box with standoffs in OpenSCAD."""
    l = spec.get("length", 100)
    w = spec.get("width", 50)
    h = spec.get("height", 30)
    wall = spec.get("wall_thickness", 3)
    
    scad_code = f"""
    // Outer Shell
    difference() {{
        cube([{l}, {w}, {h}]);
        translate([{wall}, {wall}, {wall}])
            cube([{l - 2*wall}, {w - 2*wall}, {h}]);
    }}
    
    // Corner Standoffs
    margin = {wall + 5};
    standoff_h = {h - wall};
    
    module standoff(x, y) {{
        translate([x, y, {wall}])
            difference() {{
                cylinder(r=4, h=standoff_h, $fn=30);
                cylinder(r=1.5, h=standoff_h + 1, $fn=20);
            }}
    }}
    
    standoff(margin, margin);
    standoff({l} - margin, margin);
    standoff(margin, {w} - margin);
    standoff({l} - margin, {w} - margin);
    """
    return scad_code


def compile_plate(spec: dict) -> str:
    """Compiles a mounting plate with corner holes in OpenSCAD."""
    l = spec.get("length", 100)
    w = spec.get("width", 50)
    t = spec.get("thickness", 12)
    hole_d = spec.get("hole_diameter", 5.5)
    margin = spec.get("margin", 10)
    
    scad_code = f"""
    difference() {{
        cube([{l}, {w}, {t}]);
        
        // 4 Corner Holes
        translate([{margin}, {margin}, -1]) cylinder(d={hole_d}, h={t + 2}, $fn=30);
        translate([{l - margin}, {margin}, -1]) cylinder(d={hole_d}, h={t + 2}, $fn=30);
        translate([{margin}, {w - margin}, -1]) cylinder(d={hole_d}, h={t + 2}, $fn=30);
        translate([{l - margin}, {w - margin}, -1]) cylinder(d={hole_d}, h={t + 2}, $fn=30);
    }}
    """
    return scad_code

# Master Compiler Router
def build_scad_from_json(json_str: str) -> str:
    data = json.loads(json_str)
    part_type = data.get("part_type", "plate")
    
    if part_type == "box":
        return compile_box(data)
    else:
        return compile_plate(data)