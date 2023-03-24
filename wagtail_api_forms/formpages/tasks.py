from huey.contrib.djhuey import db_task
# from django.db.models.functions import Now
from django.utils import timezone


@db_task()
def schedule_virusscan(attachment_id):
    print(f"Huey task schedule_virusscan: Scan for virus for attachment with pk {attachment_id}...")

    from .models import Attachment
    from .validators import av_scan

    # This task executes queries. Once the task finishes, the connection
    # will be closed.

    attachment_qs = Attachment.objects.filter(id=attachment_id)
    model_inst = attachment_qs.get()  # There could only be one item in this qs
    av_scan_result = av_scan(model_inst.file)
    av_scanned_at = timezone.now()  # Now()
    av_passed = False
    av_reason = None

    """
    Possible return values for av_scan: 
    1. virus found:
       {'stream': ('FOUND', 'Win.Test.EICAR_HDB-1')}
    2. no virus found:
       None
    """

    if av_scan_result:
        av_passed = False
        av_reason = av_scan_result
    else:
        av_passed = True

    print(f"av_passed: {av_passed}; av_scanned_at: {av_scanned_at}; av_reason: {av_reason}")

    attachment_qs.update(
        av_scanned_at=av_scanned_at,
        av_passed=av_passed,
        av_reason=av_reason,
    )
