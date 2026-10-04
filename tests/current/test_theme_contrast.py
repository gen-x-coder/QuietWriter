import unittest

from quietwriter.themes import THEMES


def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip('#')
    rgb = [int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    first = _relative_luminance(a)
    second = _relative_luminance(b)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


class ThemeContrast01813Tests(unittest.TestCase):
    def test_expected_theme_family_is_available(self):
        expected = {
            'Helder', 'Porselein', 'Nevel', 'Salie', 'Lavendel', 'Nord Licht',
            'Warm', 'Papier', 'Nacht', 'Grafiet', 'Middernacht', 'Inkt',
            'Diepblauw', 'Aurora',
        }
        self.assertEqual(set(THEMES), expected)

    def test_all_themes_expose_accent_text(self):
        for name, theme in THEMES.items():
            with self.subTest(theme=name):
                self.assertIn('accent_text', theme)

    def test_normal_and_secondary_text_meet_aa_on_common_surfaces(self):
        surfaces = ('bg', 'panel', 'panel2', 'editor')
        for name, theme in THEMES.items():
            for token in ('text', 'muted'):
                for surface in surfaces:
                    with self.subTest(theme=name, token=token, surface=surface):
                        self.assertGreaterEqual(_contrast(theme[token], theme[surface]), 4.5)

    def test_primary_button_text_meets_aa_in_normal_and_hover_state(self):
        for name, theme in THEMES.items():
            with self.subTest(theme=name, state='normal'):
                self.assertGreaterEqual(_contrast(theme['accent_text'], theme['accent']), 4.5)
            with self.subTest(theme=name, state='hover'):
                self.assertGreaterEqual(_contrast(theme['accent_text'], theme['accent_hover']), 4.5)

    def test_status_text_and_hero_text_meet_aa(self):
        pairs = (
            ('success', 'success_soft'),
            ('warning', 'warning_soft'),
            ('danger', 'danger_soft'),
            ('hero_text', 'hero'),
            ('history_text', 'history'),
        )
        for name, theme in THEMES.items():
            for foreground, background in pairs:
                with self.subTest(theme=name, foreground=foreground, background=background):
                    self.assertGreaterEqual(_contrast(theme[foreground], theme[background]), 4.5)

    def test_focus_indicator_has_non_text_contrast_on_common_surfaces(self):
        surfaces = ('bg', 'panel', 'panel2', 'editor')
        for name, theme in THEMES.items():
            for surface in surfaces:
                with self.subTest(theme=name, surface=surface):
                    self.assertGreaterEqual(_contrast(theme['focus'], theme[surface]), 3.0)


if __name__ == '__main__':
    unittest.main()
