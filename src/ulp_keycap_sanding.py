import solid2 as s

outer = s.cube([27, 27.5, 3.5], center=True)
inner = s.cube([16.5, 16.75, 5], center=True)
notch = s.up(1.75)(s.cube([7, 7, 1.5], center=True))
holder = s.difference()(s.cube([12.5, 10.5, 3.5], center=True), notch)

base_height = 4
base = s.down(1.25 + base_height / 2)(s.cube([27, 27.5, base_height], center=True))

feet_height = 3
feet = s.translate(7, 7, -1.5 - base_height)(s.cylinder(d=11, h=feet_height))

shape = s.union()(
    s.difference()(outer, inner, feet),
    base,
    holder,
)

shape = s.difference()(
    shape,
    feet,
    s.mirrorX()(feet),
    s.mirrorY()(feet),
    s.mirrorX()(s.mirrorY()(feet)),
)

s.scad_render_to_file(shape, "ulp_keycap_sander.scad")
