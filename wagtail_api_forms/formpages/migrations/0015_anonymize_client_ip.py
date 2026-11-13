import ipaddress

from django.db import migrations


def _anonymize_ip(ip):
    # A copy of formpages.utils.anonymize_ip, so this migration keeps working
    # whatever happens to the app code
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped
    prefix = 24 if address.version == 4 else 48
    return str(ipaddress.ip_network(f"{address}/{prefix}", strict=False).network_address)


def anonymize_client_ips(apps, schema_editor):
    """Shorten the IP addresses stored before submissions stored them shortened."""
    CustomFormSubmission = apps.get_model("formpages", "CustomFormSubmission")
    changed = []
    submissions = (
        CustomFormSubmission.objects.exclude(client_ip=None)
        .only("pk", "client_ip")
        .iterator()
    )
    for submission in submissions:
        anonymized = _anonymize_ip(submission.client_ip)
        if anonymized != submission.client_ip:
            submission.client_ip = anonymized
            changed.append(submission)
    CustomFormSubmission.objects.bulk_update(changed, ["client_ip"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("formpages", "0014_formpage_show_results"),
    ]

    operations = [
        # The full addresses are gone for good: there is nothing to reverse
        migrations.RunPython(anonymize_client_ips, migrations.RunPython.noop),
    ]
