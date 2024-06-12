import json
import os

from clusters.default_cluster import DefaultCluster
from clusters.trackball_wilder import TrackballWild


class TrackballJonboh(DefaultCluster):
    key_diameter = 75
    translation_offset = [-10, 24, -25.5]
    rotation_offset = [0, 0, 0]
    ball_wall_thickness = 4
    ball_gap = 4
    tb_height = 0

    @staticmethod
    def name():
        return "TRACKBALL_JONBOH"

    def get_config(self):
        with open(
            os.path.join("src", "clusters", "json", "DEFAULT.json"), mode="r"
        ) as fid:
            data = json.load(fid)

        superdata = super().get_config()

        # overwrite any super variables with this class' needs
        for item in data:
            superdata[item] = data[item]

        for item in superdata:
            if not hasattr(self, str(item)):
                print(self.name() + ": NO MEMBER VARIABLE FOR " + str(item))
                continue
            setattr(self, str(item), superdata[item])

        return superdata

    def __init__(self, parent_locals):
        # self.num_keys = 4
        self.is_tb = True
        super().__init__(parent_locals)
        for item in parent_locals:
            globals()[item] = parent_locals[item]

    def position_rotation(self):
        rot = [0, 0, 0]
        pos = self.thumborigin()
        pos[0] -= 1
        pos[1] -= 1
        pos[2] += 3.5
        # Changes size based on key diameter around ball, shifting off of the top left cluster key.
        shift = [
            -0.9 * self.key_diameter / 2 + 27 - 42,
            -0.1 * self.key_diameter / 2 + 3 - 20,
            -5,
        ]
        for i in range(len(pos)):
            pos[i] = pos[i] + shift[i] + self.translation_offset[i]

        for i in range(len(rot)):
            rot[i] = rot[i] + self.rotation_offset[i]

        return pos, rot

    def track_place(self, shape):
        pos, rot = self.position_rotation()
        shape = rotate(shape, rot)
        shape = translate(shape, pos)
        return shape

    def _thumb_1x_layout(self, shape, cap=False):
        debugprint("thumb_1x_layout()")
        shapes = [
            self.mr_place(rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
            self.br_place(rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
            self.bl_place(rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            self.tr_place(rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
            self.tl_place(rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
        ]
        return shapes

    def thumb_fx_layout(self, shape):
        return union([])

    def thumbcaps(self, side="right"):
        t1 = self.thumb_1x_layout(ulp_fancy_cap(1))
        return t1

    def tb_post(self, y_rotation, z_rotation):
        radius = ball_diameter / 2 + self.ball_wall_thickness + self.ball_gap
        return rotate(
            translate(web_post(), [radius - post_adj, 0, self.tb_height]),
            [0, y_rotation, z_rotation],
        )

    def tb_post_0(self):
        return self.tb_post(-20, 0)

    def tb_post_30(self):
        return self.tb_post(-30, 30)

    def tb_post_60(self):
        return self.tb_post(-40, 60)

    def tb_post_90(self):
        return self.tb_post(-40, 90)

    def tb_post_120(self):
        return self.tb_post(-35, 120)

    def tb_post_150(self):
        return self.tb_post(-25, 150)

    def tb_post_180(self):
        return self.tb_post(-20, 180)

    def tb_post_210(self):
        return self.tb_post(-7.5, 210)

    def tb_post_240(self):
        return self.tb_post(5, 240)

    def tb_post_270(self):
        return self.tb_post(10, 270)

    def tb_post_300(self):
        return self.tb_post(10, 300)

    def tb_post_330(self):
        return self.tb_post(-7.5, 330)

    def _thumb_connectors(self, side="right"):
        hulls = []
        hulls += _triangle_hulls(
            [
                self.tr_place(web_post_br()),
                self.tr_place(web_post_bl()),
                self.mr_place(web_post_br()),
                self.tr_place(web_post_bl()),
                self.mr_place(web_post_tr()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.tl_place(web_post_bl()),
                self.mr_place(web_post_tl()),
                self.mr_place(web_post_tr()),
                self.tr_place(web_post_tl()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.mr_place(web_post_bl()),
                self.mr_place(web_post_tl()),
                self.bl_place(web_post_tr()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.tl_place(web_post_br()),
                self.tr_place(web_post_tl()),
                self.tl_place(web_post_bl()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.tr_place(web_post_tr()),
                self.tr_place(web_post_tl()),
                self.tl_place(web_post_br()),
            ]
        )
        hulls += _triangle_hulls(
            [
                key_place(web_post_bl(), 0, 2),
                self.tl_place(web_post_br()),
                key_place(web_post_tl(), 0, 2),
                self.tl_place(web_post_tr()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.mr_place(web_post_bl()),
                self.bl_place(web_post_tr()),
                self.bl_place(web_post_br()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.mr_place(web_post_tr()),
                self.tr_place(web_post_bl()),
                self.tr_place(web_post_tl()),
            ]
        )
        return hulls

    def walls(self, side="right"):
        print("thumb_walls()")
        shapes = list()
        shapes.append(
            wall_brace(
                self.mr_place, 0, -1, web_post_br(), self.mr_place, 0, -1, web_post_bl()
            )
        )
        shapes.append(
            wall_brace(
                self.mr_place,
                0,
                -1,
                web_post_bl(),
                self.bl_place,
                -3,
                -1,
                web_post_br(),
            )
        )
        shapes.append(
            wall_brace(
                self.bl_place,
                -3,
                -1,
                web_post_br(),
                self.bl_place,
                -3,
                -1,
                web_post_bl(),
            )
        )
        shapes.append(
            wall_brace(
                self.bl_place,
                -3,
                -1,
                web_post_bl(),
                self.bl_place,
                -3,
                0,
                web_post_bl(),
            )
        )

        shapes.append(
            wall_brace(
                (lambda sh: left_key_place(sh, 0, 1, side=side)),
                0,
                1,
                web_post(),
                self.track_place,
                -3,
                0,
                translate(self.tb_post_60(), wall_locate3(1, 3)),
            )
        )
        shapes.append(
            wall_brace(
                self.track_place,
                -3,
                0,
                translate(self.tb_post_60(), wall_locate3(-1, 3)),
                self.track_place,
                -3,
                0,
                translate(self.tb_post_90(), wall_locate3(-2, 2)),
            )
        )
        shapes.append(
            wall_brace(
                self.track_place,
                -3,
                0,
                translate(self.tb_post_90(), wall_locate3(-2, 2)),
                self.track_place,
                -3,
                0,
                translate(self.tb_post_120(), wall_locate3(-4, 0)),
            )
        )
        shapes.append(
            wall_brace(
                self.track_place,
                -3,
                0,
                translate(self.tb_post_120(), wall_locate3(-4, 0)),
                self.track_place,
                -3,
                0,
                translate(self.tb_post_180(), wall_locate3(-2, 0)),
            )
        )
        shapes.append(
            wall_brace(
                self.track_place,
                -3,
                0,
                translate(self.tb_post_180(), wall_locate3(-2, 0)),
                self.track_place,
                -3,
                0,
                translate(self.tb_post_210(), wall_locate3(-2, 0)),
            )
        )
        shapes.append(
            wall_brace(
                self.track_place,
                -3,
                0,
                translate(self.tb_post_210(), wall_locate3(-2, 0)),
                self.track_place,
                -3,
                0,
                translate(self.tb_post_240(), wall_locate3(-2, 0)),
            )
        )
        shapes.append(
            wall_brace(
                self.track_place,
                -3,
                0,
                translate(self.tb_post_240(), wall_locate3(-2, 0)),
                self.bl_place,
                -3,
                0,
                web_post_tl(),
            )
        )
        shapes.append(
            wall_brace(
                self.bl_place,
                -3,
                0,
                web_post_tl(),
                self.bl_place,
                -3,
                0,
                web_post_bl(),
            )
        )
        shapes.append(
            wall_brace(
                (lambda sh: cluster_key_place(sh, 0, lastrow)),
                0,
                -1,
                web_post_br(),
                (lambda sh: cluster_key_place(sh, 1, lastrow)),
                0,
                -1,
                web_post_bl(),
            )
        )
        shapes.append(
            wall_brace(
                (lambda sh: cluster_key_place(sh, 1, lastrow)),
                0,
                -1,
                web_post_bl(),
                (lambda sh: cluster_key_place(sh, 1, lastrow)),
                0,
                -1,
                web_post_br(),
            )
        )
        shapes.append(
            wall_brace(
                (lambda sh: cluster_key_place(sh, 1, lastrow)),
                0,
                -1,
                web_post_br(),
                (lambda sh: cluster_key_place(sh, 3, lastrow)),
                0,
                -1,
                web_post_bl(),
            )
        )
        shapes.append(
            wall_brace(
                (lambda sh: cluster_key_place(sh, 3, lastrow)),
                0,
                -1,
                web_post_bl(),
                (lambda sh: cluster_key_place(sh, 3, lastrow)),
                -1,
                -1,
                web_post_br(),
            )
        )
        shapes.append(
            wall_brace(
                (lambda sh: cluster_key_place(sh, 3, lastrow)),
                -1,
                -1,
                web_post_br(),
                self.br_place,
                -1,
                -1,
                web_post_tl(),
            )
        )
        shapes.append(
            wall_brace(
                self.br_place,
                -1,
                -1,
                web_post_tl(),
                self.br_place,
                -1,
                -1,
                web_post_bl(),
            )
        )
        shapes.append(
            wall_brace(
                self.br_place,
                -1,
                -1,
                web_post_bl(),
                self.br_place,
                1,
                -1,
                web_post_br(),
            )
        )
        shapes.append(
            wall_brace(
                self.br_place,
                1,
                -1,
                web_post_br(),
                (lambda sh: cluster_key_place(sh, 4, lastrow)),
                1
                if not thin_right_wall
                else 0.3,  # NOTE: hack to close border in the thin wall case
                0,
                web_post_br(),
            )
        )
        # thumb corner
        extra_walls = [
            bottom_hull(
                _triangle_hulls(
                    [
                        self.mr_place(translate(web_post_br(), wall_locate3(0, -1))),
                        self.mr_place(
                            translate(web_post_br(), wall_locate3(0, -1, True))
                        ),
                        self.tr_place(web_post_br()),
                    ]
                )
            ),
            bottom_hull(
                _triangle_hulls(
                    [
                        self.tr_place(web_post_br()),
                        cluster_key_place(
                            translate(web_post_br(), wall_locate3(0, -1)), 0, lastrow
                        ),
                        cluster_key_place(
                            translate(web_post_br(), wall_locate3(0, -1, True)),
                            0,
                            lastrow,
                        ),
                    ]
                )
            ),
            _triangle_hulls(
                [
                    self.tr_place(web_post_bl()),
                    self.mr_place(translate(web_post_br(), wall_locate1(0, -1))),
                    self.tr_place(web_post_br()),
                    self.mr_place(translate(web_post_br(), wall_locate1(0, -1))),
                    self.tr_place(web_post_br()),
                    self.mr_place(translate(web_post_br(), wall_locate3(0, -1))),
                ]
            ),
        ]
        extra_braces = []
        vertical = union(list(map(lambda x: x[0], shapes)) + extra_walls)
        braces = union(list(map(lambda x: x[1], shapes)) + extra_braces)
        return vertical, braces

    def connection(self, side="right"):
        print("thumb_connection()")
        shapes = list()
        shapes.append(
            triangle_hulls(
                [
                    self.tl_place(web_post_tl()),
                    self.track_place(self.tb_post_60()),
                    self.tl_place(web_post_tr()),
                    key_place(web_post_bl(), 0, 0),
                    key_place(web_post_bl(), 0, 1),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    key_place(web_post_bl(), 0, 0),
                    self.track_place(self.tb_post_60()),
                    key_place(web_post_tl(), 0, 0),
                    left_key_place(web_post(), 0, 1, low_corner=True, side=side),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    # left_key_place(web_post(), 0, -1, low_corner=True, side=side),
                    left_key_place(web_post(), 0, 1, side=side),
                    self.track_place(self.tb_post_60()),
                    self.track_place(translate(self.tb_post_60(), wall_locate3(-1, 3))),
                    self.track_place(self.tb_post_90()),
                    self.track_place(translate(self.tb_post_90(), wall_locate3(-2, 2))),
                    self.track_place(self.tb_post_120()),
                    self.track_place(
                        translate(self.tb_post_120(), wall_locate3(-4, 0))
                    ),
                    self.track_place(self.tb_post_150()),
                    self.track_place(
                        translate(self.tb_post_150(), wall_locate3(-4, 0))
                    ),
                    self.track_place(self.tb_post_180()),
                    self.track_place(
                        translate(self.tb_post_180(), wall_locate3(-2, 0))
                    ),
                    self.track_place(self.tb_post_210()),
                    self.track_place(
                        translate(self.tb_post_210(), wall_locate3(-2, 0))
                    ),
                    self.track_place(self.tb_post_240()),
                    self.track_place(
                        translate(self.tb_post_240(), wall_locate3(-2, 0))
                    ),
                    self.track_place(self.tb_post_240()),
                    self.bl_place(web_post_tl()),
                    self.track_place(self.tb_post_270()),
                    self.bl_place(web_post_tr()),
                    self.track_place(self.tb_post_300()),
                    self.mr_place(web_post_tl()),
                    self.track_place(self.tb_post_330()),
                    self.tl_place(web_post_bl()),
                    self.track_place(self.tb_post_0()),
                    self.tl_place(web_post_tl()),
                    self.track_place(self.tb_post_30()),
                    self.tl_place(web_post_tl()),
                    self.track_place(self.tb_post_60()),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    cluster_key_place(web_post_br(), 3, lastrow),
                    self.br_place(web_post_tl()),
                    cluster_key_place(web_post_bl(), 4, lastrow),
                    self.br_place(web_post_tr()),
                    cluster_key_place(web_post_br(), 4, lastrow),
                    self.br_place(web_post_br()),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    cluster_key_place(web_post_bl(), 0, cornerrow),
                    self.tr_place(web_post_tr()),
                    cluster_key_place(web_post_br(), 0, cornerrow),
                    self.tr_place(web_post_br()),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    self.tr_place(web_post_br()),
                    cluster_key_place(
                        translate(web_post_br(), wall_locate3(0, -1)), 0, lastrow
                    ),
                    cluster_key_place(web_post_br(), 0, lastrow),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    cluster_key_place(web_post_br(), 1, cornerrow),
                    cluster_key_place(web_post_bl(), 2, cornerrow),
                    cluster_key_place(web_post_br(), 2, cornerrow),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    cluster_key_place(web_post_br(), 1, cornerrow),
                    cluster_key_place(web_post_br(), 2, cornerrow),
                    cluster_key_place(web_post_bl(), 3, cornerrow),
                ]
            )
        )
        shape = union(shapes)

        return shape

    def has_btus(self):
        return True
