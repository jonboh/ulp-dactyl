import getopt
import importlib
import json
import os
import os.path as path
import subprocess
import sys
from os import path

import numpy as np
import solid2 as s
from numpy import mod, pi
from solid2 import difference, hull, translate

import fill_extension
import wrist
from clusters.carbonfet import CarbonfetCluster
from clusters.custom_cluster import CustomCluster
from clusters.default_cluster import DefaultCluster
from clusters.mini import MiniCluster
from clusters.minidox import MinidoxCluster
from clusters.minithicc import Minithicc
from clusters.minithicc3 import Minithicc3
from clusters.trackball_btu import TrackballBTU
from clusters.trackball_cj import TrackballCJ
from clusters.trackball_jonboh import TrackballJonboh
from clusters.trackball_orbyl import TrackballOrbyl
from clusters.trackball_three import TrackballThree
from clusters.trackball_wilder import TrackballWild
from json_loader import load_json


def get_git_branch():

    try:
        output = str(
            subprocess.check_output(
                ['git', 'branch'], cwd=path.abspath('.'), universal_newlines=True
            )
        )
        branch = [a for a in output.split('\n') if a.find('*') >= 0][0]
        return branch[branch.find('*') + 2:]
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        log("No git repository found.", "ERROR")
        return None

def deg2rad(degrees: float) -> float:
    return degrees * pi / 180


def rad2deg(rad: float) -> float:
    return rad * 180 / pi


debug_exports = False
debug_trace = False


def debugprint(info):
    if debug_trace:
        print(info)

###############################################
# EXTREMELY UGLY BUT FUNCTIONAL BOOTSTRAP
###############################################

## IMPORT DEFAULT CONFIG IN CASE NEW PARAMETERS EXIST


