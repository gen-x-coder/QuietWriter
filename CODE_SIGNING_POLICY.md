# Code Signing Policy

QuietWriter publiceert officiële Windows-builds alleen vanuit de openbare releasebron in `gen-x-coder/QuietWriter`.

## Doel

Code signing wordt gebruikt om gebruikers te helpen controleren dat een Windows-build afkomstig is van het QuietWriter-project en na de geautomatiseerde build niet is gewijzigd.

## Build- en signingproces

- Officiële releases worden gebouwd vanuit een vaste Git-commit en release-tag.
- De build vindt geautomatiseerd plaats via GitHub Actions op de openbare release-repository.
- De broncode, buildscripts en workflow die bij een release horen zijn openbaar controleerbaar.
- Signing wordt pas uitgevoerd nadat de build en geautomatiseerde controles zijn geslaagd.
- Private ontwikkelbuilds worden niet als officiële ondertekende releases gepubliceerd.
- Release-assets worden voorzien van integriteitsinformatie waar beschikbaar.

## Verantwoordelijkheid

De maintainer van QuietWriter bepaalt welke commits als officiële releases worden getagd en gepubliceerd. Bij aanwijzingen voor misbruik, gestolen credentials of een gecompromitteerde release wordt publicatie gestopt totdat de oorzaak is onderzocht.

## Privacy

Het signingproces is uitsluitend bedoeld voor software-integriteit en vraagt gebruikers niet om persoonlijke gegevens.

Free code signing provided by SignPath.io, certificate by SignPath Foundation.
