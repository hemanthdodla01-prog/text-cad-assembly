import os
import trimesh
import matplotlib.pyplot as plt

RENDER_DIR = "cad_renders"

def ensure_render_dir():
    if not os.path.exists(RENDER_DIR):
        os.makedirs(RENDER_DIR)

def render_stl_views(stl_path: str, output_prefix: str = "inspection") -> dict:
    ensure_render_dir()

    if not os.path.exists(stl_path):
        return {"success": False, "error": f"STL file not found at: {stl_path}"}

    try:
        mesh = trimesh.load(stl_path)
        
        fig = plt.figure(figsize=(10, 10))
        fig.suptitle(f"CAD Visual Inspection Report: {os.path.basename(stl_path)}", fontsize=14, fontweight='bold')

        views = [
            ("Isometric View", 30, 45, 1),
            ("Top View (XY)", 90, -90, 2),
            ("Front View (XZ)", 0, -90, 3),
            ("Side View (YZ)", 0, 0, 4)
        ]

        vertices = mesh.vertices
        faces = mesh.faces

        for title, elev, azim, subplot_idx in views:
            ax = fig.add_subplot(2, 2, subplot_idx, projection='3d')
            ax.plot_trisurf(
                vertices[:, 0], vertices[:, 1], vertices[:, 2],
                triangles=faces,
                cmap='Blues',
                edgecolor='darkblue',
                linewidth=0.1,
                alpha=0.8
            )
            ax.view_init(elev=elev, azim=azim)
            ax.set_title(title, fontsize=10)
            ax.axis('off')

        plt.tight_layout()
        output_image_path = os.path.join(RENDER_DIR, f"{output_prefix}_multiview.png")
        plt.savefig(output_image_path, dpi=150)
        plt.close(fig)

        return {
            "success": True,
            "render_path": output_image_path,
            "volume_mm3": round(mesh.volume, 2),
            "is_watertight": mesh.is_watertight,
            "bounding_box": mesh.extents.tolist()
        }

    except Exception as e:
        return {"success": False, "error": f"Rendering failed: {str(e)}"}