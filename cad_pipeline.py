import ollama
from cad_agent import generate_cad_model
from inspector import render_stl_views

def analyze_cad_render(image_path: str, user_prompt: str) -> str:
    print(f"\n🔍 Visual AI Inspector analyzing: {image_path}...")

    vision_prompt = f"""
You are a senior Quality Assurance Engineer for CAD manufacturing.
The user requested: "{user_prompt}".

Examine the 4-view CAD rendering (Top, Front, Side, Isometric) provided:
1. Does the 3D geometry visually match the user's requested part?
2. Are there any visible manufacturing defects, non-physical geometry, or missing features?
3. Provide a concise QA verdict starting explicitly with either VERDICT: PASS or VERDICT: FAIL followed by your explanation.
"""

    try:
        response = ollama.chat(
            model="llava",
            messages=[
                {
                    "role": "user",
                    "content": vision_prompt,
                    "images": [image_path],
                }
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Vision inspection failed: {e}"

def run_cad_pipeline(user_prompt: str, filename_prefix: str, max_attempts: int = 3):
    current_prompt = user_prompt
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n==========================================")
        print(f" 🚀 CAD AI PIPELINE — ATTEMPT {attempt}/{max_attempts}")
        print(f"==========================================")
        
        cad_res = generate_cad_model(current_prompt, filename_prefix)
        if not cad_res["success"]:
            print(f"❌ Generation Failed: {cad_res['error']}")
            current_prompt = f"The previous CadQuery script failed with error: {cad_res['error']}. Original request: {user_prompt}. Fix the code syntax."
            continue
            
        print(f"✅ CAD compiled successfully! STL: {cad_res['stl_path']}")
        
        render_res = render_stl_views(cad_res["stl_path"], f"{filename_prefix}_attempt{attempt}")
        if not render_res["success"]:
            print(f"❌ Rendering Failed: {render_res['error']}")
            break
            
        print(f"📸 Rendered 4-view grid: {render_res['render_path']}")
        
        qa_report = analyze_cad_render(render_res["render_path"], user_prompt)
        print("\n--- QA Inspection Verdict ---")
        print(qa_report)
        print("-----------------------------\n")
        
        if "VERDICT: PASS" in qa_report.upper():
            print(f"🎉 SUCCESS! CAD model passed QA inspection on attempt {attempt}.")
            return {
                "success": True,
                "step_path": cad_res["step_path"],
                "render_path": render_res["render_path"],
                "attempts": attempt
            }
        else:
            print(f"🔄 QA Failed on attempt {attempt}. Feeding feedback back to AI for auto-correction...")
            current_prompt = f"""
Original User Request: {user_prompt}

The previous 3D model was inspected and received this QA Feedback:
{qa_report}

Please rewrite the CadQuery code to improve the design and address the QA feedback while maintaining accurate dimensions.
"""

    print("⚠️ Reached max attempts. Latest files saved in output directory.")
    return {"success": False}

if __name__ == "__main__":
    test_prompt = "Create a heavy-duty mounting bracket with 4 corner screw holes (M4 size) and a center hole for cable pass-through."
    run_cad_pipeline(test_prompt, "bracket_pipeline_test")