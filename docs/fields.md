# Felder

```{include} snippets/wiphint.md
```

Ein Formular besteht aus Formularfeldern ("Form fields"). Jedes Feld hat einen Feldtyp und einige Attribute. Der Editor zeigt nur die Attribute an, die für den gewählten Feldtyp eine Wirkung haben (z.B. `Choices` nur für Auswahlfelder). Daher am besten zuerst den Feldtyp wählen.

Die Attribute stehen bei allen Feldtypen in derselben Reihenfolge: zuerst der Feldtyp, dann das erforderliche `Label`, dann die allgemeinen Attribute (`Help text`, `Required`, `Heading`, `CSS class names`), zuletzt die Attribute, die nur für einige Feldtypen gelten (`Choices`, `Default value`, `Placeholder`).

Gespeicherte Formularfelder sind im Editor eingeklappt. Ihre Titelzeile zeigt das Label und den Feldtyp, bei Seitenumbrüchen die Überschrift und den Schritt, den sie beginnen.

Wie sich ein Formular mit Überschriften und Schritten gliedern lässt, steht unter [Ein Formular strukturieren](structure.md); Umfragen mit Ergebnissen unter [Umfragen und Danke-Seite](polls.md).

## Feldtypen

| Feldtyp im Editor | Für | In Umfrage-Ergebnissen |
| --- | --- | --- |
| `Single line text` | kurze Texte, z.B. Name | nein |
| `Multi-line text` | längere Texte, z.B. Anmerkungen | nein |
| `Email` | E-Mail-Adressen; das Format wird geprüft | nein |
| `Number` | Zahlen | nein |
| `URL` | Web-Adressen; das Format wird geprüft | nein |
| `Checkbox` | ein einzelnes Ankreuzfeld, z.B. eine Einwilligung | nein |
| `Checkboxes` | mehrere Ankreuzfelder, mehrere Antworten möglich | ja |
| `Drop down` | eine Antwort aus einer Auswahlliste | ja |
| `Multiple select` | mehrere Antworten aus einer Auswahlliste | ja |
| `Radio buttons` | eine Antwort aus wenigen sichtbaren Möglichkeiten | ja |
| `Multiple Choice (typeahead)` | mehrere Antworten aus einer langen Liste, mit Suche beim Tippen | ja |
| `Date` | ein Datum | nein |
| `Date/time` | ein Datum mit Uhrzeit | nein |
| `Hidden field` | unsichtbar, sendet immer den `Default value` mit, z.B. die Quelle des Formulars | nein |
| `Image file` | ein hochgeladenes Bild | nein |
| `Document file` | ein hochgeladenes Dokument; die erlaubten Dateitypen gelten pro Formular (siehe [FAQ](faq.md)) | nein |
| `Page break (starts a new step)` | kein Eingabefeld: teilt das Formular in Schritte, siehe [Mehrstufige Formulare](structure.md#mehrstufige-formulare) | – |

## Attribute

<details>
<summary>
<code>Field type</code>
</summary>

Der Feldtyp, siehe [Feldtypen](#feldtypen). Bestimmt, welche weiteren Attribute angezeigt werden.

</details>

<details>
<summary>
<code>Label</code>
</summary>

Die Frage bzw. der Feldname, wird über dem Eingabefeld dargestellt. Für alle Feldtypen außer dem Seitenumbruch erforderlich.

Das Label kann auch nach dem Veröffentlichen geändert werden: Einsendungen, Export und API ordnen die Antworten weiter richtig zu, über einen internen Feldnamen, der beim ersten Speichern festgelegt wird und gleich bleibt. Übersicht und Export zeigen das neue Label als Spaltenüberschrift.

```{admonition} Felder nicht löschen, solange Einsendungen gebraucht werden
   :class: warning

   Ein gelöschtes Feld verschwindet aus der Übersicht und dem Export der Einsendungen, auch für frühere Einsendungen.
```

</details>

<details>
<summary>
<code>Help text</code> (optional)
</summary>

Erläuterungstext, auch längere Texte inkl. Links. Wird "gedimmt" unterhalb des Eingabefeldes dargestellt. Siehe auch `Placeholder`.

</details>

<details>
<summary>
<code>Required</code> (optional)
</summary>

Definiert, ob das Ausfüllen dieses Feldes für das Absenden notwendig ist. Diese Felder werden im Formular mit einem `*` markiert; ein Hinweis über dem Formular erklärt das Zeichen.

Eine erforderliche `Checkbox` muss angehakt werden, sonst lässt sich das Formular nicht absenden. Das passt für eine Einwilligung ("Ich habe die Datenschutzhinweise gelesen."). Für eine Ja/Nein-Frage stattdessen `Radio buttons` mit den `Choices` "Ja" und "Nein" verwenden.

</details>

<details>
<summary>
<code>Heading</code> (optional)
</summary>

Eine Zwischenüberschrift über dem Feld, um ein längeres Formular zu gliedern. Bei einem Seitenumbruch: die Überschrift des neuen Schritts. Siehe [Ein Formular strukturieren](structure.md).

</details>

<details>
<summary>
<code>CSS class names</code> (optional)
</summary>

Eigene CSS-Klassen können hier, mit Leerzeichen getrennt, angegeben werden. Die meisten CSS-Klassen des verwendeten User-Interface-Frameworks [Bootstrap5](https://getbootstrap.com/docs/5.3/getting-started/introduction/) sollten unterstützt sein. Die CSS-Klasse(n) werden auf ein Container-Element des jeweiligen Feldes angewandt.

Verwendungsmöglichkeiten (Auszug):

* Trennlinie vor dem Feld: `border-top pt-2 mt-2`
* Hervorheben des gesamten Feldes inkl. aller Attribute (Hilfetext etc.): `alert alert-info`

**Inline selects**

Sollen Radio-Buttons oder Checkboxen "inline" (in einer Zeile statt untereinander) dargestellt werden, kann die Klasse `to-form-check-inline` genutzt werden.

**Sekundäre Felder**

Über die CSS-Klasse `field-secondary` können Felder weniger prominent dargestellt werden (etwas kleiner Input-Bereich, Schriftfarbe zurückgenommen).

</details>

<details>
<summary>
<code>Choices</code> (nur Auswahlfelder)
</summary>

Die Antwortmöglichkeiten eines Auswahlfeldes (`Checkboxes`, `Drop down`, `Multiple select`, `Radio buttons`, `Multiple Choice (typeahead)`): eine pro Zeile. Steht alles in einer Zeile, trennen Kommas die Antwortmöglichkeiten.

```text
Präsenz
Hybrid
Online
```

```{admonition} Antwortmöglichkeiten nach dem Start nicht umbenennen
   :class: warning

   Frühere Einsendungen behalten die alte Bezeichnung. In [Umfrage-Ergebnissen](polls.md) zählen sie dann nicht mehr mit.
```

</details>

<details>
<summary>
<code>Default value</code> (optional)
</summary>

Ein Wert, mit dem das Feld vorausgefüllt ist; Besucher:innen können ihn ändern (außer bei `Hidden field`).

* `Checkboxes`: vorausgewählte Antworten, eine pro Zeile, genau wie in `Choices` geschrieben.
* `Radio buttons`, `Drop down`, `Multiple select`, `Multiple Choice (typeahead)`: eine vorausgewählte Antwort, genau wie in `Choices` geschrieben.
* `Checkbox`: z.B. "ja" oder "yes" hakt das Feld an; leer, "nein", "no", "false" oder "0" lässt es frei.
* `Date`: im Format `JJJJ-MM-TT`, z.B. `2027-03-01`.

Ein Wert, der keine der `Choices` ist (z.B. "Bitte wählen"), hat keine Wirkung. Ein `Drop down` ohne `Default value` zeigt die erste Antwortmöglichkeit vorausgewählt.

Nicht für Upload-Felder und Seitenumbrüche.

</details>

<details>
<summary>
<code>Placeholder</code> (nur Textfelder)
</summary>

Kurzer Hinweistext, der im Eingabefeld dargestellt wird und verschwindet, sobald das Feld ausgefüllt wird. Ähnlich wie `Help text`. Nur für Feldtypen, in denen Browser ihn anzeigen (Texte, E-Mail, Zahl, URL, Multiple Choice (typeahead)).

</details>
