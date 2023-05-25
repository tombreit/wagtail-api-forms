# FAQ

```{include} snippets/wiphint.md
```

```{admonition} Multilanguage
   The backend is available in many languages and can be set via the account settings (bottom left).  For this documentation the English identifiers are used.
```

<details>
<summary>Bei mir ist alles auf Englisch, ich will es aber auf Deutsch (oder andersrum)!</summary>

Die Backendsprache wird automatisch durch die Browser-Präferenz festgelegt.
Soll trotdem eine andere Sprache im Backend gewünscht sein, kann diese in den
Account-Einstellungen festegelgt werden (unten links "Username" → "Account")

</details>

<details>
<summary>Neues Formular anlegen</summary>

Über das "Seiten"/"Pages"-Menü in den gewünschten Bereich/Container navigieren
und via "Unterseite hinzufügen"/"Add child page" eine neue Seite hinzufügen und
auf der neuen Seite dann "Form Fields". Im Anschluss kann die Seite publiziert
werden (Button "Publish" unten auf der Seite).

</details>

<details>
<summary>Übersetzung für Formular anlegen</summary>

Für eine existierende Seite kann eine Übersetzung angelegt werden: Via
"Translate" im Seiten-Actions-Menü. Hierbei wird im entsprechenden Seitenbaum
der anderen Sprache eine Kopie dieser Seite mit den ursprünglichen Inhalten
angelegt. Diese Inhalte auf der neuen Seite sind dann manuell zu übersetzen/überschreiben.

</details>

<details>
<summary>Wo sind die Formulardaten?</summary>

Formulardaten werden standardmäßig im System gespeichert. Über den
Navigationspunkt "Forms" können die submissions der einzelnen Formulare
eingesehen werden und auch exportiert (Excel, CSV) werden. 

Weiter bietet jedes Formular eine Einstellung, dass submissions an eine
definierte Email-Adresse ("To adress") versendet werden. Diese - und weitere zugehörige
Einstellungen wie z.B. "Subject" - sind auf der Formularseite am Ende zu finden.

</details>


<details>
<summary>Warum kann ich die Attachments in den Emails nicht abrufen?</summary>

Der Abruf von hochgeladenen Dateien (Dokumente oder Bilder) ist nur über einen
authentifizierten Request möglich. Die Authentifizierung erfolgt entweder über
einen freigegebenen IP-Bereich/-Adresse oder über einen Login im Backend. 

</details>

<details>
<summary>Wie melde ich mich am Backend an?</summary>

Eine beliebige Seite unterhalb von "/admin/" aufrufen und die Login-Seite fragt
die Credentials ab. 

</details>

<details>
<summary>Warum kann ich mich nicht am Backend anmelden?</summary>

Aktuell muss eine bestimmte Gruppenmitgliedschaft (siehe `env.template`) erfüllt
sein, damit ein Login möglich ist. 

</details>

<details>
<summary>Warum sehe ich im Backend keine oder nicht alle Formulare?</summary>

Die Seiten und Funktionen im Backend sind über Permissions eingeschränkt. Diese
Permissions hängen an der Gruppenmitgliedschaft von Usern. 

Jeder User "sieht" z.B. nur die Seiten/Formulare, für die sie oder er
berechtigt ist. 

Weiter sind die Formulare über "Container-Seiten" zusammengefasst, damit über
diese "Container-Seiten" Gruppen-Berechtigungen zugewiesen werden können.

</details>

<details>
<summary>Kann ich ein Captcha für mein Formular haben?</summary>

Ja. Auf der Backendseite eines Formulars in den Reiter "Settings" wechseln und
"Use captcha" aktivieren und die Seite publizieren.

</details>

<details>
<summary>Erhalten User automatisch eine Bestätigungsmail?</summary>

Nein. Das Formulartool kann keine automatischen Bestätigungsemails an User versenden,
da es den User "nicht kennt". Auch wenn in einem Formular ein Feld "Email"
zusammengestellt wurde, weiß das Formulartool nicht, was dieses Feld inhaltlich ausdrückt.

</details>
