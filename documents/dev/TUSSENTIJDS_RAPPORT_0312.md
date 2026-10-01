# Tussentijds rapport 0.31.2

Deze release combineert drie kleine vervolgstappen: corruptiebescherming voor de resterende JSON-bronnen, een centrale voorbereidingsfase vóór live-book adoptie, en cursorvolging in het spellingspaneel.

De vier JSON-routes (`characters.json`, `outline.json`, `publication.json`, `export/settings.json`) behandelen ongeldige UTF-8 nu als beschadigde bron in plaats van als een ongevangen decode-exceptie. Normale writes worden door dezelfde storage-guard geweigerd. Exportinstellingen tonen een expliciete herstelstatus; Integriteit controleert nu ook `export/settings.json`.

`adopt_active_book()` leest de fallibele disk-bronnen eerst centraal in `_prepare_active_book_adoption()`. De centrale `_active_book`-pointer en revision tracking worden pas na het opnieuw binden van de pagina's gecommit. Dit verkleint de oude half-geadopteerde toestand en maakt de disk-readfase expliciet testbaar. Claude moet runtime nog specifiek proberen de commitfase te laten falen; PySide6 is hier niet beschikbaar.

Het spellingspaneel kan nu een misspelling onder de editorcursor volgen zonder tekst te selecteren. Cursorbeweging door klikken/pijltjes volgt; tekstmutaties worden via de documentrevision onderscheiden zodat typen niet voortdurend het paneel laat verspringen. Contextmenu volgt in een aparte release.
