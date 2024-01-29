# Fields

```{include} snippets/wiphint.md
```

Bedeutung der Attribute eines Formularfeldes:


<details>
<summary>
<code>Label</code>
</summary>

Feldname, wird über dem Eingabefeld dargestellt. 

</details>

<details>
<summary>
<code>Help text</code> (optional)
</summary>

Erläuterungstext - auch längere Text inkl. Links. Werden "gedimmt" unterhalb des Eingabefeldes dargestellt. Siehe auch `Placeholder`.

</details>

<details>
<summary>
<code>Required</code> (optional)
</summary>

Definiert, ob das Ausfüllen dieses Feldes für die Formularabsendung notwendig ist. Diese Felder werden im Formular automatisch mit einem `*` markiert.

</details>

<details>
<summary>
<code>Field type</code>
</summary>

Feldtyp.

</details>

<details>
<summary>
<code>Choices</code> (optional)
</summary>

Nur für Auswahlfelder (siehe Feldtyp) relevant. Definiert die Ausprägungen von Auswahlfeldern.

</details>

<details>
<summary>
<code>Default value</code> (optional)
</summary>

Standardwert, falls ein Feld nicht ausgefüllt wird.

</details>

<details>
<summary>
<code>Placeholder</code> (optional)
</summary>

Kurzer Hinweistext der im Eingabefeld dargestellt wird und verschwindet, sobald das Feld ausgefüllt wird. Ähnlich wie `Help text`.

</details>

<details>
<summary>
<code>Heading</code> (optional)
</summary>

Überschrift, die über dem entsprechenden Feld dargestellt wird. Kann z.B. genutzt werden, um größere Formulare zu unterteilen.

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

Sollen Radio-Buttons oder Checkboxen "inline" (in einer Zeile statt untereinander) dargestellt werden, kann die Klasse `form-check-inline` genutzt werden.

</details>
