import cadquery as cq

# 1. Main shaft section (120mm long, 25mm diameter -> 12.5mm radius)
main = cq.Workplane("XY").circle(12.5).extrude(120)

# 2. Stepped end section (40mm long, 20mm diameter -> 10mm radius)
shaft = main.faces(">Z").workplane().circle(10).extrude(40)

# 3. Add 2mm chamfers to far ends
shaft = shaft.faces(">Z or <Z").chamfer(2)

# 4. Create keyway cutter (6mm wide x 3mm deep x 50mm long)
# Center along main shaft (Z = 60)
keyway = (
    cq.Workplane("YZ")
    .workplane(offset=12.5 - 3)
    .center(0, 60)
    .rect(6, 50)
    .extrude(10)
)

# 5. Perform boolean cut
result = shaft.cut(keyway)

# Export STL to view in Preview
cq.exporters.export(result, "cad_output/go_kart_correct.stl")
print("Saved correct model to cad_output/go_kart_correct.stl")