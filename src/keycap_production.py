import glob
import os

import solid2 as s


def import_file(fname, convexity=4):
    full_name = fname + r".stl"
    print("IMPORTING FROM {}".format(full_name))

    return s.import_stl(full_name, convexity=convexity)


def group_keycaps_production(file, number_marking):
    shape = import_file(os.path.join("./../src/parts/ulp_keycap_models", file))
    text = s.mirrorZ()(
        s.mirrorX()(
            s.forward(4)(
                s.left(6)(
                    s.linear_extrude(height=0.65)(s.text(str(number_marking), size=3))
                )
            )
        )
    )
    shape = s.union()(text, shape)

    shapes = [shape]
    amount = 10
    for i in range(amount):
        displacement = s.left(17 * i)
        shapes.append(displacement(shape))
        if i != 0:
            shapes.append(
                displacement(
                    s.right(8.5)(s.up(2.2 + 0.75)(s.cube([3, 3, 1.5], center=True)))
                )
            )
    shape = s.union()(*shapes)
    s.scad_render_to_file(
        shape, os.path.join("things", f"{file}_bundle_{number_marking}.scad")
    )
    # s.render_to_stl_file(
    #     shape, os.path.join("things", f"{file}_bundle_{number_marking}.stl")
    # )


if __name__ == "__main__":
    for i, file in enumerate(glob.glob("./src/parts/ulp_keycap_models/*")):
        name = os.path.basename(file)[:-4]
        group_keycaps_production(name, i)
