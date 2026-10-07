from quietwriter.document_view import visible_text


def test_darling_projection_hides_storage_markup_but_keeps_literal_text():
    source = r'**Vet** en 5\*3' + '\n' + r'\- geen lijst'
    assert visible_text(source) == 'Vet en 5*3\n- geen lijst'
