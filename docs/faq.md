# FAQ

<style>
details {
  box-shadow: 0 .2rem .5rem rgba(0,0,0,.05),0 0 .0625rem rgba(0,0,0,.1);
  border-radius: .2rem;
  padding: 0.5rem;
  margin-bottom: 1em;
  /* font-size: var(--admonition-font-size); */
}
</style>

```{include} snippets/wiphint.md
```

```{admonition} Multilanguage
   The backend is available in many languages and can be set via the account settings (bottom left).  For this documentation the English identifiers are used.
```

## Allgemein

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
<summary>Formular bearbeiten</summary>

Über das "Seiten"/"Pages"-Menü zum Formular navigieren und im Menü das
Bleistift/Pencil-Icon nutzen. Die Bearbeiten-Funktionalität steht wird noch an
weiteren Stellen im System - oftmals über ein *Drei-Punkte-Menü* - angeboten.

</details>

<details>
<summary>Wie kann ich ein Formular testen?</summary>

So lange Sie niemanden den "Link" des veröffentlichten Formulars mitteilen, können Sie - und jede*r andere die/der diesen Link kennt - das Formular testen.

Weiter gibt es noch die Option, ein Formular bzw. eine Seite nur für einen eingeschränkten Benutzerkreis zugänglich zu machen:

*Formular > Status > Privatssphäre ändern*:

- Privat, nur für angemeldete Benutzer einsehbar
- Privat, einsehbar mit folgendem Passwort

</details>

<details>
<summary>Übersetzung für Formular anlegen</summary>

Für eine existierende Formular-Seite kann eine Übersetzung angelegt werden: Via
"Translate" im Seiten-Actions-Menü. Hierbei wird im entsprechenden Seitenbaum
der anderen Sprache eine Kopie dieser Seite mit den ursprünglichen Inhalten
angelegt. Diese Inhalte auf der neuen Seite sind dann manuell zu übersetzen/überschreiben.

</details>

<details>
<summary>Was ist beim Kopieren einer Seite zu beachten?</summary>

Nach dem Kopieren eines Formular sollte der *slug/Kurztitel* geprüft und angepasst werden:  
*Formular > Promote/Veröffentlichung > Slug/Kurztitel*

</details>

## Features

<details>
<summary>Was bedeuten die Einstellmöglichkeiten für die Felder?</summary>

Siehe [Felder](fields.md).

</details>

<details>
<summary>Kann ich ein Captcha für mein Formular haben?</summary>

Ja. Auf der Backendseite eines Formulars in den Reiter "Settings" wechseln und
"Use captcha" aktivieren und die Seite publizieren.

</details>

## Formular-Einsendungen

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
<summary>Wie erhalte ich eine Nachricht wenn ein Formular abgesendet wird?</summary>

Grundsätzlich werden alle Formular-Einsendungen im System gespeichert (siehe nächster FAQ-Punkt).

Zusätzlich kann eine Email mit den Formulardaten bei jeder Einsendung versendet werden. Hierzu
tragen Sie im Formular-Backend im Feld "An-Adresse" die von Ihnen gewünschte Empfänger-Emailadresse sowie einen einen Betreff im Feld "Betreff" ein. Der Betreff ist für für alle Einsendungen dieses Formulars identisch und kann z.B. für eine Emailpostfach-Eingangsregel genutzt werden.

</details>

<details>
<summary>Wo kann ich alle Einsendungen eines Formulars sehen?</summary>

Auf der Formular-Backend-Seite sind die "Form page submissions" direkt unter dem Formulartitel mit der Anzahl der gesamten Einsendungen sowie dem Datum der letzten Einsendung verlinkt.

Auf der verlinkten Seite der Formular-Einsendungen besteht die Möglichkeit die Einsendungen in einer tabellarischen Darstellung zu prüfen, nach Datum zu filtern oder sie im Excel-Format zu exportieren.

</details>

<details>
<summary>Erhalten User automatisch eine Bestätigungsmail?</summary>

Nein. Das Formulartool kann keine automatischen Bestätigungsemails an User versenden,
da es den User "nicht kennt". Auch wenn in einem Formular ein Feld "Email"
zusammengestellt wurde, weiß das Formulartool nicht, was dieses Feld inhaltlich ausdrückt.

</details>

## Anmeldung und Berechtigungen

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
<summary>Warum kann ich die Attachments in den Emails nicht abrufen?</summary>

Der Abruf von hochgeladenen Dateien (Dokumente oder Bilder) ist nur über einen
authentifizierten Request möglich. Die Authentifizierung erfolgt entweder über
einen freigegebenen IP-Bereich/-Adresse oder über einen Login im Backend.

</details>

<details>
<summary>Wie kann ich andere Dateitypen für ein Dokumenten-Upload-Feld erlauben?</summary>

Pro Formular - nicht per Feld - können Dateitypen bestimmt werden, die für den
Dokument-Upload akzeptiert werden. Das entsprechende Feld ist *Seite > Einstellungen >  Allowed document file types*.  
Dieses Feld ist ausschließlich für Administratoren sichtbar.

</details>
