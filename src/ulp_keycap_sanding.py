import solid2 as s

outer = s.cube([27, 27.5, 3.5], center=True)
inner = s.cube([16.5, 16.75, 5], center=True)
notch = s.up(1.75)(s.cube([7, 7, 1.5], center=True))
holder = s.difference()(s.cube([12.5, 10.5, 3.5], center=True), notch)
base = s.down(1.25)(s.cube([27, 27.5, 1], center=True))
shape = s.union()(s.difference()(outer, inner), base, holder)

s.scad_render_to_file(shape, "ulp_keycap_sander.scad")
