
from common.handler import JsonHandler, AuthenticatedHandler
from common.access import scoped, AccessToken

from tornado.gen import coroutine
from tornado.web import HTTPError, stream_request_body

from common.options import options
from common.ratelimit import RateLimitExceeded

from model.report import ReportError, ReportFormat

import ujson


class UploadReportHandler(AuthenticatedHandler):
    @scoped(scopes=["report_upload"])
    @coroutine
    def put(self, application_name, application_version):

        reports = self.application.reports
        account_id = self.token.account
        gamespace_id = self.token.get(AccessToken.GAMESPACE)

        message = self.get_argument("message")
        category = self.get_argument("category")

        report_format = self.get_argument("format")

        if report_format in ReportFormat.ALL:
            report_format = ReportFormat(report_format)
        else:
            raise HTTPError(400, "Unknown report format: '{0}'.".format(report_format))

        try:
            report_info = ujson.loads(self.get_argument("info", "{}"))
        except (KeyError, ValueError):
            raise HTTPError(400, "Corrupted 'info' argument.")

        payload = self.request.body

        try:
            limited = yield self.application.ratelimit.limit("report_upload", account_id)
        except RateLimitExceeded:
            raise HTTPError(429, "Too many report uploads")

        try:
            report_id = yield reports.create_report(
                gamespace_id, account_id, application_name, application_version,
                category, message, report_info, report_format, payload)
        except ReportError as e:
            yield limited.rollback()
            raise HTTPError(e.code, e.message)

        self.dumps({
            "id": report_id
        })
