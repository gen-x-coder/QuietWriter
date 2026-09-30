from quietwriter.chapter_context import build_chapter_context
from quietwriter.planning_models import Character, Scene


def test_context_builder_uses_only_saved_relations_and_skips_orphans():
    alice = Character(id='c1', name='Alice')
    bob = Character(id='c2', name='Bob')
    rows = [
        Scene(id='s1', chapter_id='h1', title='Ontmoeting', character_ids=['c1', 'missing']),
        Scene(id='s2', chapter_id='h2', title='Andere scène', character_ids=['c2']),
        Scene(id='s3', chapter_id='h1', title='Tweede', character_ids=['c2', 'c1']),
    ]
    context = build_chapter_context('h1', rows, [alice, bob])
    assert [scene.title for scene in context.scenes] == ['Ontmoeting', 'Tweede']
    assert context.scenes[0].character_names == ('Alice',)
    assert context.scenes[1].character_names == ('Bob', 'Alice')
    assert context.character_names == ('Alice', 'Bob')
