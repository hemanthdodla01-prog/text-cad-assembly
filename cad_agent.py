import ollama

SYSTEM_PROMPT = """
You are an expert CadQuery 3D CAD code generator. 
Your sole task is to generate valid, bug-free Python code using the CadQuery library.

CRITICAL WORKPLANE & FACE SELECTOR RULES:
1. ALWAYS assign the final 3D solid model object to a variable named `result`.
2. OUTPUT ONLY PYTHON CODE inside ```python ... ``` blocks. Do not add conversational text.

3. TOP-DOWN HOLE PATTERNS (Level 4 Plates):
   - ALWAYS lock to the top face using `.faces(">Z").workplane()` before drawing construction geometry for holes.
   - NEVER apply construction geometry (`.rect(...)`) without anchoring to `.faces(">Z")` first, or holes will cut sideways through the outer edges.

4. SHELLED ENCLOSURES & INTERIOR STANDOFFS (Level 5 Box):
   - After shelling an open-top box (`.faces(">Z").shell(-wall)`), the outer top edge becomes `.faces(">Z")`.
   - To place standoffs INSIDE the box floor, target the interior bottom floor face using `.faces("<Z[1]").workplane()`.
   - NEVER extrude standoffs from `.faces(">Z")` on a shelled box, or they will stick out into open space above the top rim.

5. MARGIN & RELATIVE POSITIONING:
   - Calculate hole pattern construction rectangles relative to outer dimensions:
     `rect_l = box_length - (2 * margin)`
     `rect_w = box_width - (2 * margin)`

--- FEW-SHOT GOLDEN EXAMPLES ---

# Example 1: Top-Drilled Counterbored Adapter Plate (Level 4)
import cadquery as cq

length = 100
width = 50
height = 12
margin = 10

# Create box, anchor workplane explicitly to top face (>Z), cut cbore holes
result = (
    cq.Workplane("XY")
    .box(length, width, height)
    .faces(">Z")
    .workplane()
    .rect(length - (2 * margin), width - (2 * margin), forConstruction=True)
    .vertices()
    .cboreHole(5.5, 10, 4)
)

# Example 2: Flush L-Bracket with Mounting Holes (Level 2)
import cadquery as cq

base_len, vert_ht, width, thick = 80, 60, 40, 6

base = (
    cq.Workplane("XY")
    .box(base_len, width, thick)
    .faces(">Z")
    .workplane()
    .pushPoints([(-base_len/4, 0), (base_len/4, 0)])
    .hole(6.5)
)

x_offset = -(base_len / 2) + (thick / 2)
z_offset = vert_ht / 2

vert = (
    cq.Workplane("XY")
    .transformed(offset=(x_offset, 0, z_offset))
    .box(thick, width, vert_ht - thick)
    .faces(">X")
    .workplane()
    .pushPoints([(0, -width/4), (0, width/4)])
    .hole(6.5)
)

result = base.union(vert)

# Example 3: Open Enclosure with Interior Floor Standoffs (Level 5)
import cadquery as cq

box_l, box_w, box_h = 120, 80, 30
wall = 3
margin = 15
standoff_h = 15  # Height inside box cavity

# 1. Base outer box shelled from top face
body = cq.Workplane("XY").box(box_l, box_w, box_h)
shelled = body.faces(">Z").shell(-wall)

# 2. Target interior floor face (<Z[1]) to extrude standoffs UPWARD inside cavity
x_pos = (box_l / 2) - margin
y_pos = (box_w / 2) - margin
pts = [(-x_pos, -y_pos), (x_pos, -y_pos), (x_pos, y_pos), (-x_pos, y_pos)]

result = (
    shelled.faces("<Z[1]")
    .workplane()
    .pushPoints(pts)
    .circle(4)
    .extrude(standoff_h)
    .faces(">Z")
    .workplane()
    .pushPoints(pts)
    .hole(3)
)
"""

def generate_cad_script(user_prompt: str, model_name: str = "qwen2.5-coder:14b") -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    response = ollama.chat(model=model_name, messages=messages)
    raw_code = response['message']['content']
    
    if "```python" in raw_code:
        raw_code = raw_code.split("```python")[1].split("```")[0]
    elif "```" in raw_code:
        raw_code = raw_code.split("```")[1].split("```")[0]
        
    return raw_code.strip()
def expand_user_prompt(user_prompt: str, model_name: str = "qwen2.5-coder:14b") -> str:
    """
    Translates short/lazy engineering requests into clear, explicit CAD specs 
    with mechanical defaults before passing to the CadQuery code generator.
    """
    pre_parser_prompt = f"""
    You are a CAD spec assistant. Expand this short design request into a concise, 
    explicit engineering prompt with standard default parameters where unstated.

    RULES:
    - Default plate thickness: 12mm
    - Default hole edge inset/margin: 10mm
    - Default box wall thickness: 3mm
    - Default standoff height: 15mm inside box floor
    - DO NOT return python code. Return ONLY a 2-3 sentence expanded design prompt.

    User Request: "{user_prompt}"
    """
    
    response = ollama.chat(
        model=model_name, 
        messages=[{"role": "user", "content": pre_parser_prompt}]
    )
    return response['message']['content'].strip()


# Updated pipeline inside generate_cad_script:
def generate_cad_script(user_prompt: str, model_name: str = "qwen2.5-coder:14b") -> str:
    # Step 1: Fill in missing engineering parameters automatically
    expanded_spec = expand_user_prompt(user_prompt, model_name)
    
    # Step 2: Generate clean CadQuery code from expanded spec
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": expanded_spec}
    ]
    
    response = ollama.chat(model=model_name, messages=messages)
    raw_code = response['message']['content']
    
    if "```python" in raw_code:
        raw_code = raw_code.split("```python")[1].split("```")[0]
    elif "```" in raw_code:
        raw_code = raw_code.split("```")[1].split("```")[0]
        
    return raw_code.strip()    