def make_dactyl():
    right_cluster = None
    left_cluster = None

    left_wall_x_offset = 8
    left_wall_x_row_offsets = [
        18, 43, 28, 28, 28, 28, 28, 28
    ]
    left_wall_z_offset = 3
    left_wall_lower_y_offset = 0
    left_wall_lower_z_offset = 0

    symmetry = None
    column_style = None
    column_style = "fixed"
    save_path = path.join(r".", "things")

    matrix = {
        "right": [],
        "left": []
    }

    def cluster(side="right"):
        return right_cluster if side == "right" else left_cluster

    import generate_configuration as cfg
    for item in cfg.shape_config:
        globals()[item] = cfg.shape_config[item]

    data = None

    overrides_name = ""

    local_branch = get_git_branch()
        ## CHECK FOR CONFIG FILE AND WRITE TO ANY VARIABLES IN FILE.
    opts, args = getopt.getopt(sys.argv[1:], "", ["config=", "save_path=", "overrides="])
    for opt, arg in opts:
        if opt in '--config':
            with open(os.path.join(r".", "configs", arg + '.json'), mode='r') as fid:
                data = json.load(fid)
        elif opt in '--save_path':
            print("save_path set to argument: ", arg)
            save_path = arg
        elif opt in '--overrides':
            print("overrides set to: ", arg)
            overrides_name = arg

    if data is None:
        print(f">>> Using config run_config.json on Git branch {local_branch}")
        data = load_json(os.path.join("src", "run_config.json"), None, save_path)
        # with open(os.path.join("src", "run_config.json"), mode='r') as fid:
        #     data = json.load(fid)

    if data["overrides"] not in [None, ""]:
        if overrides_name != "":
            print("YO! overrides param set in run_config.json AND in command line 'overrides' argument! Can't compute!")
            sys.exit(99)
        overrides_name = data["overrides"]

        # for item in override_data:
        #     data[item] = override_data[item]
    if overrides_name != "":
        print(f"Importing config overrides for: {overrides_name}")
        save_path = path.join(save_path, overrides_name)
        override_file = path.join(save_path, overrides_name + '.json')
        with open(override_file, mode='r') as fid:
            data = load_json(override_file, data, save_path)

    try:
        if data["branch"] not in ["", None]:
            if data["branch"] != local_branch:
                print(f"INCORRECT GIT BRANCH! Local is {local_branch} but config requires {data['branch']}.  Exiting.")
                sys.exit(101)
    except Exception:
        print("No 'branch' param found on config.")

    for item in data:
        globals()[item] = data[item]

    if save_name not in ['', None]:
        config_name = save_name
    elif overrides_name is not None:
        config_name = overrides_name + "_" + str(nrows) + "x" + str(ncols) + "_" + thumb_style

    ENGINE = data["ENGINE"]
    # Really rough setup.  Check for ENGINE, set it not present from configuration.
    try:
        print('Found Current Engine in Config = {}'.format(ENGINE))
    except Exception:
        print('Engine Not Found in Config')
        ENGINE = 'solid'
        # ENGINE = 'cadquery'
        print('Setting Current Engine = {}'.format(ENGINE))

    parts_path = os.path.abspath(path.join(r"src", "parts"))

    if save_dir not in ['', None, '.']:
        save_path = save_dir
        print("save_path set to save_dir json setting: ", save_path)
            # parts_path = path.join(r"..", r"..", "src", "parts")
        # parts_path = path.join(r"..", r"..", "src", "parts")

        # parts_path = path.jo

    dir_exists = os.path.isdir(save_path)
    if not dir_exists:
        os.makedirs(save_path, exist_ok=True)

    ###############################################
    # END EXTREMELY UGLY BOOTSTRAP
    ###############################################

    ####################################################
    # HELPER FUNCTIONS TO MERGE CADQUERY AND OPENSCAD
    ####################################################

    if ENGINE == 'cadquery':
        globals().update(importlib.import_module("helpers_cadquery").__dict__)
    else:
        globals().update(importlib.import_module("helpers_solid").__dict__)

    ####################################################
    # END HELPER FUNCTIONS
    ####################################################

    if oled_mount_type is not None and oled_mount_type != "NONE":
        for item in oled_configurations[oled_mount_type]:
            globals()[item] = oled_configurations[oled_mount_type][item]

    if nrows > 5:
        column_style = column_style_gt5

    centerrow = nrows - centerrow_offset

    lastrow = nrows - 1
    cornerrow = lastrow
    lastcol = ncols - 1

    oled_row = nrows - 1
    plate_file = None

    # Derived values
    if plate_style in ['NUB', 'HS_NUB']:
        keyswitch_height = nub_keyswitch_height
        keyswitch_width = nub_keyswitch_width
    elif plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
        keyswitch_height = undercut_keyswitch_height
        keyswitch_width = undercut_keyswitch_width
    else:
        keyswitch_height = hole_keyswitch_height
        keyswitch_width = hole_keyswitch_width

    if "AMOEBA" in plate_style:
        symmetry = "asymmetric"
        plate_file = path.join(parts_path, r"amoeba_key_hole")
    elif 'HS_' in plate_style:
        symmetry = "asymmetric"
        pname = r"hot_swap_plate"
        if plate_file_name is not None:
            pname = plate_file_name
        plate_file = path.join(parts_path, pname)
        # plate_offset = 0.0 # this overwrote the config variable

    if (trackball_in_wall or ('TRACKBALL' in thumb_style)) and not ball_side == 'both':
        symmetry = "asymmetric"

    mount_width = keyswitch_width + 2 * plate_rim_width
    mount_height = keyswitch_height + 2 * plate_rim_height
    mount_thickness = plate_thickness

    if default_1U_cluster and thumb_style == 'DEFAULT':
        double_plate_height = (.7 * sa_double_length - mount_height) / 3
        # double_plate_height = (.95 * sa_double_length - mount_height) / 3
    elif thumb_style == 'DEFAULT':
        double_plate_height = (.90 * sa_double_length - mount_height) / 3
    else:
        double_plate_height = (sa_double_length - mount_height) / 3

    wide = 22 if not oled_horizontal else tbiw_left_wall_x_offset_override
    short = 8 if not oled_horizontal else tbiw_left_wall_x_offset_override

    if oled_mount_type is not None and oled_mount_type != "NONE":
        left_wall_x_offset = oled_left_wall_x_offset_override
        if nrows <= 4:
            left_wall_x_row_offsets = [wide, wide, wide, wide]
        elif nrows == 5:
            left_wall_x_row_offsets = [wide, wide, wide, wide, short]
        elif nrows == 6:
            left_wall_x_row_offsets = [wide, wide, wide, short, short, short]
        # left_wall_x_row_offsets = [22 if row > oled_row else 8 for row in range(lastrow)]
        left_wall_z_offset = oled_left_wall_z_offset_override
        left_wall_lower_y_offset = oled_left_wall_lower_y_offset
        left_wall_lower_z_offset = oled_left_wall_lower_z_offset

    cap_top_height = plate_thickness + sa_profile_key_height
    row_radius = ((mount_height + extra_height) / 2) / (np.sin(alpha / 2)) + cap_top_height
    column_radius = (
                            ((mount_width + extra_width) / 2) / (np.sin(beta / 2))
                    ) + cap_top_height
    column_x_delta = -1 - column_radius * np.sin(beta)
    column_base_angle = beta * (centercol - 2)

    teensy_width = 20
    teensy_height = 12
    teensy_length = 33
    teensy2_length = 53
    teensy_pcb_thickness = 2
    teensy_offset_height = 5
    teensy_holder_top_length = 18
    teensy_holder_width = 7 + teensy_pcb_thickness
    teensy_holder_height = 6 + teensy_width

    # todo
    def build_matrix():
        return matrix

    def build_layout():
        return matrix

    # save_path = path.join("..", "things", save_dir)
    if not path.isdir(save_path):
        os.mkdir(save_path)

    if layouts is not None:
        matrix = build_layout()
    else:
        left_matrix = build_matrix()

    def col(from_column):
        c = from_column + shift_column  # if not inner_column else from_column - 1
        if c < 0:
            c = 0
        if c > ncols - 1:
            c = ncols -1
        return c

    def column_offset(column: int) -> list:
        c = column - shift_column

        if c < 0:
            c = 0
        if c > ncols - 1:
            c = ncols - 1

        return column_offsets[c]


    def single_plate(cylinder_segments=100, side="right"):
        if plate_style == "ULP":
            plate = box(mount_width, mount_height, mount_thickness)
            plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))

            plate = s.difference()(plate, surface_pcb())

        elif plate_style == "MXLEDBIT":
            pcb_width = 19
            pcb_length = 19
            pcb_height = 1.6

            # degrees = np.degrees(alpha / 2)
            # frame = box(pcb_width + 2, pcb_length + 2, pcb_height * 2)
            # cutout = union([box(pcb_width - 1, pcb_length - 1, pcb_height * 4),
            #                 translate(box(pcb_width + 0.2, pcb_height + 0.2, pcb_height * 2), (0, 0, -(pcb_height / 2)))])
            # # # frame = difference(frame, [box(pcb_width - 1, pcb_length - 1, pcb_height * 4)])
            # frame = difference(frame, [cutout])
            # connector = translate(rotate(box(pcb_width + 2, extra_height * 2, pcb_height * 2), (degrees, 0, 0)), (0, (pcb_length / 2), 0))
            # frame = union([frame, connector])

            degrees = np.degrees(alpha / 2)
            frame = box(21, 21, 3)
            # # frame = difference(frame, [box(pcb_width - 1, pcb_length - 1, pcb_height * 4)])
            frame = difference(frame, [box(18.5, 18.5, 5)])
            frame = difference(frame, [box(19.5, 19.5, 2.5)])
            connector = translate(rotate(box(21, 4, 2.5), (degrees, 0, 0)), (0, 11.5, 0))
            frame = translate(union([frame, connector]), (0, 0, -5))
            return frame

        elif plate_style in ['NUB', 'HS_NUB']:
            tb_border = (mount_height - keyswitch_height) / 2
            top_wall = box(mount_width, tb_border, plate_thickness)
            top_wall = translate(top_wall, (0, (tb_border / 2) + (keyswitch_height / 2), plate_thickness / 2))

            lr_border = (mount_width - keyswitch_width) / 2
            left_wall = box(lr_border, mount_height, plate_thickness)
            left_wall = translate(left_wall, ((lr_border / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

            side_nub = cylinder(radius=1, height=2.75)
            side_nub = rotate(side_nub, (90, 0, 0))
            side_nub = translate(side_nub, (keyswitch_width / 2, 0, 1))

            nub_cube = box(1.5, 2.75, plate_thickness)
            nub_cube = translate(nub_cube, ((1.5 / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

            side_nub2 = tess_hull(shapes=(side_nub, nub_cube))
            side_nub2 = union([side_nub2, side_nub, nub_cube])

            plate_half1 = union([top_wall, left_wall, side_nub2])
            plate_half2 = plate_half1
            plate_half2 = mirror(plate_half2, 'XZ')
            plate_half2 = mirror(plate_half2, 'YZ')

            plate = union([plate_half1, plate_half2])

        # elif plate_style in "AMOEBA":  # 'HOLE' or default, square cutout for non-nub designs.
        #     plate = box(mount_width, mount_height, mount_thickness)
        #     plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))
        #
        #     shape_cut = box(keyswitch_width + 2, keyswitch_height + 2, mount_thickness * 2 + .02)
        #     shape_cut = translate(shape_cut, (0.0, 0.0, mount_thickness - .01))
        #
        #     plate = difference(plate, [shape_cut])

        else:  # 'HOLE' or default, square cutout for non-nub designs.
            plate = box(mount_width, mount_height, mount_thickness)
            plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))

            shape_cut = box(keyswitch_width, keyswitch_height, mount_thickness * 2 + .02)
            shape_cut = translate(shape_cut, (0.0, 0.0, mount_thickness - .01))

            plate = difference(plate, [shape_cut])

        if plate_file is not None:
            socket = import_file(plate_file)
            socket = translate(socket, [0, 0, plate_thickness + plate_offset])
            plate = union([plate, socket])

        if plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH', 'AMOEBA']:
            if plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
                undercut = box(
                    keyswitch_width + 2 * clip_undercut,
                    keyswitch_height + 2 * clip_undercut,
                    mount_thickness
                )

            if plate_style in ['NOTCH', 'HS_NOTCH', 'AMOEBA']:
                undercut = box(
                    notch_width,
                    keyswitch_height + 2 * clip_undercut,
                    mount_thickness
                )
                undercut = union([undercut,
                    box(
                        keyswitch_width + 2 * clip_undercut,
                        notch_width,
                        mount_thickness
                    )
                ])

            undercut = translate(undercut, (0.0, 0.0, -clip_thickness + mount_thickness / 2.0))

            if ENGINE == 'cadquery' and undercut_transition > 0:
                undercut = undercut.faces("+Z").chamfer(undercut_transition, clip_undercut)

            plate = difference(plate, [undercut])

        # if plate_file is not None:
        #     socket = import_file(plate_file)
        #
        #     socket = translate(socket, [0, 0, plate_thickness + plate_offset])
        #     plate = union([plate, socket])

        if plate_holes:
            half_width = plate_holes_width / 2.
            half_height = plate_holes_height / 2.
            x_off = plate_holes_xy_offset[0]
            y_off = plate_holes_xy_offset[1]
            holes = [
                translate(
                    cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                    (x_off + half_width, y_off + half_height, plate_holes_depth / 2 - .01)
                ),
                translate(
                    cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                    (x_off - half_width, y_off + half_height, plate_holes_depth / 2 - .01)
                ),
                translate(
                    cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                    (x_off - half_width, y_off - half_height, plate_holes_depth / 2 - .01)
                ),
                translate(
                    cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                    (x_off + half_width, y_off - half_height, plate_holes_depth / 2 - .01)
                ),
            ]
            # plate = difference(plate, holes)


        if side == "left":
            plate = mirror(plate, 'YZ')

        return plate


    ################
    ## SA Keycaps ##
    ################

    def ulp_cap(Usize=1):
        bl2 = 15.5 / 2
        bw2 = 15.5 / 2
        m = 15.5 / 2
        pl2 = 3.5
        pw2 = 3.5
        key_height = 1.5
        key_top_height = 4. # height of the top of the keycap with respect to the base

        k1 = polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = extrude_poly(outer_poly=k1, height=0.1)
        k1 = translate(k1, (0, 0, 0.05))
        k2 = polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = extrude_poly(outer_poly=k2, height=0.1)
        k2 = translate(k2, (0, 0, key_height))
        if m > 0:
            m1 = polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = extrude_poly(outer_poly=m1, height=0.1)
            m1 = translate(m1, (0, 0, key_height))
            key_cap = hull_from_shapes((k1, k2, m1))
        else:
            key_cap = hull_from_shapes((k1, k2))

        key_cap = translate(key_cap, (0, 0, key_top_height - key_height + plate_thickness))

        if show_pcbs:
            key_cap = add([key_cap, key_pcb()])

        return key_cap
    def choc_cap(Usize=1):
        bl2 = 16.75 / 2
        bw2 = 16.75 / 2
        m = 15.5 / 2
        pl2 = 3.5
        pw2 = 3.5
        key_height = 3.7

        k1 = polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = extrude_poly(outer_poly=k1, height=0.1)
        k1 = translate(k1, (0, 0, 0.05))
        k2 = polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = extrude_poly(outer_poly=k2, height=0.1)
        k2 = translate(k2, (0, 0, key_height))
        if m > 0:
            m1 = polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = extrude_poly(outer_poly=m1, height=0.1)
            m1 = translate(m1, (0, 0, key_height))
            key_cap = hull_from_shapes((k1, k2, m1))
        else:
            key_cap = hull_from_shapes((k1, k2))

        key_cap = translate(key_cap, (0, 0, 5 + plate_thickness))

        if show_pcbs:
            key_cap = add([key_cap, key_pcb()])

        return key_cap

    def dsa_cap(Usize=1):
        bl2 = 18.5 / 2
        bw2 = 18.5 / 2
        m = 15 / 2
        pl2 = 6
        pw2 = 6
        key_height = 8

        k1 = polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = extrude_poly(outer_poly=k1, height=0.1)
        k1 = translate(k1, (0, 0, 0.05))
        k2 = polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = extrude_poly(outer_poly=k2, height=0.1)
        k2 = translate(k2, (0, 0, key_height))
        if m > 0:
            m1 = polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = extrude_poly(outer_poly=m1, height=0.1)
            m1 = translate(m1, (0, 0, 5.0))
            key_cap = hull_from_shapes((k1, k2, m1))
        else:
            key_cap = hull_from_shapes((k1, k2))

        key_cap = translate(key_cap, (0, 0, 6 + plate_thickness))

        if show_pcbs:
            key_cap = add([key_cap, key_pcb()])

        return key_cap

    def sa_cap(Usize=1):
        # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
        # sa_length = 18.25

        if Usize == 1:
            bl2 = 18.5 / 2
            bw2 = 18.5 / 2
            m = 17 / 2
            pl2 = 6
            pw2 = 6

        elif Usize == 2:
            bl2 = sa_length
            bw2 = sa_length / 2
            m = 0
            pl2 = 16
            pw2 = 6

        elif Usize == 1.5:
            bl2 = sa_length / 2
            bw2 = 27.94 / 2
            m = 0
            pl2 = 6
            pw2 = 11

        elif Usize == 1.25:  # todo
            bl2 = sa_length / 2
            bw2 = 22.64 / 2
            m = 0
            pl2 = 16
            pw2 = 11

        k1 = polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = extrude_poly(outer_poly=k1, height=0.1)
        k1 = translate(k1, (0, 0, 0.05))
        k2 = polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = extrude_poly(outer_poly=k2, height=0.1)
        k2 = translate(k2, (0, 0, 12.0))
        if m > 0:
            m1 = polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = extrude_poly(outer_poly=m1, height=0.1)
            m1 = translate(m1, (0, 0, 6.0))
            key_cap = hull_from_shapes((k1, k2, m1))
        else:
            key_cap = hull_from_shapes((k1, k2))

        key_cap = translate(key_cap, (0, 0, 6 + plate_thickness))

        if show_pcbs:
            key_cap = add([key_cap, key_pcb()])

        return key_cap


    def _ulp_key_pcb():
        tolerance_cylinders = 0.4
        tolerance_thickness = 0.4
        tolerance_lengths = 0.4
        pcb_thickness_ = pcb_thickness + tolerance_thickness
        pcb_width_ = pcb_width + tolerance_lengths
        pcb_height_ = pcb_height + tolerance_lengths
        if not quickly:
            centering_hole_position = (0,3)
            centering_hole_radius = 1.5
            corner_radius = 2
            pcb = box(pcb_width_, pcb_height_, pcb_thickness_)
            solder_clearance = translate(box(4, 3, 2), [0,0,-pcb_thickness_/2-1+0.01])
            diode_clearance = translate(box(2.5, 4, 2), [3.4,2.85,-pcb_thickness_/2-1+0.01])
            clearances = [
                    translate(solder_clearance, [7, 0, 0]),
                    translate(solder_clearance, [-7, 0,0]),
                    translate(rotate(solder_clearance, [0,0,90]), [0, 6.4,0]),
                    translate(rotate(solder_clearance, [0,0,90]), [0,-6.4,0]),
                    diode_clearance,
                    ]
            centering_hole = translate(cylinder(centering_hole_radius-tolerance_cylinders/2, pcb_thickness_+.2), [centering_hole_position[0], centering_hole_position[1], 0])
            corner_hole = cylinder(corner_radius-tolerance_cylinders/2, pcb_thickness_ + .2)
            holes = [
                translate(corner_hole, (pcb_width_ / 2, pcb_height_ / 2, 0)),
                translate(corner_hole, (-pcb_width_ / 2, pcb_height_ / 2, 0)),
                translate(corner_hole, (-pcb_width_ / 2, -pcb_height_ / 2, 0)),
                translate(corner_hole, (pcb_width_ / 2, -pcb_height_ / 2, 0)),
                centering_hole,
            ]
            pcb = difference(pcb, holes)
            pcb = union([pcb, *clearances])
            pcb = translate(pcb, [0,0,-pcb_thickness_/2])
        else:
            pcb = box(pcb_width_, pcb_height_, pcb_thickness_)
            pcb = translate(pcb, [0,0,-pcb_thickness_/2])
        holder_height_mul = 2
        holder = s.difference()(s.translate([0,0, -holder_height_mul/2*pcb_thickness])(s.cube([pcb_width_-0.01,pcb_height_-0.01,holder_height_mul*pcb_thickness-0.01], center=True)), pcb)
        column_top = s.translate([0,0, -holder_height_mul*pcb_thickness])(s.cube([pcb_width_-0.01,pcb_height_-0.01,0.01], center=True))
        # export_file(holder, fname="things/pcb_holder")
        # export_file(pcb, fname="things/pcb")
        return pcb, holder, column_top

    def surface_pcb():
        return s.translate([0,0,pcb_thickness/2+mount_thickness/2+(mount_thickness-pcb_thickness)/2+0.02])(_ulp_key_pcb()[0])

    def key_pcb():
        return _ulp_key_pcb()[0]

    def key_pcb_holder():
        return _ulp_key_pcb()[1]

    def key_pcb_column_top():
        return _ulp_key_pcb()[2]
    #########################
    ## Placement Functions ##
    #########################


    def rotate_around_x(position, angle):
        # debugprint('rotate_around_x()')
        t_matrix = np.array(
            [
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)


    def rotate_around_y(position, angle):
        # debugprint('rotate_around_y()')
        t_matrix = np.array(
            [
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)


    def apply_key_geometry(
            shape,
            translate_fn,
            rotate_x_fn,
            rotate_y_fn,
            column,
            row,
            column_style=column_style,
    ):
        debugprint('apply_key_geometry()')

        column_angle = beta * (centercol - column)

        column_x_delta_actual = column_x_delta
        if (pinky_1_5U and column == lastcol):
            if row >= first_1_5U_row and row <= last_1_5U_row:
                column_x_delta_actual = column_x_delta - 1.5
                column_angle = beta * (centercol - column - 0.27)

        if column_style == "orthographic":
            column_z_delta = column_radius * (1 - np.cos(column_angle))
            shape = translate_fn(shape, [0, 0, -row_radius])
            shape = rotate_x_fn(shape, alpha * (centerrow - row))
            shape = translate_fn(shape, [0, 0, row_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(
                shape, [-(column - centercol) * column_x_delta_actual, 0, column_z_delta]
            )
            shape = translate_fn(shape, column_offset(column))

        elif column_style == "fixed":
            shape = rotate_y_fn(shape, fixed_angles[column])
            shape = translate_fn(shape, [fixed_x[column], 0, fixed_z[column]])
            shape = translate_fn(shape, [0, 0, -(row_radius + fixed_z[column])])
            shape = rotate_x_fn(shape, alpha * (centerrow - row))
            shape = translate_fn(shape, [0, 0, row_radius + fixed_z[column]])
            shape = rotate_y_fn(shape, fixed_tenting)
            shape = translate_fn(shape, [0, column_offset(column)[1], 0])

        else:
            shape = translate_fn(shape, [0, 0, -row_radius])
            shape = rotate_x_fn(shape, alpha * (centerrow - row))
            shape = translate_fn(shape, [0, 0, row_radius])
            shape = translate_fn(shape, [0, 0, -column_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(shape, [0, 0, column_radius])
            shape = translate_fn(shape, column_offset(column))

        shape = rotate_y_fn(shape, tenting_angle)
        shape = translate_fn(shape, [0, 0, keyboard_z_offset])

        return shape

    def bottom_key(column):
        # if column < shift_column:  # attempt to make inner columns fewer keys
        #     return nrows - 3
        if all_last_rows:
            return nrows - 1
        cluster_columns = 2 + shift_column
        if column in list(range(cluster_columns)):
            return nrows - 2
        # if column == 2:
        #     if inner_column:
        #         return nrows - 2
        if full_last_rows or column < cluster_columns + 2:
            return nrows - 1

        return nrows - 2


    def first_bottom_key():
        for c in range(ncols - 1):
            if bottom_key(c) == nrows - 1:
                return c


    def valid_key(column, row):
        return row <= bottom_key(column)

    def x_rot(shape, angle):
        # debugprint('x_rot()')
        return rotate(shape, [rad2deg(angle), 0, 0])


    def y_rot(shape, angle):
        # debugprint('y_rot()')
        return rotate(shape, [0, rad2deg(angle), 0])


    def key_place(shape, column, row):
        debugprint('key_place()')
        return apply_key_geometry(shape, translate, x_rot, y_rot, column, row)


    def cluster_key_place(shape, column, row):
        debugprint('key_place()')
        c = col(column)
        # if c < 0:
        #     c = 0
        # if c > ncols - 1:
        #     c = ncols - 1
        # c = column if not inner_column else column + 1
        return apply_key_geometry(shape, translate, x_rot, y_rot, c, row)
    def add_translate(shape, xyz):
        debugprint('add_translate()')
        vals = []
        for i in range(len(shape)):
            vals.append(shape[i] + xyz[i])
        return vals


    def key_position(position, column, row):
        debugprint('key_position()')
        return apply_key_geometry(
            position, add_translate, rotate_around_x, rotate_around_y, column, row
        )


    def _key_holes(side="right"):
        holes = []
        for column in range(ncols):
            for row in range(nrows):
                if valid_key(column, row):
                    holes.append(key_place(single_plate(side=side), column, row))
        return holes

    def _place_shape_on_keyplace(shape):
        holes = []
        for column in range(ncols):
            for row in range(nrows):
                if valid_key(column, row):
                    holes.append(key_place(shape, column, row))
        return holes

    def key_holes(side="right"):
        debugprint('key_holes()')
        shape = union(_key_holes(side))
        return shape

    def key_holes_filled(side="right"):
        return list(map(lambda hole: hull_from_shapes([hole]), _key_holes(side)))


    def surface_pcbs():
        pcbs = None
        single_pcb = translate(surface_pcb(), [0,0,0.25])
        # single_pcb = key_pcb()
        for column in range(ncols):
            for row in range(nrows):
                if valid_key(column, row):
                    if pcbs is None:
                        pcbs = key_place(single_pcb, column, row)
                    else:
                        pcbs = add([pcbs, key_place(single_pcb, column, row)])

        return pcbs

    def pcbs():
        pcbs = None
        single_pcb = translate(key_pcb(), [0,0,0.25])
        # single_pcb = key_pcb()
        for column in range(ncols):
            for row in range(nrows):
                if valid_key(column, row):
                    if pcbs is None:
                        pcbs = key_place(single_pcb, column, row)
                    else:
                        pcbs = add([pcbs, key_place(single_pcb, column, row)])

        return pcbs

    def caps():
        caps = None
        for column in range(ncols):
            size = 1
            if pinky_1_5U and column == lastcol:
                if row >= first_1_5U_row and row <= last_1_5U_row:
                    size = 1.5
            for row in range(nrows):
                if valid_key(column, row):
                    if caps is None:
                        caps = key_place(ulp_cap(size), column, row)
                    else:
                        caps = add([caps, key_place(ulp_cap(size), column, row)])

        return caps


    ####################
    ## Web Connectors ##
    ####################


    def web_post():
        debugprint('web_post()')
        post = box(post_size, post_size, web_thickness)
        post = translate(post, (0, 0, plate_thickness - (web_thickness / 2)))
        return post


    def web_post_tr(off_w=0, off_h=0, off_z=0):
        return translate(web_post(), ((mount_width / 2.0) + off_w, (mount_height / 2.0) + off_h, 0))


    def web_post_tl(off_w=0, off_h=0, off_z=0):
        return translate(web_post(), (-(mount_width / 2.0) - off_w, (mount_height / 2.0) + off_h, 0))


    def web_post_bl(off_w=0, off_h=0, off_z=0):
        return translate(web_post(), (-(mount_width / 2.0) - off_w, -(mount_height / 2.0) - off_h, 0))


    def web_post_br(off_w=0, off_h=0, off_z=0):
        return translate(web_post(), ((mount_width / 2.0) + off_w, -(mount_height / 2.0) - off_h, 0))

    def get_torow(column):
        return bottom_key(column) + 1
        # torow = lastrow
        # if full_last_rows or (column == 4 and inner_column):
        #     torow = lastrow + 1
        #
        # if column in [0, 1]:
        #     torow = lastrow
        # return torow


    def _connectors():
        debugprint('connectors()')
        hulls = []
        for column in range(ncols - 1):
            torow = get_torow(column)
            if not full_last_rows and column == 3:
                torow -= 1

            for row in range(torow):  # need to consider last_row?
                # for row in range(nrows):  # need to consider last_row?
                places = []
                next_row = row if row <= bottom_key(column + 1) else bottom_key(column + 1)
                places.append(key_place(web_post_tl(), column + 1, next_row))
                places.append(key_place(web_post_tr(), column, row))
                places.append(key_place(web_post_bl(), column + 1, next_row))
                places.append(key_place(web_post_br(), column, row))
                hulls += _triangle_hulls(places)

        for column in range(ncols):
            torow = get_torow(column)
            # for row in range(nrows-1):
            # next_row = row + 1 if row + 1 < bottom_key(column) else bottom_key(column)
            for row in range(torow - 1):
                places = []
                places.append(key_place(web_post_bl(), column, row))
                places.append(key_place(web_post_br(), column, row))
                places.append(key_place(web_post_tl(), column, row + 1))
                places.append(key_place(web_post_tr(), column, row + 1))
                hulls += _triangle_hulls(places)

        for column in range(ncols - 1):
            torow = get_torow(column)
            # for row in range(nrows-1):  # need to consider last_row?
            for row in range(torow - 1):  # need to consider last_row?
                next_row = row if row < bottom_key(column + 1) else bottom_key(column + 1) - 1

                places = []
                places.append(key_place(web_post_br(), column, row))
                places.append(key_place(web_post_tr(), column, row + 1))
                places.append(key_place(web_post_bl(), column + 1, next_row))
                places.append(key_place(web_post_tl(), column + 1, next_row + 1))
                hulls += _triangle_hulls(places)

        return hulls

    def connectors():
        debugprint('connectors()')
        return union(_connectors())

    def detached_connectors(side='right'):
        return s.difference()(s.union()(key_holes(), connectors()), s.union()(*model_side(side)))

    ############
    ## Thumbs ##
    ############


    def adjustable_plate_size(Usize=1.5):
        return (Usize * sa_length - mount_height) / 2


    def adjustable_plate_half(Usize=1.5):
        debugprint('double_plate()')
        adjustable_plate_height = adjustable_plate_size(Usize)
        top_plate = box(mount_width, adjustable_plate_height, web_thickness)
        top_plate = translate(top_plate,
                              [0, (adjustable_plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
                              )
        return top_plate


    def adjustable_plate(Usize=1.5):
        debugprint('double_plate()')
        top_plate = adjustable_plate_half(Usize)
        return union((top_plate, mirror(top_plate, 'XZ')))


    def double_plate_half():
        debugprint('double_plate()')
        top_plate = box(mount_width, double_plate_height, web_thickness)
        top_plate = translate(top_plate,
                              [0, (double_plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
                              )
        return top_plate


    def double_plate():
        debugprint('double_plate()')
        top_plate = double_plate_half()
        return union((top_plate, mirror(top_plate, 'XZ')))


    ############################
    # MINI THUMB CLUSTER
    ############################


    ############################
    # MINIDOX (3-key) THUMB CLUSTER
    ############################


    ############################
    # Carbonfet THUMB CLUSTER
    ############################


    ############################
    # Wilder Trackball (Ball + 4-key) THUMB CLUSTER
    ############################


    ############################
    # CJ TRACKBALL THUMB CLUSTER
    ############################

    # single_plate = the switch shape


    ##########
    ## Case ##
    ##########

    def left_key_position(row, direction, low_corner=False, side='right'):
        debugprint("left_key_position()")
        pos = np.array(
            key_position([-mount_width * 0.5, direction * mount_height * 0.5, 0], 0, row)
        )
        if trackball_in_wall and (side == ball_side or ball_side == 'both'):

            if low_corner:
                y_offset = tbiw_left_wall_lower_y_offset
                z_offset = tbiw_left_wall_lower_z_offset
            else:
                y_offset = 0.0
                z_offset = 0.0

            return list(pos - np.array([
                tbiw_left_wall_x_offset_override,
                -y_offset,
                tbiw_left_wall_z_offset_override + z_offset
            ]))

        if low_corner:
            y_offset = left_wall_lower_y_offset
            z_offset = left_wall_lower_z_offset
        else:
            y_offset = 0.0
            z_offset = 0.0

        return list(pos - np.array([left_wall_x_row_offsets[row], -y_offset, left_wall_z_offset + z_offset]))


    def left_key_place(shape, row, direction, low_corner=False, side='right'):
        debugprint("left_key_place()")
        if row > bottom_key(0):
            row = bottom_key(0)
        pos = left_key_position(row, direction, low_corner=low_corner, side=side)
        return translate(shape, pos)

    # This is hackish... It just allows the search and replace of key_place in the cluster code
    # to not go big boom
    def left_cluster_key_place(shape, row, direction, low_corner=False, side='right'):
        if row > bottom_key(0):
            row = bottom_key(0)
        return left_key_place(shape, row, direction, low_corner, side)

    def wall_locate1(dx, dy):
        debugprint("wall_locate1()")
        return [dx * wall_thickness, dy * wall_thickness, -1]


    def wall_locate2(dx, dy):
        debugprint("wall_locate2()")
        return [dx * wall_x_offset, dy * wall_y_offset, -wall_z_offset]


    def wall_locate3(dx, dy, back=False):
        debugprint("wall_locate3()")
        if back:
            return [
                dx * (wall_x_offset + wall_base_x_thickness),
                dy * (wall_y_offset + wall_base_back_thickness),
                -wall_z_offset,
            ]
        else:
            return [
                dx * (wall_x_offset + wall_base_x_thickness),
                dy * (wall_y_offset + wall_base_y_thickness),
                -wall_z_offset,
            ]
        # return [
        #     dx * (wall_xy_offset + wall_thickness),
        #     dy * (wall_xy_offset + wall_thickness),
        #     -wall_z_offset,
        # ]


    def wall_brace(place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False):
        debugprint("wall_brace()")
        hulls = []

        hulls.append(place1(post1))
        hulls.append(place1(translate(post1, wall_locate1(dx1, dy1))))
        hulls.append(place1(translate(post1, wall_locate2(dx1, dy1))))
        hulls.append(place1(translate(post1, wall_locate3(dx1, dy1, back))))

        hulls.append(place2(post2))
        hulls.append(place2(translate(post2, wall_locate1(dx2, dy2))))
        hulls.append(place2(translate(post2, wall_locate1(dx2, dy2))))
        hulls.append(place2(translate(post2, wall_locate2(dx2, dy2))))
        hulls.append(place2(translate(post2, wall_locate3(dx2, dy2, back))))
        brace = hull_from_shapes(hulls)

        hulls = []
        hulls.append(place1(translate(post1, wall_locate2(dx1, dy1))))
        hulls.append(place1(translate(post1, wall_locate3(dx1, dy1, back))))
        hulls.append(place2(translate(post2, wall_locate2(dx2, dy2))))
        hulls.append(place2(translate(post2, wall_locate3(dx2, dy2, back))))
        vertical = bottom_hull(hulls)

        # return union([shape1, shape2])
        return vertical, brace


    def key_wall_brace(x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False):
        debugprint("key_wall_brace()")
        return wall_brace(
            (lambda shape: key_place(shape, x1, y1)),
            dx1,
            dy1,
            post1,
            (lambda shape: key_place(shape, x2, y2)),
            dx2,
            dy2,
            post2,
            back
        )


    def back_wall():
        print("back_wall()")
        x = 0
        shapes = list()
        shapes.append(key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True))
        shapes.append(key_wall_brace(x, 0, 0, 1, web_post_tr(), x+2, 0, 0, 1, web_post_tl(), back=True))
        shapes.append(key_wall_brace(x+2, 0, 0, 1, web_post_tl(), x+2, 0, 0, 1, web_post_tr(), back=True))
        for i in range(2, ncols - 1):
            x = i + 1
            shapes.append(key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True))
            shapes.append(key_wall_brace(
                x, 0, 0, 1, web_post_tl(), x - 1, 0, 0, 1, web_post_tr(), back=True
            ))
        shapes.append(key_wall_brace(
            lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr(), back=True
        ))

        # extra braces for index finger wall
        extra_braces = [
                triangle_hulls(
             [key_place(web_post_tl(), 1, 0),
            key_place(web_post_tr(), 0, 0),
             key_place(web_post_tr(), 1, 0),
             key_place(web_post_tl(), 2, 0)
             ])
                ]


        # union all shapes into vertical and brace
        vertical = union(list(map(lambda x: x[0], shapes)))
        braces = union(list(map(lambda x: x[1], shapes))+extra_braces)
        return vertical, braces


    def right_wall():
        print("right_wall()")

        torow = lastrow - 1
        if (full_last_rows or ncols < 5):
            torow = lastrow
        tocol = lastcol
        y = 0
        shapes = list()
        shapes.append( key_wall_brace(
                tocol, y, 1, 0, web_post_tr(), tocol, y, 1, 0, web_post_br()))

        for i in range(torow):
            y = i + 1
            shapes.append(key_wall_brace(
                tocol, y - 1, 1, 0, web_post_br(), tocol, y, 1, 0, web_post_tr()
            ))

            shapes.append(key_wall_brace(
                tocol, y, 1, 0, web_post_tr(), tocol, y, 1, 0, web_post_br()
            ))
            # STRANGE PARTIAL OFFSET

        # NOTE: uncomment this if using fron_wall instead of extended cluster walls
        # if ncols > 4:
        #     shapes.append(key_wall_brace(lastcol, torow, 0, -1, web_post_br(), lastcol, torow, 1, 0, web_post_br())
        #     )
        # union all shapes into vertical and brace
        vertical = union(list(map(lambda x: x[0], shapes)))
        braces = union(list(map(lambda x: x[1], shapes)))
        return vertical, braces


    def left_wall(side='right'):
        print('left_wall()')
        shapes = list() # list of (vertical, brace)
        shapes.append(wall_brace(
            (lambda sh: key_place(sh, 0, 0)), 0, 1, web_post_tl(),
            (lambda sh: left_key_place(sh, 0, 1, side=side)), 0, 1, web_post(),
        ))

        # shapes.append(wall_brace(
        #     (lambda sh: left_key_place(sh, 0, 1, side=side)), 0, 1, web_post(),
        #     (lambda sh: left_key_place(sh, 0, 1, side=side)), -1, 0, web_post(),
        # ))

        extra_braces = list()
        if full_last_rows:
            torow = lastrow +1
        else:
            torow = lastrow
        torow-=3
        for i in range(torow):
            y = i
            low = (y == (lastrow - 1))
            shapes.append(wall_brace(
                (lambda sh: left_key_place(sh, y, 1, side=side)), -1, 0, web_post(),
                (lambda sh: left_key_place(sh, y, -1, low_corner=low, side=side)), -1, 0, web_post(),
            ))
            extra_braces.append(hull_from_shapes((
                key_place(web_post_tl(), 0, y),
                key_place(web_post_bl(), 0, y),
                left_key_place(web_post(), y, 1, side=side),
                left_key_place(web_post(), y, -1, low_corner=low, side=side),
            )))
        # union all shapes into vertical and brace
        vertical = union(list(map(lambda x: x[0], shapes)))
        braces = union(list(map(lambda x: x[1], shapes))+extra_braces)
        return vertical, braces


    def front_wall():
        print('front_wall()')

        shapes = list()
        min_last_col = shift_column  # first_bottom_key()
        if min_last_col < 0:
            min_last_col = 0
        if min_last_col >= ncols - 1:
            min_last_col = ncols - 1

        if ncols >= min_last_col + 1:
            for i in range(ncols - (min_last_col + 1)):
                x = i + min_last_col + 1
                shapes.append(key_wall_brace(
                    x, bottom_key(x), 0, -1, web_post_bl(), x, bottom_key(x), 0, -1, web_post_br()
                ))

        if ncols >= min_last_col + 2:
            for i in range(ncols - (min_last_col + 2)):
                x = i + (min_last_col + 2)
                shapes.append(key_wall_brace(
                    x, bottom_key(x), 0, -1, web_post_bl(), x - 1, bottom_key(x - 1), 0, -1, web_post_br()
                ))
        vertical = union(list(map(lambda x: x[0], shapes)))
        braces = union(list(map(lambda x: x[1], shapes)))
        return vertical, braces


    def case_walls(side='right'):
        print('case_walls()')
        shapes = list()
        shapes.append(back_wall())
        shapes.append(left_wall(side=side))
        shapes.append(right_wall())
        # shapes.append(front_wall())

        shapes.append(cluster(side=side).walls(side=side))
        extra_braces = [cluster(side=side).connection(side=side)]
        # extra_braces = []

        vertical = union(list(map(lambda x: x[0], shapes)))
        braces = union(list(map(lambda x: x[1], shapes))+extra_braces)
        return vertical, braces


    rj9_start = list(
        np.array([0, -3, 0])
        + np.array(
            key_position(
                list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
                0,
                0,
            )
        )
    )

    rj9_position = (rj9_start[0], rj9_start[1], 11)


    def rj9_cube():
        debugprint('rj9_cube()')
        shape = box(14.78, 13, 22.38)

        return shape


    def rj9_space():
        debugprint('rj9_space()')
        return translate(rj9_cube(), rj9_position)


    def rj9_holder():
        print('rj9_holder()')
        shape = union([translate(box(10.78, 9, 18.38), (0, 2, 0)), translate(box(10.78, 13, 5), (0, 0, 5))])
        shape = difference(rj9_cube(), [shape])
        shape = translate(shape, rj9_position)

        return shape


    usb_holder_position = key_position(
        list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2), 0])), 1, 0
    )
    usb_holder_size = [6.5, 10.0, 13.6]
    usb_holder_thickness = 4


    def usb_holder():
        print('usb_holder()')
        shape = box(
            usb_holder_size[0] + usb_holder_thickness,
            usb_holder_size[1],
            usb_holder_size[2] + usb_holder_thickness,
        )
        shape = translate(shape,
                          (
                              usb_holder_position[0],
                              usb_holder_position[1],
                              (usb_holder_size[2] + usb_holder_thickness) / 2,
                          )
                          )
        return shape


    def usb_holder_hole():
        debugprint('usb_holder_hole()')
        shape = box(*usb_holder_size)
        shape = translate(shape,
                          (
                              usb_holder_position[0],
                              usb_holder_position[1],
                              (usb_holder_size[2] + usb_holder_thickness) / 2,
                          )
                          )
        return shape


    def trrs_mount_point():
        shape = box(6.2, 14, 5.2)
        jack = translate(rotate(cylinder(2.6, 5), (90, 0, 0)), (0, 9, 0))
        jack_entry = translate(rotate(cylinder(4, 5), (90, 0, 0)), (0, 11, 0))
        shape = rotate(translate(union([shape, jack, jack_entry]), (0, 0, 10)), (0, 0, 75))

        # shape = translate(shape,
        #               (
        #                   usb_holder_position[0] + trrs_hole_xoffset,
        #                   usb_holder_position[1] + trrs_hole_yoffset,
        #                   trrs_hole_zoffset,
        #               )
        #               )

        pos = screw_position(0, 0, 5, 5, 5) # wall_locate2(0, 1)
        # trans = wall_locate2(1, 1)
        # pos = [pos[0] + trans[0], pos[1] + trans[1], pos[2]]
        shape = translate(shape,
                      (
                          pos[0] + trrs_hole_xoffset,
                          pos[1] + trrs_hole_yoffset + screw_offsets[0][1],
                          trrs_hole_zoffset,
                      )
                      )
        return shape

    def usb_c_shape(width, height, depth):
        shape = box(width, depth, height)
        cyl1 = translate(rotate(cylinder(height / 2, depth), (90, 0, 0)), (width / 2, 0, 0))
        cyl2 = translate(rotate(cylinder(height / 2, depth), (90, 0, 0)), (-width / 2, 0, 0))
        return union([shape, cyl1, cyl2])

    def usb_c_hole():
        debugprint('usb_c_hole()')
        return usb_c_shape(usb_c_width, usb_c_height, 20)

    def usb_c_mount_point():
        width = usb_c_width * 1.2
        height = usb_c_height * 1.2
        front_bit = translate(usb_c_shape(usb_c_width + 2, usb_c_height + 2, wall_thickness / 2), (0, (wall_thickness / 2) + 1, 0))
        shape = union([front_bit, usb_c_hole()])
        shape = translate(shape,
                          (
                              usb_holder_position[0] + usb_c_xoffset,
                              usb_holder_position[1] + usb_c_yoffset,
                              usb_c_zoffset,
                          )
                          )
        return shape

    external_start = list(
        # np.array([0, -3, 0])
        np.array([external_holder_width / 2, 0, 0])
        + np.array(
            key_position(
                list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
                0,
                0,
            )
        )
    )

    def blackpill_mount_hole():
        print('blackpill_external_mount_hole()')
        shape = box(blackpill_holder_width, 20.0, external_holder_height + .1)
        undercut = box(blackpill_holder_width + 8, 10.0, external_holder_height + 8 + .1)
        shape = union([shape, translate(undercut, (0, -5, 0))])

        shape = translate(shape,
                          (
                              external_start[0] + blackpill_holder_xoffset,
                              external_start[1] + external_holder_yoffset,
                              external_holder_height / 2 - .05,
                          )
                          )
        return shape


    def external_mount_hole():
        print('external_mount_hole()')
        shape = box(external_holder_width, 40.0, external_holder_height + .1)
        # undercut = box( 10.0,external_holder_width + 8, external_holder_height + 8 + .1)
        # shape = union([shape, translate(undercut, (0, -5, 0))])

        shape = translate(
                rotate(shape, external_holder_rotation),
                          (
                              external_start[0] + external_holder_xoffset,
                              external_start[1] + external_holder_yoffset,
                              external_holder_height / 2 - .05 + external_holder_zoffset,
                          )
                          )
        return shape

    def compactyl_mount_hole():
        shape = import_file(path.join(parts_path, r"usb_holder_vertical_cutout"))
        compactyl_holder_height = 30.6
        compactyl_holder_width =  18
        # undercut = box( 10.0,external_holder_width + 8, external_holder_height + 8 + .1)
        # shape = union([shape, translate(undercut, (0, -5, 0))])
        shape = translate(
               rotate(shape, external_holder_rotation),
               [
                              external_start[0] + external_holder_xoffset,
                              external_start[1] + external_holder_yoffset,
                              compactyl_holder_height / 2 - .05,
                              ]
                       )
        return shape

    def usb_holder_w_reset():
        holder = import_file(path.join(parts_path, r"usb_holder_w_reset"))
        top_plate = s.translate([0, 0.5, 18])(s.cube([36, 1, 8], center=True))
        left_plate = s.translate([18, 0.5, 11])(s.cube([7, 1, 22], center=True))
        right_plate = s.translate([-18, 0.5, 11])(s.cube([7, 1, 22], center=True))
        back =  s.translate([0, -5, 0])
        holder = s.union()(holder, top_plate, left_plate, right_plate,
                           back(top_plate), back(left_plate), back(right_plate))
        holder = s.translate([-4, 22.5, -11])(holder)
        return holder

########### TRACKBALL GENERATION
    def use_btus(cluster):
        return trackball_in_wall or (cluster is not None and cluster.has_btus())


    def rexroth_bearing(cutter):
        tolerance_diameter = 0.25
        tolerance_depth = 1.5
        return translate(union([
                translate(cylinder(12.6/2+tolerance_diameter, 6.4+tolerance_depth), [0,0,-3.2]),
                cylinder(17/2+tolerance_diameter, 1.8+tolerance_depth),
                translate(sphere(4) if not cutter else translate(cylinder(17/2+tolerance_diameter, 4), [0,0,2]), [0,0,-0.1])
            ]), [0, 0, -0.9])

    def rexroth_bearing_cutter():
        return rexroth_bearing(True)

    def trackball_holder(cutter=False):
        cutter_tol = 0.75
        outer_shell_radius = 25
        if cutter:
            outer_shell_radius += cutter_tol
        trackball_radius = 17
        ball_spacing = 1.5
        distance_bearing_plate = 2.5
        sensor_holder_distance = 10
        sensor_plate_extra_distance = -0.25
        bearings_horizon_rotation = [10,10,10]
        bearing_zrotation_offset = 40
        sensor_rotations = ([70, 0, 0], [0, 0, -32],[0, 0, 0], )
        trackball_hole_radius = trackball_radius+ball_spacing
        holder_back_thickness = 2
        outer_shell = sphere(outer_shell_radius)
        trackball_hole = sphere(trackball_hole_radius)
        shell_cutter = translate(box(30,30,30), [0,0, 15])

        shell_cut_surface = [
                [60,20,20],
                [-40,40,20],
                [-50,0,10],
                [0,-30,-7.5],
                [20,-30,-7.5],
                ]
        if cutter:
            shell_cut_surface = [[point[0], point[1], point[2]+cutter_tol] for point in shell_cut_surface]
        shell_cutter = hull_from_shapes(
                    [translate(box(1,1,1), point) for point in shell_cut_surface] +
                    [translate(box(1,1,1), [point[0], point[1], point[2]+20]) for point in shell_cut_surface]
                                         )
        # shell_cutter = translate(box(100,100,100), [0,0, 50])
        cylinder_cutter = translate(cylinder(trackball_radius+1, 30), [0,0,15])
        sensor_hole = box(12,8,100)
        sensor_plate_distance = trackball_radius+sensor_plate_extra_distance

        bearings = union([
            rotate(translate(rotate(rexroth_bearing_cutter(), [0,90,0]), [-trackball_radius - distance_bearing_plate , 0, 0]), [0,-bearings_horizon_rotation[0],bearing_zrotation_offset+0]),
            rotate(rotate(translate(rotate( rexroth_bearing_cutter(), [0,90,0]), [-trackball_radius - distance_bearing_plate, 0, 0]), [0,-bearings_horizon_rotation[1],0]), [0, 0,bearing_zrotation_offset + 130]),
            rotate(rotate(translate(rotate( rexroth_bearing_cutter(), [0,90,0]), [-trackball_radius - distance_bearing_plate, 0, 0]), [0,-bearings_horizon_rotation[2],0]), [0, 0, bearing_zrotation_offset + 250])])

        sensor_plate = translate(translate(box(32, 21, 1), [0,0,-0.5]), [0,0, -sensor_plate_distance])
        sensor_section_sealing = translate(translate(cylinder(19, 1), [0,0,-0.5]), [0,0,-sensor_plate_distance])
        sensor_plate = union([sensor_section_sealing,sensor_plate])
        sensor_plate = difference(sensor_plate, [sensor_hole])
        sensor_cutter = translate(translate(box(32,32,12), [0,3, -6]), [0,0,-sensor_plate_distance])
        sensor_holder = union([
                translate(translate( box(32.5, 20, holder_back_thickness) , [0, 0, -holder_back_thickness/2]),[0,-2.5,-sensor_plate_distance-sensor_holder_distance]),
                translate( translate( box(2, 20, sensor_holder_distance) , [0.85, 0, sensor_holder_distance/2]), [-16.025, -2.5, -sensor_plate_distance-sensor_holder_distance]),
                translate( translate( box(2, 20, sensor_holder_distance) , [-0.85, 0, sensor_holder_distance/2]), [16.025, -2.5, -sensor_plate_distance-sensor_holder_distance]),
                sensor_plate,
                ])
        for rotation in sensor_rotations:
            sensor_cutter = rotate(sensor_cutter, rotation)
            sensor_holder = rotate(sensor_holder, rotation)
        sensor_holder = difference(sensor_holder, [bearings])

        # shape = union([outer_shell, trackball, box_cutter])
        shape = difference(union([outer_shell]), [trackball_hole, shell_cutter, cylinder_cutter, bearings, sensor_cutter])
        shape = difference(union([shape, sensor_holder]), [
            shell_cutter
                            ])
        # shape = union([shape, sensor_cutter])
        if cutter:
            # remove floor to avoid cutting baseplate
            shape = difference(shape, [translate(box(60,60,25), [0,0,-20])])
            shape = union([shape, sphere(trackball_radius+ball_spacing), bearings, difference(sensor_cutter, [shell_cutter])])
            if hull_trackball_cutter:
                shape = hull_from_shapes([shape])
        if show_trackball:
            shape = union([shape, sphere(trackball_radius), bearings])
        # shape = union([shape, bearings])
        shape = translate(shape, [0, 0, 22])
        return shape

    def trackball_socket(btus=False,segments=100, side="right"):
        # shape = sphere(ball_diameter / 2)
        # cyl = cylinder(ball_diameter / 2 + 4, 20)
        # cyl = translate(cyl, (0, 0, -8))
        # shape = union([shape, cyl])

        # tb_file = path.join(parts_path, r"trackball_socket_body_34mm")
        # tbcut_file = path.join(parts_path, r"trackball_socket_cutter_34mm")

        if btus:
            tb_file = path.join(parts_path, r"phat_btu_socket")
            tbcut_file = path.join(parts_path, r"phatter_btu_socket_cutter")
        else:
            tb_file = path.join(parts_path, r"trackball_socket_body_34mm")
            tbcut_file = path.join(parts_path, r"trackball_socket_cutter_34mm")

        if ENGINE == 'cadquery':
            sens_file = path.join(parts_path, r"gen_holder")
        else:
            sens_file = path.join(parts_path, r"trackball_sensor_mount")

        senscut_file = path.join(parts_path, r"trackball_sensor_cutter")

        # shape = import_file(tb_file)
        # # shape = difference(shape, [import_file(senscut_file)])
        # # shape = union([shape, import_file(sens_file)])
        # cutter = import_file(tbcut_file)

        # shape = import_file(tb_file)
        shape = trackball_holder()
        cutter = trackball_holder(cutter=True)
        sensor = import_file(sens_file)
        # shape = box(1,1,1)
        # sensor = box(1,1,1)
        if quickly:
            cutter = box(1,1,1)
        # cutter = sphere(ball_diameter/2)
        if not btus:
            cutter = union([cutter, import_file(senscut_file)])

        # return shape, cutter
        return shape, cutter, sensor


    def trackball_ball(segments=100, side="right"):
        shape = sphere(ball_diameter / 2)
        return shape

    def generate_trackball(pos, rot, cluster):
        tb_t_offset = tb_socket_translation_offset
        tb_r_offset = tb_socket_rotation_offset

        if use_btus(cluster):
            tb_t_offset = tb_btu_socket_translation_offset
            tb_r_offset = tb_btu_socket_rotation_offset

        shape, cutout, _ = trackball_socket(btus=use_btus(cluster))

        shape = rotate(shape, tb_r_offset)
        shape = translate(shape, tb_t_offset)
        shape = rotate(shape, rot)
        shape = translate(shape, pos)

        if cluster is not None and resin is False:
            shape = cluster.get_extras(shape, pos)

        cutout = rotate(cutout, tb_r_offset)
        cutout = translate(cutout, tb_t_offset)
        # cutout = rotate(cutout, tb_sensor_translation_offset)
        # cutout = translate(cutout, tb_sensor_rotation_offset)
        cutout = rotate(cutout, rot)
        cutout = translate(cutout, pos)


        # return precut, shape, cutout, ball
        return None, shape, cutout, None, None


    def generate_trackball_in_cluster(cluster):
        pos, rot = tbiw_position_rotation()
        if cluster.is_tb:
            pos, rot = cluster.position_rotation()
        return generate_trackball(pos, rot, cluster)


    def tbiw_position_rotation():
        base_pt1 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
            0, cornerrow - tbiw_ball_center_row - 1
        )
        base_pt2 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
            0, cornerrow - tbiw_ball_center_row + 1
        )
        base_pt0 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
            0, cornerrow - tbiw_ball_center_row
        )

        left_wall_x_offset = tbiw_left_wall_x_offset_override

        tbiw_mount_location_xyz = (
                (np.array(base_pt1) + np.array(base_pt2)) / 2.
                + np.array(((-left_wall_x_offset / 2), 0, 0))
                + np.array(tbiw_translational_offset)
        )

        # tbiw_mount_location_xyz[2] = (oled_translation_offset[2] + base_pt0[2])/2

        angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
        angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
        tbiw_mount_rotation_xyz = (rad2deg(angle_x), 0, rad2deg(angle_z)) + np.array(tbiw_rotation_offset)

        return tbiw_mount_location_xyz, tbiw_mount_rotation_xyz


    def generate_trackball_in_wall():
        pos, rot = tbiw_position_rotation()
        return generate_trackball(pos, rot, None)


    def oled_position_rotation(side='right'):
        _oled_center_row = None
        if trackball_in_wall and (side == ball_side or ball_side == 'both'):
            _oled_center_row = tbiw_oled_center_row
            _oled_translation_offset = tbiw_oled_translation_offset
            _oled_rotation_offset = tbiw_oled_rotation_offset

        elif oled_center_row is not None:
            _oled_center_row = oled_center_row
            _oled_translation_offset = oled_translation_offset
            _oled_rotation_offset = oled_rotation_offset

        if _oled_center_row is not None:
            base_pt1 = key_position(
                list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row - 1
            )
            base_pt2 = key_position(
                list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row + 1
            )
            base_pt0 = key_position(
                list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row
            )

            if oled_horizontal:
                _left_wall_x_offset = tbiw_left_wall_x_offset_override
            elif (trackball_in_wall or oled_horizontal) and (side == ball_side or ball_side == 'both'):
                _left_wall_x_offset = tbiw_left_wall_x_offset_override
            else:
                _left_wall_x_offset = left_wall_x_offset

            oled_mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-_left_wall_x_offset / 2), 0, 0)) + np.array(_oled_translation_offset)
            oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2]) / 2

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
            if oled_horizontal:
                oled_mount_rotation_xyz = (0, rad2deg(angle_x), -100) + np.array(_oled_rotation_offset)
            elif trackball_in_wall and (side == ball_side or ball_side == 'both'):
                # oled_mount_rotation_xyz = (0, rad2deg(angle_x), -rad2deg(angle_z)-90) + np.array(oled_rotation_offset)
                # oled_mount_rotation_xyz = (rad2deg(angle_x)*.707, rad2deg(angle_x)*.707, -45) + np.array(oled_rotation_offset)
                oled_mount_rotation_xyz = (0, rad2deg(angle_x), -100) + np.array(_oled_rotation_offset)
            else:
                oled_mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(_oled_rotation_offset)

        return oled_mount_location_xyz, oled_mount_rotation_xyz


    def oled_sliding_mount_frame(side='right'):
        mount_ext_width = oled_mount_width + 2 * oled_mount_rim
        mount_ext_height = (
                oled_mount_height + 2 * oled_edge_overlap_end
                + oled_edge_overlap_connector + oled_edge_overlap_clearance
                + 2 * oled_mount_rim
        )
        mount_ext_up_height = oled_mount_height + 2 * oled_mount_rim
        top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
        top_hole_length = oled_mount_height

        hole = box(mount_ext_width, mount_ext_up_height, oled_mount_cut_depth + .01)
        hole = translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

        hole_down = box(mount_ext_width, mount_ext_height, oled_mount_depth + oled_mount_cut_depth / 2)
        hole_down = translate(hole_down, (0., 0., -oled_mount_cut_depth / 4))
        hole = union([hole, hole_down])

        shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)

        conn_hole_start = -mount_ext_height / 2.0 + oled_mount_rim
        conn_hole_length = (
                oled_edge_overlap_end + oled_edge_overlap_connector
                + oled_edge_overlap_clearance + oled_thickness
        )
        conn_hole = box(oled_mount_width, conn_hole_length + .01, oled_mount_depth)
        conn_hole = translate(conn_hole, (
            0,
            conn_hole_start + conn_hole_length / 2,
            -oled_edge_overlap_thickness
        ))

        end_hole_length = (
                oled_edge_overlap_end + oled_edge_overlap_clearance
        )
        end_hole_start = mount_ext_height / 2.0 - oled_mount_rim - end_hole_length
        end_hole = box(oled_mount_width, end_hole_length + .01, oled_mount_depth)
        end_hole = translate(end_hole, (
            0,
            end_hole_start + end_hole_length / 2,
            -oled_edge_overlap_thickness
        ))

        top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
        top_hole_length = oled_mount_height
        top_hole = box(oled_mount_width, top_hole_length, oled_edge_overlap_thickness + oled_thickness - oled_edge_chamfer)
        top_hole = translate(top_hole, (
            0,
            top_hole_start + top_hole_length / 2,
            (oled_mount_depth - oled_edge_overlap_thickness - oled_thickness - oled_edge_chamfer) / 2.0
        ))

        top_chamfer_1 = box(
            oled_mount_width,
            top_hole_length,
            0.01
        )
        top_chamfer_2 = box(
            oled_mount_width + 2 * oled_edge_chamfer,
            top_hole_length + 2 * oled_edge_chamfer,
            0.01
        )
        top_chamfer_1 = translate(top_chamfer_1, (0, 0, -oled_edge_chamfer - .05))

        top_chamfer_1 = hull_from_shapes([top_chamfer_1, top_chamfer_2])

        top_chamfer_1 = translate(top_chamfer_1, (
            0,
            top_hole_start + top_hole_length / 2,
            oled_mount_depth / 2.0 + .05
        ))

        top_hole = union([top_hole, top_chamfer_1])

        shape = difference(shape, [conn_hole, top_hole, end_hole])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = rotate(shape, oled_mount_rotation_xyz)
        shape = translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = rotate(hole, oled_mount_rotation_xyz)
        hole = translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )
        return hole, shape


    def oled_clip_mount_frame(side='right'):
        mount_ext_width = oled_mount_width + 2 * oled_mount_rim
        mount_ext_height = (
                oled_mount_height + 2 * oled_clip_thickness
                + 2 * oled_clip_undercut + 2 * oled_clip_overhang + 2 * oled_mount_rim
        )
        hole = box(mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01)

        shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)
        shape = difference(shape, [box(oled_mount_width, oled_mount_height, oled_mount_depth + .1)])

        clip_slot = box(
            oled_clip_width + 2 * oled_clip_width_clearance,
            oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang,
            oled_mount_depth + .1
        )

        shape = difference(shape, [clip_slot])

        clip_undercut = box(
            oled_clip_width + 2 * oled_clip_width_clearance,
            oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang + 2 * oled_clip_undercut,
            oled_mount_depth + .1
        )

        clip_undercut = translate(clip_undercut, (0., 0., oled_clip_undercut_thickness))
        shape = difference(shape, [clip_undercut])

        plate = box(
            oled_mount_width + .1,
            oled_mount_height - 2 * oled_mount_connector_hole,
            oled_mount_depth - oled_thickness
        )
        plate = translate(plate, (0., 0., -oled_thickness / 2.0))
        shape = union([shape, plate])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = rotate(shape, oled_mount_rotation_xyz)
        shape = translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = rotate(hole, oled_mount_rotation_xyz)
        hole = translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )

        return hole, shape


    def oled_clip():
        mount_ext_width = oled_mount_width + 2 * oled_mount_rim
        mount_ext_height = (
                oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang
                + 2 * oled_clip_undercut + 2 * oled_mount_rim
        )

        oled_leg_depth = oled_mount_depth + oled_clip_z_gap

        shape = box(mount_ext_width - .1, mount_ext_height - .1, oled_mount_bezel_thickness)
        shape = translate(shape, (0., 0., oled_mount_bezel_thickness / 2.))

        hole_1 = box(
            oled_screen_width + 2 * oled_mount_bezel_chamfer,
            oled_screen_length + 2 * oled_mount_bezel_chamfer,
            .01
        )
        hole_2 = box(oled_screen_width, oled_screen_length, 2.05 * oled_mount_bezel_thickness)
        hole = hull_from_shapes([hole_1, hole_2])

        shape = difference(shape, [translate(hole, (0., 0., oled_mount_bezel_thickness))])

        clip_leg = box(oled_clip_width, oled_clip_thickness, oled_leg_depth)
        clip_leg = translate(clip_leg, (
            0.,
            0.,
            # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
            -oled_leg_depth / 2.
        ))

        latch_1 = box(
            oled_clip_width,
            oled_clip_overhang + oled_clip_thickness,
            .01
        )
        latch_2 = box(
            oled_clip_width,
            oled_clip_thickness / 2,
            oled_clip_extension
        )
        latch_2 = translate(latch_2, (
            0.,
            -(-oled_clip_thickness / 2 + oled_clip_thickness + oled_clip_overhang) / 2,
            -oled_clip_extension / 2
        ))
        latch = hull_from_shapes([latch_1, latch_2])
        latch = translate(latch, (
            0.,
            oled_clip_overhang / 2,
            -oled_leg_depth
        ))

        clip_leg = union([clip_leg, latch])

        clip_leg = translate(clip_leg, (
            0.,
            (oled_mount_height + 2 * oled_clip_overhang + oled_clip_thickness) / 2 - oled_clip_y_gap,
            0.
        ))

        shape = union([shape, clip_leg, mirror(clip_leg, 'XZ')])

        return shape


    def oled_undercut_mount_frame(side='right'):
        mount_ext_width = oled_mount_width + 2 * oled_mount_rim
        mount_ext_height = oled_mount_height + 2 * oled_mount_rim
        hole = box(mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01)

        shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)
        shape = difference(shape, [box(oled_mount_width, oled_mount_height, oled_mount_depth + .1)])
        undercut = box(
            oled_mount_width + 2 * oled_mount_undercut,
            oled_mount_height + 2 * oled_mount_undercut,
            oled_mount_depth)
        undercut = translate(undercut, (0., 0., -oled_mount_undercut_thickness))
        shape = difference(shape, [undercut])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = rotate(shape, oled_mount_rotation_xyz)
        shape = translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                          )

        hole = rotate(hole, oled_mount_rotation_xyz)
        hole = translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                         )

        return hole, shape


    def teensy_holder():
        print('teensy_holder()')
        teensy_top_xy = key_position(wall_locate3(-1, 0), 0, centerrow - 1)
        teensy_bot_xy = key_position(wall_locate3(-1, 0), 0, centerrow + 1)
        teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
        teensy_holder_offset = -teensy_holder_length / 2
        teensy_holder_top_offset = (teensy_holder_top_length / 2) - teensy_holder_length

        s1 = box(3, teensy_holder_length, 6 + teensy_width)
        s1 = translate(s1, [1.5, teensy_holder_offset, 0])

        s2 = box(teensy_pcb_thickness, teensy_holder_length, 3)
        s2 = translate(s2,
                       (
                           (teensy_pcb_thickness / 2) + 3,
                           teensy_holder_offset,
                           -1.5 - (teensy_width / 2),
                       )
                       )

        s3 = box(teensy_pcb_thickness, teensy_holder_top_length, 3)
        s3 = translate(s3,
                       [
                           (teensy_pcb_thickness / 2) + 3,
                           teensy_holder_top_offset,
                           1.5 + (teensy_width / 2),
                       ]
                       )

        s4 = box(4, teensy_holder_top_length, 4)
        s4 = translate(s4,
                       [teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (teensy_width / 2)]
                       )

        shape = union((s1, s2, s3, s4))

        shape = translate(shape, [-teensy_holder_width, 0, 0])
        shape = translate(shape, [-1.4, 0, 0])
        shape = translate(shape,
                          [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + teensy_width) / 2]
                          )

        return shape


    def screw_insert_shape(bottom_radius, top_radius, height, hole=False):
        debugprint('screw_insert_shape()')
        mag_offset = 0
        if bottom_radius == top_radius:
            shape = translate(cylinder(radius=bottom_radius, height=height),
                             (0, 0, mag_offset - (height / 2))  # offset magnet by 1 mm in case
                             )
        else:
            shape = translate(cone(r1=bottom_radius, r2=top_radius, height=height), (0, 0, -height / 2))

        if magnet_bottom:
            if not hole:
                shape = union((
                    shape,
                    translate(sphere(top_radius), (0, 0, mag_offset / 2)),
                ))
        else:
            shape = union((
                shape,
                translate(sphere(top_radius), (0, 0,  (height / 2))),
            ))
        return shape

    def place_screw(shape, column, row, side='right'):
        debugprint('screw_insert()')
        position = screw_position(column, row, side)
        shape = translate(shape, [position[0], position[1], 0])

        return shape

    def screw_position(column, row, side='right'):
        debugprint('screw_position()')
        shift_right = column == lastcol
        shift_left = column == 0
        shift_up = (not (shift_right or shift_left)) and (row == 0)
        shift_down = (not (shift_right or shift_left)) and (row >= lastrow)

        if screws_offset == 'INSIDE':
            # debugprint('Shift Inside')
            shift_left_adjust = wall_base_x_thickness
            shift_right_adjust = -wall_base_x_thickness / 3
            shift_down_adjust = -wall_base_y_thickness / 2
            shift_up_adjust = -wall_base_y_thickness / 3

        elif screws_offset == 'OUTSIDE':
            debugprint('Shift Outside')
            shift_left_adjust = 0
            shift_right_adjust = wall_base_x_thickness / 2
            shift_down_adjust = wall_base_y_thickness * 2 / 3
            shift_up_adjust = wall_base_y_thickness * 2 / 3

        else:
            # debugprint('Shift Origin')
            shift_left_adjust = 0
            shift_right_adjust = 0
            shift_down_adjust = 0
            shift_up_adjust = 0

        if shift_up:
            position = key_position(
                list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2) + shift_up_adjust, 0])),
                column,
                row,
            )
        elif shift_down:
            position = key_position(
                list(np.array(wall_locate2(0, -1)) - np.array([0, (mount_height / 2) + shift_down_adjust, 0])),
                column,
                row,
            )
        elif shift_left:
            position = list(
                np.array(left_key_position(row, 0, side=side)) + np.array(wall_locate3(-1, 0)) + np.array(
                    (shift_left_adjust, 0, 0))
            )
        else:
            position = key_position(
                list(np.array(wall_locate2(1, 0)) + np.array([(mount_height / 2), 0, 0]) + np.array(
                    (shift_right_adjust, 0, 0))
                     ),
                column,
                row,
            )

        return position

    def screw_insert_thumb(shape, side='right'):
        position = cluster(side).screw_positions()
        shape = translate(shape, [position[0], position[1], 0])
        return shape


    def place_screw_all(screw, side='right'):
        print('screw_insert_all_shapes()')
        so = screw_offsets
        shape = [
            translate(place_screw(screw, 0, 0,side=side), (so[0][0] - 8 if side == 'right' else so[0][0] , so[0][1], so[0][2] )),  # rear left
            translate(place_screw(screw, 0, lastrow - 1,side=side),
                      (so[1][0], so[1][1] + left_wall_lower_y_offset, so[1][2] )),  # front left
            translate(place_screw(screw, 3, 0,side=side), (so[3][0], so[3][1], so[3][2] )),  # rear middle
            translate(place_screw(screw, lastcol, 0,side=side),
                      (so[4][0], so[4][1], so[4][2] )),  # rear right
            translate(place_screw(screw, lastcol, lastrow - 1,side=side),
                      (so[5][0], so[5][1], so[5][2] )),  # front right
            translate(screw_insert_thumb(screw, side=side), (so[6][0], so[6][1], so[6][2] )),  # thumb cluster
        ]
        if side=='right':
            shape.append(translate(screw_insert_thumb(screw, side=side), (so[7][0], so[7][1], so[7][2] ))) # extra screw on right side
        else:
            shape.append(translate(place_screw(screw, 3, lastrow,side=side), (so[2][0], so[2][1], so[2][2] )),  )# front middle

        return tuple(shape)


    def screw_insert_holes(side='right'):
        height = screw_insert_height + .02
        screw = translate(screw_insert_shape(screw_insert_bottom_radius, screw_insert_top_radius, height, hole=True), [0,0,height / 2-0.01])
        return place_screw_all(screw, side=side)


    def screw_insert_outers(side='right'):
        height = screw_insert_height + 1.5
        screw = translate(screw_insert_shape(screw_insert_bottom_radius + 1.6, screw_insert_top_radius + 1.6, height), [0,0,height / 2])
        return place_screw_all( screw , side=side)


    def baseplate_holes(side='right'):
        # ugh
        hide_screw = translate(cone(3.25, 1.7, 2.05), [0,0,-2.05/2-base_thickness/2])
        holes = place_screw_all(hide_screw, side=side)
        return holes


    def wire_post(direction, offset):
        debugprint('wire_post()')
        s1 = box(
            wire_post_diameter, wire_post_diameter, wire_post_height
        )
        s1 = translate(s1, [0, -wire_post_diameter * 0.5 * direction, 0])

        s2 = box(
            wire_post_diameter, wire_post_overhang, wire_post_diameter
        )
        s2 = translate(s2,
                       [0, -wire_post_overhang * 0.5 * direction, -wire_post_height / 2]
                       )

        shape = union((s1, s2))
        shape = translate(shape, [0, -offset, (-wire_post_height / 2) + 3])
        shape = rotate(shape, [-alpha / 2, 0, 0])
        shape = translate(shape, (3, -mount_height / 2, 0))

        return shape

    def model_side(side="right"):
        print('model_side()' + side)
        shape = union([key_holes(side=side)])
        if debug_exports:
            export_file(shape=shape, fname=path.join(r".", "things", f"debug_key_plates_{side}"))
        connector_shape = connectors()
        shape = union([shape, connector_shape])
        if debug_exports:
            export_file(shape=shape, fname=path.join(r".", "things", f"debug_connector_shape_{side}"))
        thumb_shape = union([shape, cluster(side).thumb(side=side)])
        # thumb_shape = union([cluster(side).thumb(side=side)])
        if debug_exports:
            export_file(shape=thumb_shape, fname=path.join(r".", "things", f"debug_thumb_shape_{side}"))
        shape = union([thumb_shape])
        thumb_connector_shape = cluster(side).thumb_connectors(side=side)
        shape = union([shape, thumb_connector_shape])
        if debug_exports:
            export_file(shape=shape, fname=path.join(r".", "things", f"debug_thumb_connector_shape_{side}"))
        walls_vertical, walls_brace = case_walls(side=side)
        if debug_exports:
            export_file(shape=walls_vertical, fname=path.join(r".", "things", f"debug_walls_shape_{side}"))

        if independent_walls:
            s2 = union([walls_vertical])
        else:
            s2 = union([walls_vertical, walls_brace])
        s2 = union([s2, *screw_insert_outers(side=side)])
        if trrs_hole:
            s2 = difference(s2, [trrs_mount_point()])
        if controller_side == "both" or side == controller_side:
            if controller_mount_type in ['RJ9_USB_TEENSY', 'USB_TEENSY']:
                s2 = union([s2, teensy_holder()])
            if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL', 'USB_WALL', 'USB_TEENSY']:
                s2 = union([s2, usb_holder()])
                s2 = difference(s2, [usb_holder_hole()])
            if controller_mount_type in ['USB_C_WALL']:
                s2 = difference(s2, [usb_c_mount_point()])
            if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
                s2 = difference(s2, [rj9_space()])
            if controller_mount_type in ['BLACKPILL_EXTERNAL']:
                s2 = difference(s2, [blackpill_mount_hole()])
            if controller_mount_type in ['EXTERNAL']:
                s2 = difference(s2, [external_mount_hole()])
                # s2 = union([s2, external_mount_hole()])
                if show_external_holder:
                    holder = usb_holder_w_reset()
                    # holder = union([holder, box(18,36,22), ]) # dupont clearance
                    holder = translate(
                            translate(rotate(holder,
                                             [external_holder_rotation[0], -external_holder_rotation[1], external_holder_rotation[2]]),
                                      [6, -22, 11]), [external_start[0] + external_holder_xoffset, external_start[1] + external_holder_yoffset, external_holder_zoffset]
                            # translate(rotate(holder, [0,0,0]), [0, 0, 0]), [external_start[0] + external_holder_xoffset, external_start[1] + external_holder_yoffset, 0]
                            )
                    s2 = union([s2, holder])

            if controller_mount_type in ['COMPACTYL']:
                s2 = difference(s2, [compactyl_mount_hole()])
            if controller_mount_type in ['COMPACTYL_VERTICAL']:
                s2 = difference(s2, [compactyl_vertical_mount_hole()])
                # s2 = union([s2, compactyl_vertical_mount_hole()])
            if controller_mount_type in ['None']:
                0  # do nothing, only here to expressly state inaction.

        s2 = difference(s2, [union(screw_insert_holes(side=side))])
        if independent_walls:
            shape = union([shape, walls_brace])
        else:
            shape = union([shape, s2])

        if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
            shape = union([shape, rj9_holder()])

        if oled_mount_type == "UNDERCUT":
            hole, frame = oled_undercut_mount_frame(side=side)
            shape = difference(shape, [hole])
            shape = union([shape, frame])

        elif oled_mount_type == "SLIDING":
            hole, frame = oled_sliding_mount_frame(side=side)
            shape = difference(shape, [hole])
            shape = union([shape, frame])

        elif oled_mount_type == "CLIP":
            hole, frame = oled_clip_mount_frame(side=side)
            shape = difference(shape, [hole])
            shape = union([shape, frame])

        if trackball_in_wall and (side == ball_side or ball_side == 'both'):
            tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_wall()

            shape = difference(shape, [tbprecut])
            # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
            shape = union([shape, tb])
            # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
            shape = difference(shape, [tbcutout])
            # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
            # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
            shape = union([shape, sensor])

            if show_caps:
                shape = add([shape, ball])

        elif cluster(side).is_tb:
            _, tb, tbcutout, sensor, _ = generate_trackball_in_cluster(cluster(side))

            if cluster(side).has_btus():
                if hull_trackball_cutter:
                    shape = union([shape, tbcutout])
                else:
                    shape = difference(shape, [tbcutout])
                if show_trackball:
                    shape = union([shape, tb])
                # shape = union([shape, tb])
                # shape = union([shape, sensor])
            else:
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
                shape = union([shape, tb])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
                shape = difference(shape, [tbcutout])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
                # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
                shape = union([shape, sensor])

            # if show_caps:
            #     shape = add([shape, ball])

        floor = translate(box(400, 400, 40), (0, 0, -20))
        shape = difference(shape, [floor])
        if independent_walls:
            s2 = difference(s2, [floor, walls_brace]) # remove floor and the actual model
            export_file(shape=s2, fname=path.join(".", path.join(save_path, config_name + f"_walls_{side}")))

        # shape = difference(shape, [pcbs(), cluster(side).pcbs()])
        if show_caps:
            shape = add([shape, cluster(side).thumbcaps(side=side)])
            shape = add([shape, caps()])

        if side == "left":
            shape = mirror(shape, 'YZ')

        return shape, walls_vertical

    def backplate(side):
        export_file(shape=key_pcb(), fname="things/pcb")
        # bottom_hull = union
        print('backplate()' + side)
        key_columns = list(map(lambda shape: bottom_hull([shape]), _place_shape_on_keyplace(key_pcb_column_top())))
        # manually prevent bottom hulls from overlapping
        # key_columns[3] = difference(key_columns[3], [translate(key_columns[6], [0,0,20])])
        # key_columns[4] = difference(key_columns[4], [translate(key_columns[7], [0,0,20])])
        # key_columns[5] = difference(key_columns[5], [translate(key_columns[8], [0,0,20])])
        # key_columns[8] = difference(key_columns[8], [translate(key_columns[11], [0,0,20])])
        key_columns = union(key_columns+_place_shape_on_keyplace(key_pcb_holder()))
        # connector_columns = union(map(lambda shape: bottom_hull([shape]), _connectors()))
        # connector_columns = difference(connector_columns, [translate(key_columns, [0,0,20])])
        # main_block =union([key_columns, connector_columns])
        main_block = key_columns
        thumb_shapes = (cluster(side)._thumb_1x_layout(hull_from_shapes([single_plate(side=side)]))
                    + cluster(side)._thumb_connectors(side=side))
        thumb_block = union(map(lambda shape: bottom_hull([shape]), thumb_shapes))

        global web_thickness
        global post_size
        _web_thickness = web_thickness
        _post_size = post_size
        web_thickness += 1
        post_size += 1
        shape = union([main_block, thumb_block])
        shape = difference(shape, [
            pcbs(),
            key_holes_filled(),
            connectors(),
            cluster(side).thumb_connectors(), cluster(side).pcbs(side=side),
            cluster(side).thumb_1x_layout(hull_from_shapes([single_plate(side=side)])),
            *list(map(lambda screw_insert: bottom_hull([translate(screw_insert, [0,0,100])]), screw_insert_outers(side=side)))
            ] )
        web_thickness = _web_thickness
        post_size = _post_size
        floor = translate(box(400, 400, 40), (0, 0, -20))
        shape = difference(shape, [floor, *case_walls(side=side)])
        if side == "left":
            shape = mirror(shape, 'YZ')
        return shape

    def wrist_rest(model, base, side="right"):
        body = wrist.wrist_rest(side)
        body = s.rotate([90,0,0])(body)
        body = s.rotate([0,0,95])(body)
        body = s.translate([-35,-150,-base_thickness])(body)
        if side == "left":
            body = mirror(body, "YZ")
        body = s.difference()(body, model, base)
        return body

    def baseplate(shape, wedge_angle=None, side='right'):
        shape = union([
            *case_walls(side=side),
            *screw_insert_outers(side=side)
        ])

        tool = union(baseplate_holes(side=side))
        rubber_feet_hole_depth = 1.64
        rubber_feet_radius = 4.25
        rubber_feet_hole = translate(cylinder(rubber_feet_radius, rubber_feet_hole_depth),
                                     [0,0, -base_thickness+rubber_feet_hole_depth/2-0.01])
        rubber_feet = [
                    translate(rubber_feet_hole, [-47, 19, 0]),
                    translate(rubber_feet_hole, [-70, -64, 0]),
                    translate(rubber_feet_hole, [-99, -19, 0]) if side=='right' else translate(rubber_feet_hole, [-60, -19, 0]),
                    translate(rubber_feet_hole, [42, -65, 0]),
                    translate(rubber_feet_hole, [51, -7, 0]),
                    translate(rubber_feet_hole, [2, 27, 0]),
                ]
        base = box(1000, 1000, .01)
        # shape = shape - tool
        shape = intersect(shape, base)

        shape = translate(shape, [0, 0, -0.001])
        # global web_thickness
        # global post_size
        # _web_thickness = web_thickness
        # _post_size = post_size
        # web_thickness += 1.
        # post_size += 1.
        base = difference(translate(sl.linear_extrude(height=base_thickness)( sl.projection(cut=True)(shape).fill()),
                            [0,0, -base_thickness]), [
                                surface_pcbs(),
                                tool,
                                rubber_feet,
                                # cluster(side).thumb_connectors(), cluster(side).pcbs(side=side),
                                # connectors()
                                ])
        # web_thickness = _web_thickness
        # post_size = _post_size
        # base = union([base, backplate(side=side)])
        if cluster(side).is_tb:
            _, tb, tbcutout, _, _ = generate_trackball_in_cluster(cluster(side))
            base = difference(base, [tbcutout])
            # NOTE: you need to compute the caches commenting the following three lines, then ucomment and compute
            # the whole thing
            floor = translate(rotate(box(52,52,50), [0,0,22]), [-67,-17,-25-base_thickness])
            tb = difference(tb, [floor])
            base = union([base, tb])
        return base


    def round_cube(x, y, z, radius, _fn):
        x_ = x - 2*radius
        y_ = y - 2*radius
        z_ = z - 2*radius
        spheres = s.translate([x_/2, y_/2, z_/2])(s.sphere(radius, _fn=_fn))
        spheres = s.union()(s.mirrorZ()(spheres), spheres)
        spheres = s.union()(s.mirrorY()(spheres), spheres)
        spheres = s.union()(s.mirrorX()(spheres), spheres)
        return s.hull()(spheres)

    def cylinder_band(x, y, band_width, band_depth, radius, _fn):
        x -= 2*radius
        y -= 2*radius
        outer = s.back(y/2)(s.left(x/2)(s.down(band_width/2)(s.cylinder(h=band_width, r=radius, _fn=_fn))))
        outer = s.union()(s.mirrorY()(outer), outer)
        outer = s.union()(s.mirrorX()(outer), outer)
        outer = s.hull()(outer)
        inner = s.back(y/2-band_depth/2)(s.left(x/2-band_depth/2)(s.down(band_width/2+0.05)(s.cylinder(h=band_width+0.1, r=radius, _fn=_fn))))
        inner = s.union()(s.mirrorY()(inner), inner)
        inner = s.union()(s.mirrorX()(inner), inner)
        inner = s.hull()(inner)
        return s.difference()(outer, inner)

    def _make_case(x_width, y_width, z_top, z_bottom, band_width, band_depth, radius, _fn, side, wire_box):
        global show_caps, base_thickness, hull_trackball_cutter, show_external_holder, external_holder_yoffset
        global wall_thickness, wall_base_x_thickness, wall_base_y_thickness, wall_base_back_thickness
        _show_caps = show_caps
        _base_thickness = base_thickness
        _hull_trackball_cutter = hull_trackball_cutter
        _show_external_holder = show_external_holder
        _external_holder_yoffset = external_holder_yoffset
        _wall_thickness = wall_thickness
        _wall_base_x_thickness = wall_base_x_thickness
        _wall_base_y_thickness = wall_base_y_thickness
        _wall_base_back_thickness = wall_base_back_thickness
        show_caps = True
        if side == "right":
            hull_trackball_cutter = True
        show_external_holder = True
        _external_holder_yoffset = external_holder_yoffset
        external_holder_yoffset +=0.5
        base_thickness+=1
        wall_thickness+=1
        wall_base_x_thickness+=1
        wall_base_y_thickness+=1
        wall_base_back_thickness+=1
        keyboard, walls = model_side(side)
        if side == "left":
            base = mirror(baseplate(walls, side=side), 'YZ')
        else:
            base = baseplate(walls, side=side)
        # keyboard = s.union()(keyboard, base)
        # keyboard_hole = s.left(32.5)(s.forward(22.5)(
        #     s.hull()(keyboard)))
        if side=="left":
            centering = lambda x: s.left(32.5)(s.forward(22.5)(x))
        else:
            centering = lambda x: s.right(27.5)(s.forward(22.5)(x))
        base_hole = centering(s.hull()(base))
        keyboard_hole = centering(s.hull()(keyboard))
        keyboard_hole = s.union()(keyboard_hole, base_hole)

        if wire_box:
            keyboard_hole = s.union()(
                    keyboard_hole,
                    s.up(20)(s.right(68)(s.forward(12.5)((s.rotate([0,0,20])(round_cube(50, 90, 45, 15, _fn)))))))
        show_caps = _show_caps
        base_thickness = _base_thickness
        show_external_holder = _show_external_holder
        hull_trackball_cutter = _hull_trackball_cutter
        external_holder_yoffset = _external_holder_yoffset
        wall_thickness = _wall_thickness
        wall_base_x_thickness = _wall_base_x_thickness
        wall_base_y_thickness = _wall_base_y_thickness
        wall_base_back_thickness = _wall_base_back_thickness


        # Bottom
        case_bottom = s.up(z_top/2)(s.difference()(
                s.down(z_bottom/2)(round_cube(x_width, y_width, z_bottom+z_top, radius, _fn)),
                s.cube(x_width*2, y_width*2, z_top, center=True)
                ))
        case_bottom = s.difference()(case_bottom, keyboard_hole)

        # Top
        case_top = s.down(z_bottom/2)(s.difference()(
            s.up(z_top/2)(round_cube(x_width, y_width, z_top+z_bottom, radius, _fn)),
            s.cube(x_width*2, y_width*2, z_bottom, center=True)
            ))
        case_top = s.difference()(case_top, keyboard_hole)

        # Bands
        band_xz = s.up((z_top+z_bottom)/2-z_bottom)(s.rotate([90,0,0])(cylinder_band(x_width+0.01, (z_top+z_bottom)+0.01, band_width, band_depth, radius, _fn)))
        band_xy = s.up((z_top+z_bottom)/2-z_bottom)(cylinder_band(x_width+0.01, y_width+0.01, band_width, band_depth, radius, _fn))
        band_yz = s.up((z_top+z_bottom)/2-z_bottom)(s.rotate([0,90,0])(cylinder_band((z_top+z_bottom)+0.01, y_width+0.01, band_width, band_depth, radius, _fn)))
        case_top = s.difference()(case_top, band_xz, band_xy, band_yz)
        case_bottom = s.difference()(case_bottom, band_xz, band_xy, band_yz)

        # Centering columns
        columns_radius = 7
        cylinder_hole = s.down(0.01)(s.cylinder(h=10, r=columns_radius+0.25, _fn=_fn))
        cylinder = s.cylinder(h=5, r=columns_radius-0.5, _fn=_fn)

        if side == "left":
            cyl_place = lambda cylinder: s.union()(
                    s.right(87)(s.back(50)(cylinder)),
                    s.right(87)(s.forward(50)(cylinder)),
                    s.left(87)(s.forward(50)(cylinder))
                    )
        else:
            cyl_place = lambda cylinder: s.union()(
                    s.left(80)(s.back(50)(cylinder)),
                    s.right(80)(s.forward(50)(cylinder)),
                    s.left(80)(s.forward(50)(cylinder))
                    )

        feet = s.union()(
                s.down(z_bottom-0.01)(s.right(80)(s.back(50)(s.cylinder(h=2, d=11, _fn=_fn)))),
                s.down(z_bottom-0.01)(s.left(80)(s.back(50)(s.cylinder(h=2, d=11, _fn=_fn)))),
                s.down(z_bottom-0.01)(s.left(80)(s.forward(50)(s.cylinder(h=2, d=11, _fn=_fn)))),
                s.down(z_bottom-0.01)(s.right(80)(s.forward(50)(s.cylinder(h=2, d=11, _fn=_fn))))
                )

        case_top = s.difference()(case_top, cyl_place(cylinder_hole))
        case_bottom = s.union()(case_bottom, cyl_place(cylinder))
        case_bottom = s.difference()(case_bottom, feet)
        # return keyboard, keyboard_hole
        return case_top, case_bottom

    def make_case_left():
        _fn = 100
        radius = 15
        x_width = 215
        y_width = 140
        z_top = 47.5
        z_bottom = 6
        band_depth = 4
        band_width = 20.5
        case_top, case_bottom = _make_case(x_width, y_width, z_top, z_bottom, band_width, band_depth, radius, _fn, "left", True)
        return case_top, case_bottom


    def make_case_right():
        _fn = 100
        radius = 15
        x_width = 205
        y_width = 140
        z_top = 47.5
        z_bottom = 6
        band_depth = 4
        band_width = 20.5
        case_top, case_bottom = _make_case(x_width, y_width, z_top, z_bottom, band_width, band_depth, radius, _fn, "right", False)
        return case_top, case_bottom


    def run():

        mod_l, walls_l = model_side(side="left")
        export_file(shape=mod_l, fname=path.join(save_path, config_name + r"_left"))
        base_l = mirror(baseplate(walls_l, side='left'), 'YZ')
        export_file(shape=base_l, fname=path.join(save_path, config_name + r"_left_plate"))

        export_file(shape=trackball_holder(), fname=path.join(save_path, "trackball_holder"))
        export_file(shape=trackball_holder(True), fname=path.join(save_path, "trackball_holder_cutter"))
        export_file(shape=single_plate(), fname=path.join(save_path, "single_plate"))
        export_file(shape=usb_holder_w_reset(), fname=path.join(save_path, "usb_holder_w_reset_plated"))
        mod_r, walls_r = model_side(side="right")
        export_file(shape=mod_r, fname=path.join(save_path, config_name + r"_right"))
        # conn = detached_connectors()
        # export_file(shape=conn, fname=path.join(save_path, config_name + r"conn_right"))
        # pcb_backplate = backplate(side="right")
        # export_file(shape=pcb_backplate, fname=path.join(save_path, config_name + r"backplate_right"))

        if right_side_only:
            print(">>>>>  RIGHT SIDE ONLY: Only rendering a the right side.")
            return
        base = baseplate(walls_r, side='right')
        export_file(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))
        rest = wrist_rest(mod_r, base, side="right")
        export_file(shape=rest, fname=path.join(save_path, config_name + r"_right_wrist_rest"))
        # if quickly:
        #     print(">>>>>  QUICK RENDER: Only rendering a the right side and bottom plate.")
        #     return
        # export_dxf(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))

        case_top_r, case_bottom_r = make_case_right()
        export_file(shape=case_top_r, fname=path.join(save_path, config_name + r"_case_top_right"))
        export_file(shape=case_bottom_r, fname=path.join(save_path, config_name + r"_case_bottom_right"))
        case_top_l, case_bottom_l = make_case_left()
        export_file(shape=case_top_l, fname=path.join(save_path, config_name + r"_case_top_left"))
        export_file(shape=case_bottom_l, fname=path.join(save_path, config_name + r"_case_bottom_left"))

        # if symmetry == "asymmetric":
        first_column_test = difference(mod_l, [
            translate(
                rotate(box(150, 300, 200), [0, -15, 5]), [40,-25,40])
            ])
        export_file(shape=first_column_test, fname=path.join(save_path, config_name + r"first_column_test"))

        # export_dxf(shape=base_l, fname=path.join(save_path, config_name + r"_left_plate"))
        rest = wrist_rest(mod_l, base_l, side="left")
        export_file(shape=rest, fname=path.join(save_path, config_name + r"_left_wrist_rest"))

        # else:
        #     export_file(shape=mirror(mod_r, 'YZ'), fname=path.join(save_path, config_name + r"_left"))
        #
        #     lbase = mirror(base, 'YZ')
        #     export_file(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))
        #     export_dxf(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))

        if ENGINE == 'cadquery':
            import freecad_that as freecad
            freecad.generate_freecad_script(path.abspath(save_path), [
                config_name + r"_right",
                config_name + r"_left",
                config_name + r"_right_plate",
                config_name + r"_left_plate"
            ], config_name)

        if oled_mount_type == 'UNDERCUT':
            export_file(shape=oled_undercut_mount_frame()[1],
                        fname=path.join(save_path, config_name + r"_oled_undercut_test"))

        if oled_mount_type == 'SLIDING':
            export_file(shape=oled_sliding_mount_frame()[1],
                        fname=path.join(save_path, config_name + r"_oled_sliding_test"))

        if oled_mount_type == 'CLIP':
            oled_mount_location_xyz = (0.0, 0.0, -oled_mount_depth / 2)
            oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
            export_file(shape=oled_clip(), fname=path.join(save_path, config_name + r"_oled_clip"))
            export_file(shape=oled_clip_mount_frame()[1],
                        fname=path.join(save_path, config_name + r"_oled_clip_test"))
            export_file(shape=union((oled_clip_mount_frame()[1], oled_clip())),
                        fname=path.join(save_path, config_name + r"_oled_clip_assy_test"))

    all_merged = locals().copy()
    for item in globals():
        all_merged[item] = globals()[item]

    def get_cluster(style):
        if style == CarbonfetCluster.name():
            clust = CarbonfetCluster(all_merged)
        elif style == MiniCluster.name():
            clust = MiniCluster(all_merged)
        elif style == MinidoxCluster.name():
            clust = MinidoxCluster(all_merged)
        elif style == Minithicc.name():
            clust = Minithicc(all_merged)
        elif style == Minithicc3.name():
            clust = Minithicc3(all_merged)
        elif style == TrackballOrbyl.name():
            clust = TrackballOrbyl(all_merged)
        elif style == TrackballWild.name():
            clust = TrackballWild(all_merged)
        elif style == TrackballThree.name():
            clust = TrackballThree(all_merged)
        elif style == TrackballBTU.name():
            clust = TrackballBTU(all_merged)
        elif style == TrackballJonboh.name():
            clust = TrackballJonboh(all_merged)
        elif style == TrackballCJ.name():
            clust = TrackballCJ(all_merged)
        elif style == CustomCluster.name():
            clust = CustomCluster(all_merged)
        else:
            clust = DefaultCluster(all_merged)

        return clust


    right_cluster = get_cluster(thumb_style)

    if right_cluster.is_tb:
        if ball_side == "both":
            left_cluster = right_cluster
        elif ball_side == "left":
            left_cluster = right_cluster
            right_cluster = get_cluster(other_thumb)
        else:
            left_cluster = get_cluster(other_thumb)
    elif other_thumb != "DEFAULT" and other_thumb != thumb_style:
        left_cluster = get_cluster(other_thumb)
    else:
        left_cluster = right_cluster  # this assumes thumb_style always overrides DEFAULT other_thumb

    run()


def make_btu2static():
    shape = cylinder(14/2, 2.5)
    bearing = translate(cylinder(3/1.75, 4), [0,0,1])
    shape = difference(shape, [ bearing ])
    # shape = union([shape, bearing])
    export_file(shape, fname="things/btu2static")


def rexroth_bearing(cutter):
    # DELETEME
    tolerance_diameter = 0.25
    tolerance_depth = 1.5
    return translate(union([
            translate(cylinder(12.6/2+tolerance_diameter, 6.4+tolerance_depth), [0,0,-3.2]),
            cylinder(17/2+tolerance_diameter, 1.8+tolerance_depth),
            translate(sphere(4) if not cutter else translate(cylinder(17/2+tolerance_diameter, 4), [0,0,2]), [0,0,-0.1])
        ]), [0, 0, -0.9])


if __name__ == '__main__':
    make_dactyl()

    if ENGINE == "solid":
        make_btu2static()

    # base = baseplate()
    # export_file(shape=base, fname=path.join(save_path, config_name + r"_plate"))
