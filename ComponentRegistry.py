# Hardware Registrations for Aerospace, Automotive, Robotics, & Automation Systems

@ComponentRegistry.register("bearing", BoundingBox(22.0, 22.0, 7.0), cq.Color(0.7, 0.75, 0.8), ["bearing", "ball bearing", "cross-roller bearing", "ceramic hybrid bearing"])
def build_bearing(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    r_inner = r_outer * 0.35
    return cq.Workplane("XY").circle(r_outer).circle(r_inner).extrude(bbox.h)

@ComponentRegistry.register("stepper_motor", BoundingBox(42.3, 42.3, 48.0), cq.Color(0.2, 0.2, 0.2), ["stepper", "motor", "nema", "brushless motor"])
def build_stepper_motor(bbox: BoundingBox) -> cq.Workplane:
    body = cq.Workplane("XY").box(bbox.w, bbox.d, bbox.h - 20.0)
    shaft = cq.Workplane("XY").workplane(offset=(bbox.h - 20.0) / 2.0).circle(2.5).extrude(20.0)
    return body.union(shaft)

@ComponentRegistry.register("spur_gear", BoundingBox(30.0, 30.0, 8.0), cq.Color(0.9, 0.6, 0.2), ["spur gear", "involute spur gear", "gear", "pinion gear", "sun gear"])
def build_spur_gear(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    return cq.Workplane("XY").circle(r_outer).extrude(bbox.h).faces(">Z").hole(r_outer * 0.3)

@ComponentRegistry.register("helical_gear", BoundingBox(35.0, 35.0, 10.0), cq.Color(0.85, 0.55, 0.15), ["helical gear", "helical groove"])
def build_helical_gear(bbox: BoundingBox) -> cq.Workplane:
    r_outer = bbox.w / 2.0
    return cq.Workplane("XY").circle(r_outer).extrude(bbox.h).faces(">Z").hole(r_outer * 0.25)

@ComponentRegistry.register("bevel_gear", BoundingBox(30.0, 30.0, 12.0), cq.Color(0.8, 0.5, 0.2), ["bevel gear", "spider gear"])
def build_bevel_gear(bbox: BoundingBox) -> cq.Workplane:
    r_bottom = bbox.w / 2.0
    r_top = bbox.w / 4.0
    return (
        cq.Workplane("XY")
        .circle(r_bottom)
        .workplane(offset=bbox.h)
        .circle(r_top)
        .loft()
        .faces(">Z")
        .hole(bbox.w * 0.2)
    )

@ComponentRegistry.register("worm_gear", BoundingBox(20.0, 20.0, 40.0), cq.Color(0.75, 0.6, 0.3), ["worm gear", "worm shaft"])
def build_worm_gear(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").cylinder(bbox.h, bbox.w / 2.0).faces(">Z").hole(bbox.w * 0.25)

@ComponentRegistry.register("lead_screw", BoundingBox(12.0, 12.0, 100.0), cq.Color(0.7, 0.7, 0.75), ["lead screw", "ball screw"])
def build_lead_screw(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").cylinder(bbox.h, bbox.w / 2.0)

@ComponentRegistry.register("lead_screw_nut", BoundingBox(22.0, 22.0, 15.0), cq.Color(0.85, 0.7, 0.3), ["lead screw nut", "anti-backlash nut", "ball nut"])
def build_lead_screw_nut(bbox: BoundingBox) -> cq.Workplane:
    flange = cq.Workplane("XY").circle(bbox.w / 2.0).extrude(4.0)
    body = cq.Workplane("XY").circle(bbox.w * 0.35).extrude(bbox.h)
    return flange.union(body).faces(">Z").hole(bbox.w * 0.25)

@ComponentRegistry.register("flange", BoundingBox(50.0, 50.0, 10.0), cq.Color(0.6, 0.65, 0.7), ["flange", "pipe flange"])
def build_flange(bbox: BoundingBox) -> cq.Workplane:
    base = cq.Workplane("XY").circle(bbox.w / 2.0).extrude(bbox.h).faces(">Z").hole(bbox.w * 0.4)
    return base

@ComponentRegistry.register("piston_head", BoundingBox(40.0, 40.0, 30.0), cq.Color(0.65, 0.7, 0.75), ["piston head", "piston", "inner piston"])
def build_piston_head(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").cylinder(bbox.h, bbox.w / 2.0)

@ComponentRegistry.register("brake_rotor", BoundingBox(120.0, 120.0, 12.0), cq.Color(0.5, 0.5, 0.55), ["brake rotor", "vented brake rotor"])
def build_brake_rotor(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").circle(bbox.w / 2.0).circle(bbox.w * 0.3).extrude(bbox.h)

@ComponentRegistry.register("impeller", BoundingBox(60.0, 60.0, 25.0), cq.Color(0.8, 0.4, 0.2), ["impeller", "inducer", "turbine blade"])
def build_impeller(bbox: BoundingBox) -> cq.Workplane:
    hub = cq.Workplane("XY").cone(bbox.h, bbox.w * 0.3, bbox.w * 0.1)
    return hub

@ComponentRegistry.register("nozzle_cone", BoundingBox(50.0, 50.0, 70.0), cq.Color(0.3, 0.3, 0.35), ["nozzle cone", "jet engine nozzle", "gimbaled rocket nozzle"])
def build_nozzle_cone(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").cone(bbox.h, bbox.w / 2.0, bbox.w * 0.25).faces(">Z").hole(bbox.w * 0.2)

@ComponentRegistry.register("pulley", BoundingBox(35.0, 35.0, 12.0), cq.Color(0.4, 0.4, 0.45), ["pulley", "v-belt pulley", "cable-driven pulley"])
def build_pulley(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").circle(bbox.w / 2.0).extrude(bbox.h).faces(">Z").hole(bbox.w * 0.2)

@ComponentRegistry.register("omni_roller", BoundingBox(15.0, 15.0, 25.0), cq.Color(0.2, 0.5, 0.8), ["omni-directional wheel roller", "roller"])
def build_omni_roller(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").sphere(bbox.w / 2.0)

@ComponentRegistry.register("linear_rail", BoundingBox(15.0, 100.0, 10.0), cq.Color(0.75, 0.78, 0.82), ["linear guide rail", "guide rail", "linear guide"])
def build_linear_rail(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").box(bbox.w, bbox.d, bbox.h)

@ComponentRegistry.register("slider_block", BoundingBox(30.0, 40.0, 20.0), cq.Color(0.25, 0.3, 0.35), ["slider block", "linear guide rail slider"])
def build_slider_block(bbox: BoundingBox) -> cq.Workplane:
    return cq.Workplane("XY").box(bbox.w, bbox.d, bbox.h)