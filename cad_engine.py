import cadquery as cq
import ollama
import streamlit as st
import traceback

SYSTEM_PROMPT = """
You are an expert CadQuery 3D CAD code generator. 
Your sole task is to generate valid, bug-free Python code using the CadQuery library.

CRITICAL WORKPLANE & FACE SELECTOR RULES:
1. ALWAYS assign the final 3D solid model object to a variable named `result`.
2. OUTPUT ONLY PYTHON CODE inside ```python ... ``` blocks. Do not add conversational text.
3. TOP-DOWN HOLE PATTERNS: Lock to the top face using `.faces(">Z").workplane()` before drawing construction geometry for holes.
4. SHELLED ENCLOSURES: Target the interior floor face using `.faces("<Z[1]").workplane()` to extrude interior standoffs upward.
5. DYNAMIC MARGINS: Use relative bounds like `rect(length - 2*margin, width - 2*margin, forConstruction=True)` instead of hardcoded coordinates.
"""

def expand_user_prompt(user_prompt: str, model_name: str) -> str:
    """Translates short user input into explicit CAD specifications with engineering defaults."""
    pre_parser = f"""
    Expand this short CAD request into explicit geometric specs with standard defaults where unstated.
    - Default plate thickness: 12mm
    - Default hole margin: 10mm
    - Default box wall thickness: 3mm
    - Default standoff height: 15mm inside box cavity
    Return ONLY a 2-3 sentence expanded specification. No code.
    Request: "{user_prompt}"
    """
    response = ollama.chat(model=model_name, messages=[{"role": "user", "content": pre_parser}])
    return response['message']['content'].strip()


def query_llm_for_code(prompt: str, model_name: str) -> str:
    """Calls Ollama and extracts clean Python code."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    response = ollama.chat(model=model_name, messages=messages)
    raw = response['message']['content']
    
    if "```python" in raw:
        return raw.split("```python")[1].split("```")[0].strip()
    elif "```" in raw:
        return raw.split("```")[1].split("```")[0].strip()
    return raw.strip()


def validate_and_execute_geometry(code_str: str):
    """
    Executes code in isolated memory & performs strict 3D manifold/volume checks.
    Returns: (is_valid: bool, error_message: str, cq_object: Workplane)
    """
    local_scope = {}
    try:
        # 1. Compile and execute in isolated namespace
        exec(code_str, {"cq": cq}, local_scope)
        
        if "result" not in local_scope:
            return False, "Code executed successfully, but variable `result` was not defined.", None
            
        cad_obj = local_scope["result"]
        
        # 2. Check CadQuery Object Structure
        if not hasattr(cad_obj, "val"):
            return False, "The `result` object is not a valid CadQuery object.", None
            
        shape_val = cad_obj.val()
        
        # 3. Topology & Manifold Check
        if not shape_val.isValid():
            return False, "Geometry Error: Generated shape has invalid or non-manifold topology.", None
            
        # 4. Volume Validation Check
        if shape_val.Volume() <= 0:
            return False, f"Geometry Error: Invalid shape volume ({shape_val.Volume()} mm³).", None
            
        return True, "OK", cad_obj

    except Exception as e:
        tb = traceback.format_exc()
        # Return truncated traceback to keep prompt context clean
        short_tb = "\n".join(tb.splitlines()[-5:])
        return False, f"Python Execution Exception: {str(e)}\n{short_tb}", None


@st.cache_data(show_spinner=False)
def generate_solid_cad(user_prompt: str, model_name: str = "qwen2.5-coder:14b", max_retries: int = 3) -> dict:
    """
    Master Production Pipeline:
    - Cached by Streamlit to prevent duplicate LLM calls
    - Auto-Expands user prompt with CAD defaults
    - Validates execution & geometry manifoldness
    - Feeds exceptions back to LLM for self-correction (Auto-Healing Loop)
    """
    expanded_prompt = expand_user_prompt(user_prompt, model_name)
    current_prompt = expanded_prompt
    
    attempts_log = []
    
    for attempt in range(1, max_retries + 1):
        # Step A: LLM Code Generation
        code = query_llm_for_code(current_prompt, model_name)
        
        # Step B: Execution & Geometry Validation
        is_valid, error_msg, cad_object = validate_and_execute_geometry(code)
        
        if is_valid:
            return {
                "success": True,
                "attempts": attempt,
                "code": code,
                "object": cad_object,
                "logs": attempts_log
            }
            
        # Step C: Prepare Auto-Healing Feedback Loop
        attempts_log.append(f"Attempt {attempt} failed: {error_msg}")
        
        current_prompt = f"""
        The previously generated CadQuery code failed execution or geometry validation.

        ORIGINAL REQUEST:
        {user_prompt}

        FAULTY CODE:
        ```python
        {code}
        ```

        ERROR TRACEBACK / VALIDATION FAILURE:
        {error_msg}

        INSTRUCTIONS:
        Fix the errors (check workplane selections, face targets, or missing variables) and return ONLY the corrected Python code block.
        """

    return {
        "success": False,
        "attempts": max_retries,
        "code": code,
        "object": None,
        "error": f"Failed after {max_retries} attempts.",
        "logs": attempts_log
    }