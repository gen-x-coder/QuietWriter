from quietwriter.editor_view import TEXT_WIDTHS


def test_0369_width_scale_shifts_previous_visual_steps_up_one_label():
    assert TEXT_WIDTHS == {
        'extra_narrow': 720,
        'narrow': 850,
        'normal': 1000,
        'wide': 1180,
        'extra_wide': 1360,
    }


def test_0369_normal_is_a_comfortably_wider_default():
    assert TEXT_WIDTHS['normal'] == 1000
    assert TEXT_WIDTHS['extra_wide'] - TEXT_WIDTHS['wide'] >= 150
