import logging

from huey.contrib.djhuey import db_task
from django.utils import timezone


logger = logging.getLogger(__name__)


@db_task(retries=3, retry_delay=30)
def schedule_virusscan(attachment_id):
    """
    Background virus scan for an uploaded Attachment.

    Updates the attachment row via .update() (not .save()) to avoid
    re-triggering Attachment.save()'s scheduling hook.

    Possible av_scan return values:
      - virus found:   {'stream': ('FOUND', '<signature>')}
      - clean:         None
      - transport error: raises -> Huey retries
    """
    from .models import Attachment
    from .validators import av_scan

    logger.info("Huey: starting virus scan for attachment %s", attachment_id)

    attachment_qs = Attachment.objects.filter(id=attachment_id)
    model_inst = attachment_qs.get()

    av_scanned_at = timezone.now()
    av_passed = False
    av_reason = None

    try:
        av_scan_result = av_scan(model_inst.file)
    except Exception as exc:
        # Let Huey retry (decorator above); persist a reason so an
        # operator can spot stuck attachments without log-spelunking.
        logger.exception(
            "Huey: AV scan errored for attachment %s", attachment_id
        )
        attachment_qs.update(
            av_scanned_at=av_scanned_at,
            av_passed=False,
            av_reason=f"scan_error: {exc}"[:255],
        )
        raise

    if av_scan_result:
        av_passed = False
        av_reason = str(av_scan_result)[:255]
        logger.warning(
            "Huey: AV scan FOUND for attachment %s: %s",
            attachment_id,
            av_reason,
        )
    else:
        av_passed = True
        logger.info("Huey: AV scan clean for attachment %s", attachment_id)

    attachment_qs.update(
        av_scanned_at=av_scanned_at,
        av_passed=av_passed,
        av_reason=av_reason,
    )
