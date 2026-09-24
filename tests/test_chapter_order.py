import random
import unittest
from dataclasses import dataclass, field

from quietwriter.chapter_order import DropTarget, chapter_ids, move_chapter

@dataclass
class C:
    id: str

@dataclass
class S:
    id: str
    chapters: list[C] = field(default_factory=list)


def ids(section):
    return [c.id for c in section.chapters]


class ChapterOrderTests(unittest.TestCase):
    def setUp(self):
        self.s1 = S('s1', [C('a'), C('b'), C('c')])
        self.s2 = S('s2', [C('d'), C('e')])
        self.sections = [self.s1, self.s2]

    def test_same_section_before(self):
        self.assertTrue(move_chapter(self.sections, 'c', DropTarget('chapter', 'a', True)))
        self.assertEqual(ids(self.s1), ['c', 'a', 'b'])

    def test_same_section_after(self):
        self.assertTrue(move_chapter(self.sections, 'a', DropTarget('chapter', 'c', False)))
        self.assertEqual(ids(self.s1), ['b', 'c', 'a'])

    def test_cross_section_before(self):
        self.assertTrue(move_chapter(self.sections, 'b', DropTarget('chapter', 'e', True)))
        self.assertEqual(ids(self.s1), ['a', 'c'])
        self.assertEqual(ids(self.s2), ['d', 'b', 'e'])

    def test_section_top_and_bottom(self):
        self.assertTrue(move_chapter(self.sections, 'c', DropTarget('section', 's2', True)))
        self.assertEqual(ids(self.s2), ['c', 'd', 'e'])
        self.assertTrue(move_chapter(self.sections, 'a', DropTarget('section', 's2', False)))
        self.assertEqual(ids(self.s2), ['c', 'd', 'e', 'a'])

    def test_invalid_target_is_non_destructive(self):
        before = chapter_ids(self.sections)
        self.assertFalse(move_chapter(self.sections, 'b', DropTarget('chapter', 'missing', True)))
        self.assertEqual(chapter_ids(self.sections), before)

    def test_self_drop_is_non_destructive(self):
        before = chapter_ids(self.sections)
        self.assertFalse(move_chapter(self.sections, 'b', DropTarget('chapter', 'b', True)))
        self.assertEqual(chapter_ids(self.sections), before)

    def test_random_moves_never_lose_or_duplicate_chapters(self):
        expected = set(chapter_ids(self.sections))
        rng = random.Random(1976)
        for _ in range(1000):
            current = chapter_ids(self.sections)
            source = rng.choice(current)
            if rng.random() < .75:
                target = rng.choice(current)
                move_chapter(self.sections, source, DropTarget('chapter', target, bool(rng.getrandbits(1))))
            else:
                target_section = rng.choice(self.sections).id
                move_chapter(self.sections, source, DropTarget('section', target_section, bool(rng.getrandbits(1))))
            now = chapter_ids(self.sections)
            self.assertEqual(set(now), expected)
            self.assertEqual(len(now), len(expected))

if __name__ == '__main__':
    unittest.main()
