"""Render training pairs for a "turn the character" model with Blender.

Every character is posed from a few frames of a few animations, then rendered facing the camera and turned to 7 other
facings, with the camera, light and pose kept the same. Each pair is:
  control  the character facing the camera
  target   the same character, same pose, turned to another facing
  caption  which way to turn

    blender -b -P blender/render_turn_pairs.py -- --models "characters/*.glb" --out turn_pairs [--size 1024]
        [--actions Idle,Walking_A,Running_A,Cheer] [--frames 2] [--holdout Rogue_Hooded] [--samples 24]

Works with rigged .glb/.gltf/.fbx characters whose animations are inside the file (the free CC0 KayKit packs are).
Writes <out>/renders/, <out>/train.jsonl, <out>/dataset.toml and <out>/sample_prompts.txt (from --holdout characters)."""
import argparse, glob, json, math, os, sys
import bpy
from mathutils import Vector

# Degrees the character turns (seen from above, counterclockwise) and how the caption says it.
FACINGS = [(0, 'toward the camera'), (45, 'toward the camera and to the right'), (90, 'to the right'),
           (135, 'away from the camera and to the right'), (180, 'away from the camera'),
           (-135, 'away from the camera and to the left'), (-90, 'to the left'), (-45, 'toward the camera and to the left')]
CAPTION = 'Turn the character so it faces {}. Keep the same character, outfit, colours and pose.'


def args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--size', type=int, default=1024)
    ap.add_argument('--actions', default='Idle,Walking_A,Running_A,Cheer,1H_Melee_Attack_Chop,Spellcast_Shoot')
    ap.add_argument('--frames', type=int, default=2, help='frames taken from each animation')
    ap.add_argument('--holdout', default='', help='comma-separated character names kept out of training, used for test jobs')
    ap.add_argument('--samples', type=int, default=24)
    ap.add_argument('--elevation', type=float, default=25, help='camera angle above the ground, degrees')
    ap.add_argument('--front-turn', type=float, default=0, help='extra degrees if your characters do not face the camera at 0')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    a = ap.parse_args(argv)
    a.models = sorted({p for m in a.models for p in (glob.glob(m) or [m])})
    return a


def setup_render(size, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for kind in ('OPTIX', 'CUDA'):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
            except TypeError:
                continue
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = 'GPU'
                print('render device', kind)
                break
    except Exception as e:
        print('rendering on the CPU:', e)
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('white')
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (1, 1, 1, 1)
    bg.inputs[1].default_value = 1.0


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials, bpy.data.images,
                 bpy.data.cameras, bpy.data.lights):
        for x in list(coll):
            if x.users == 0:
                coll.remove(x)


def load(path):
    before = set(bpy.data.objects)
    if path.lower().endswith(('.glb', '.gltf')):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.import_scene.fbx(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in objs if o.type == 'ARMATURE')
    return objs, arm


def world_bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.type != 'MESH' or o.hide_render:
            continue
        e = o.evaluated_get(dg)
        m = e.to_mesh()
        pts += [e.matrix_world @ v.co for k, v in enumerate(m.vertices) if k % 4 == 0]
        e.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def frames_of(action, n):
    s, e = action.frame_range
    return [round(s + (e - s) * (k + 0.5) / n) for k in range(n)]


def render_character(path, a, renders):
    clear()
    objs, arm = load(path)
    name = os.path.splitext(os.path.basename(path))[0]
    pivot = bpy.data.objects.new('pivot', None)
    bpy.context.collection.objects.link(pivot)
    for o in objs:
        if o.parent is None:
            o.parent = pivot
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    bpy.context.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    bpy.context.scene.camera = cam
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    bpy.context.collection.objects.link(sun)
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))  # stays on the camera side; only the character turns
    arm.animation_data_create()
    wanted = [x for x in a.actions.split(',') if x]
    # Importers add suffixes to animation names (KayKit's "Idle" arrives as "Idle_Rig"), so match on the start of the name.
    acts = [next(act for act in bpy.data.actions if act.name == x or act.name.startswith(x + '_'))
            for x in wanted if any(act.name == x or act.name.startswith(x + '_') for act in bpy.data.actions)]
    acts = acts or list(bpy.data.actions)[:3]
    shots = []
    for act in acts:
        arm.animation_data.action = act
        for f in frames_of(act, a.frames):
            bpy.context.scene.frame_set(f)
            # Frame the camera on this pose turned every way, so the control and every target share one scale.
            lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
            for deg, _ in FACINGS:
                pivot.rotation_euler = (0, 0, math.radians(deg + a.front_turn))
                bpy.context.view_layer.update()
                l, h = world_bounds(objs)
                lo = Vector(map(min, lo, l))
                hi = Vector(map(max, hi, h))
            c = (lo + hi) / 2
            cam.data.ortho_scale = max(hi.z - lo.z, hi.x - lo.x, hi.y - lo.y) * 1.2
            el = math.radians(a.elevation)
            cam.location = (c.x, c.y - 20 * math.cos(el), c.z + 20 * math.sin(el))
            cam.rotation_euler = (math.pi / 2 - el, 0, 0)
            for deg, words in FACINGS:
                pivot.rotation_euler = (0, 0, math.radians(deg + a.front_turn))
                fn = os.path.join(renders, f'{name}_{act.name}_{f:03d}_{deg:+04d}.png')
                bpy.context.scene.render.filepath = fn
                bpy.ops.render.render(write_still=True)
                shots.append((name, act.name, f, deg, words, fn))
            print(f'{name} {act.name} frame {f}: 8 facings', flush=True)
    return shots


def write_toml(out, size):
    with open(os.path.join(out, 'dataset.toml'), 'w') as f:
        f.write(f'[general]\nresolution = [{size}, {size}]\nbatch_size = 1\nenable_bucket = false\n\n'
                f'[[datasets]]\nimage_jsonl_file = "{os.path.join(out, "train.jsonl").replace(os.sep, "/")}"\n'
                f'cache_directory = "{os.path.join(out, "cache").replace(os.sep, "/")}"\ncontrol_resolution = [{size}, {size}]\n')


def main():
    a = args()
    out = os.path.abspath(a.out)
    renders = os.path.join(out, 'renders')
    os.makedirs(renders, exist_ok=True)
    setup_render(a.size, a.samples)
    held = {x for x in a.holdout.split(',') if x}
    rows, prompts = [], []
    for path in a.models:
        shots = render_character(path, a, renders)
        front = {(n, act, f): fn for n, act, f, deg, _, fn in shots if deg == 0}
        first = shots[0]
        for n, act, f, deg, words, fn in shots:
            if deg == 0:
                continue
            if n in held:
                if (act, f) == (first[1], first[2]) and deg in (90, 180, -45):
                    prompts.append(f'{CAPTION.format(words)} --ci {front[(n, act, f)]} --w {a.size} --h {a.size} --s 20 --d {len(prompts) + 1}')
                continue
            rows.append({'image_path': fn, 'control_path': front[(n, act, f)], 'caption': CAPTION.format(words)})
    with open(os.path.join(out, 'train.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')
    with open(os.path.join(out, 'sample_prompts.txt'), 'w') as f:
        f.write('\n'.join(prompts) + '\n')
    write_toml(out, a.size)
    print(f'{len(rows)} pairs from {len(a.models) - len(held)} characters, {len(prompts)} test jobs from {sorted(held)} -> {out}')


main()
