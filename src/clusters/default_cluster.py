import json
import os


class DefaultCluster(object):
    num_keys = 6
    is_tb = False
    thumb_pos_offsets = [-9, 12, 18.5]
    thumb_rot_offset = [0, -35, 0]
    thumb_plate_te_rotation = 0
    thumb_plate_tr_rotation = 0
    thumb_plate_tl_rotation = 0
    thumb_plate_mr_rotation = 0
    thumb_plate_ml_rotation = 0
    thumb_plate_br_rotation = 0
    thumb_plate_bl_rotation = 0

    @staticmethod
    def name():
        return "DEFAULT"

    def get_config(self):
        with open(
            os.path.join("src", "clusters", "json", "DEFAULT.json"), mode="r"
        ) as fid:
            data = json.load(fid)
        for item in data:
            if not hasattr(self, str(item)):
                print(self.name() + ": NO MEMBER VARIABLE FOR " + str(item))
                continue
            setattr(self, str(item), data[item])
        return data

    def __init__(self, parent_locals):
        for item in parent_locals:
            globals()[item] = parent_locals[item]
        self.get_config()
        print(self.name(), " built")

    def thumborigin(self):
        # debugprint('thumborigin()')
        origin = key_position([mount_width / 2, -(mount_height / 2), 0], 1, cornerrow)
        _thumb_offsets = self.thumb_pos_offsets.copy()
        if shift_column != 0:
            _thumb_offsets[0] = self.thumb_pos_offsets[0] + (
                shift_column * (mount_width + 6)
            )
            # if shift_column < 0:  # raise cluster up when moving inward
            #     _thumb_offsets[1] = self.thumb_offsets[1] - (shift_column * 3)
            #     _thumb_offsets[2] = self.thumb_offsets[2] - (shift_column * 8)
            #     if shift_column <= -2:
            #         # y = shift_column * 15
            #         _thumb_offsets[1] = self.thumb_offsets[1] - (shift_column * 15)
        for i in range(len(origin)):
            origin[i] = origin[i] + _thumb_offsets[i]

        return origin

    def thumb_rotate(self):
        x = y = z = 0
        if shift_column != 0:
            y = shift_column * 8
            if shift_column < 0:
                z = shift_column * -10
        return [
            x + self.thumb_rot_offset[0],
            y + self.thumb_rot_offset[1],
            z + self.thumb_rot_offset[2],
        ]

    def thumb_place(self, shape):
        return translate(rotate(shape, self.thumb_rotate()), self.thumborigin())

    def te_place(self, shape):
        debugprint("t2_place()")
        shape = translate(shape, [-8.5, 18, -1])
        shape = rotate(shape, [47.5, -18, 15])
        shape = translate(shape, [-32.5, 0, 15])
        shape = self.thumb_place(shape)
        return shape

    def tl_place(self, shape):
        debugprint("tl_place()")
        shape = rotate(shape, [27.5, -18, 12])
        shape = translate(shape, [-32.5, -3, 15])
        shape = self.thumb_place(shape)
        return shape

    def tr_place(self, shape):
        debugprint("tr_place()")
        shape = rotate(shape, [10, -20, 10])
        shape = translate(shape, [-25, -20, 10])
        shape = self.thumb_place(shape)
        return shape

    def mr_place(self, shape):
        debugprint("mr_place()")
        # shape = rotate(shape, [-6, -34, 48])
        # shape = translate(shape, [-29, -40, -13])
        shape = rotate(shape, [7.5, -18, 15])
        shape = translate(shape, [-43.5, -25, 2])
        shape = self.thumb_place(shape)
        return shape

    def ml_place(self, shape):
        debugprint("ml_place()")
        # shape = rotate(shape, [6, -34, 10])
        # shape = translate(shape, [-51, -25, -12])
        shape = rotate(shape, [30.5, -20, 18])
        shape = translate(shape, [-52, -8, 9])
        shape = self.thumb_place(shape)
        return shape

    def br_place(self, shape):
        debugprint("br_place()")
        # shape = rotate(shape, [6, -20, 10])
        # shape = translate(shape, [-32, -44, -9])
        shape = rotate(shape, [17, 35, -5])
        shape = translate(shape, [22, -41.9, -62])
        shape = self.thumb_place(shape)
        return shape

    def bl_place(self, shape):
        debugprint("bl_place()")
        # shape = rotate(shape, [-4, -35, 52])
        # shape = translate(shape, [-56.3, -43.3, -23.5])
        shape = rotate(shape, [13, 35, 22])
        shape = translate(shape, [-64, -33, 5])
        shape = self.thumb_place(shape)
        return shape

    def _thumb_1x_layout(self, shape, cap=False):
        debugprint("thumb_1x_layout()")
        shapes = [
            self.mr_place(rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
            self.ml_place(rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
            self.br_place(rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
            self.bl_place(rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            self.tr_place(rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
            self.tl_place(rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
            self.te_place(rotate(shape, [0, 0, self.thumb_plate_te_rotation])),
        ]
        return shapes

    def thumb_1x_layout(self, shape, cap=False):
        return union(self._thumb_1x_layout(shape, cap))

    def thumbcaps(self, side="right"):
        t1 = self.thumb_1x_layout(ulp_fancy_cap(1), cap=True)
        return t1

    def thumb(self, side="right"):
        print("thumb()")
        plate = single_plate(side=side)
        # plate = s.union()(plate, cross())
        shape = self.thumb_1x_layout(plate)
        return shape

    def pcbs(self, side="right"):
        print("thumb()")
        shape = self.thumb_1x_layout(key_pcb())
        return shape

    def thumb_post_tr(self):
        debugprint("thumb_post_tr()")
        return translate(
            web_post(),
            [
                (mount_width / 2) - post_adj,
                ((mount_height / 2) + double_plate_height) - post_adj,
                0,
            ],
        )

    def thumb_post_tl(self):
        debugprint("thumb_post_tl()")
        return translate(
            web_post(),
            [
                -(mount_width / 2) + post_adj,
                ((mount_height / 2) + double_plate_height) - post_adj,
                0,
            ],
        )

    def thumb_post_bl(self):
        debugprint("thumb_post_bl()")
        return translate(
            web_post(),
            [
                -(mount_width / 2) + post_adj,
                -((mount_height / 2) + double_plate_height) + post_adj,
                0,
            ],
        )

    def thumb_post_br(self):
        debugprint("thumb_post_br()")
        return translate(
            web_post(),
            [
                (mount_width / 2) - post_adj,
                -((mount_height / 2) + double_plate_height) + post_adj,
                0,
            ],
        )

    def _thumb_connectors(self, side="right"):
        print("default thumb_connectors()")
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
        hulls += _triangle_hulls(
            [
                self.tl_place(web_post_bl()),
                self.tl_place(web_post_tl()),
                self.ml_place(web_post_tr()),
                # self.te_place(web_post_tl()),
                # self.te_place(web_post_bl()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.te_place(web_post_bl()),
                self.te_place(web_post_tl()),
                self.ml_place(web_post_tl()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.mr_place(web_post_tr()),
                self.ml_place(web_post_br()),
                self.mr_place(web_post_tl()),
                self.ml_place(web_post_bl()),
                self.bl_place(web_post_tr()),
                self.bl_place(web_post_tl()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.te_place(web_post_tr()),
                self.te_place(web_post_br()),
                self.tl_place(web_post_tr()),
                self.tl_place(web_post_tl()),
                # self.te_place(web_post_tl()),
                # self.ml_place(web_post_tl()),
            ]
        )
        hulls += _triangle_hulls(
            [
                self.ml_place(web_post_bl()),
                self.bl_place(web_post_tl()),
                self.ml_place(web_post_tl()),
            ]
        )
        return hulls

    def thumb_connectors(self, side="right"):
        return union(self._thumb_connectors(side))

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
                -1,
                -1,
                web_post_br(),
            )
        )
        shapes.append(
            wall_brace(
                self.bl_place,
                -1,
                -1,
                web_post_br(),
                self.bl_place,
                -1,
                -1,
                web_post_bl(),
            )
        )
        shapes.append(
            wall_brace(
                self.bl_place,
                -1,
                -1,
                web_post_bl(),
                self.bl_place,
                -1,
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
                (lambda sh: left_key_place(sh, 0, 1, side=side)),
                -1,
                0,
                web_post(),
            )
        )
        shapes.append(
            wall_brace(
                lambda sh: left_key_place(sh, 0, 1, side=side),
                -1,
                0,
                web_post(),
                self.te_place,
                0,
                1,
                web_post_tl(),
            )
        )
        shapes.append(
            wall_brace(
                self.te_place,
                0,
                1,
                web_post_tl(),
                self.ml_place,
                -2,
                1,
                web_post_tl(),
            )
        )
        shapes.append(
            wall_brace(
                self.ml_place,
                -2,
                1,
                web_post_tl(),
                self.bl_place,
                -1,
                0,
                web_post_tl(),
            )
        )
        shapes.append(
            wall_brace(
                self.bl_place,
                -1,
                0,
                web_post_tl(),
                self.bl_place,
                -1,
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

        extra_walls = [
            bottom_hull(
                _triangle_hulls(
                    [
                        self.mr_place(translate(web_post_br(), wall_locate1(0, -1))),
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
                            translate(web_post_br(), wall_locate2(0, -1)), 0, lastrow
                        ),
                        cluster_key_place(
                            translate(web_post_br(), wall_locate1(0, -1)),
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
                        translate(web_post_br(), wall_locate1(0, -1)), 0, lastrow
                    ),
                    cluster_key_place(web_post_br(), 0, lastrow),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    key_place(web_post_bl(), 0, 1),
                    key_place(web_post_bl(), 0, 0),
                    self.tl_place(web_post_tr()),
                    self.te_place(web_post_tr()),
                    key_place(web_post_bl(), 0, 0),
                    left_key_place(web_post(), 0, 1, low_corner=True, side=side),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    self.te_place(web_post_tr()),
                    self.te_place(web_post_tl()),
                    left_key_place(web_post(), 0, 1, low_corner=True, side=side),
                ]
            )
        )
        shapes.append(
            triangle_hulls(
                [
                    key_place(web_post_tl(), 0, 0),
                    key_place(web_post_bl(), 0, 0),
                    left_key_place(web_post(), 0, 1, low_corner=True, side=side),
                ]
            )
        )

        shape = union(shapes)

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-15, -58, 0]))
        position[2] = 0

        return position

    def get_extras(self, shape, pos):
        return shape

    def has_btus(self):
        return False
