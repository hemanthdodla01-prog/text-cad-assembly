import ollama
from inspector import render_stl_views

def analyze_cad_render(image_path: str, user_prompt: str) -> str:
    """
    Sends the 4-view CAD render image to the vision model to inspect 
    whether it visually satisfies the user's design requirements.
    """
    print(f"\n🔍 Visual AI Inspector analyzing: {image_path}...")

    vision_prompt = f"""
You are a senior Quality Assurance Engineer for CAD manufacturing.
The user requested: "{user_prompt}".

Examine the 4-view CAD rendering (Top, Front, Side, Isometric) provided:
1. Does the 3D geometry visually match the user's requested part?
2. Are there any visible manufacturing defects, non-physical geometry, or missing features?
3. Provide a concise 2-sentence QA verdict (PASS/FAIL) and explanation.
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


if __name__ == "__main__":
    stl_path = "cad_output/spacer_test.stl"
    original_prompt = "Create a cylindrical spacer with an outer diameter of 30mm, inner diameter of 10mm, and height of 25mm."

    # Render views
    render_res = render_stl_views(stl_path, "spacer_qa")
    
    if render_res["success"]:
        # Run Vision Review
        feedback = analyze_cad_render(render_res["render_path"], original_prompt)
        print("\n--- QA Inspection Report ---")
        print(feedback)
        print("----------------------------\n")