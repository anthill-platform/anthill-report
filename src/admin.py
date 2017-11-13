
from tornado.gen import coroutine, Return

import common.admin as a

from common.validate import validate
from common.environment import AppNotFound
from common.database import format_conditions_json, ConditionError

from model.report import ReportError, ReportFormat

import ujson
import math
import csv
import StringIO
import base64


class RootAdminController(a.AdminController):
    def render(self, data):
        return [
            a.breadcrumbs([], "Reports"),
            a.links("Navigate", [
                a.link("apps", "Applications", icon="mobile")
            ])
        ]

    def access_scopes(self):
        return ["report_admin"]


class ApplicationsController(a.AdminController):
    @coroutine
    def get(self):
        env_service = self.application.env_service
        apps = yield env_service.list_apps()

        result = {
            "apps": apps
        }

        raise a.Return(result)

    def render(self, data):
        return [
            a.breadcrumbs([
                a.link("index", "Reports")
            ], "Applications"),
            a.links("Select application", links=[
                a.link("app", app_title, icon="mobile", app_name=app_name)
                for app_name, app_title in data["apps"].iteritems()
            ]),
            a.links("Navigate", [
                a.link("index", "Go back", icon="chevron-left"),
                a.link("/environment/apps", "Manage apps", icon="link text-danger"),
            ])
        ]

    def access_scopes(self):
        return ["report_admin"]


class ApplicationController(a.AdminController):
    @coroutine
    def get(self, app_name):

        env_service = self.application.env_service

        try:
            app = yield env_service.get_app_info(app_name)
        except AppNotFound as e:
            raise a.ActionError("App was not found.")

        app_versions = app["versions"].keys()
        app_versions.sort()

        result = {
            "app_name": app_name,
            "app_title": app["title"],
            "app_record_id": app["id"],
            "versions": app_versions
        }

        raise a.Return(result)

    def render(self, data):

        app_name = self.context.get("app_name")

        return [
            a.breadcrumbs([
                a.link("index", "Reports"),
                a.link("apps", "Applications"),
            ], data["app_title"]),
            a.links("Application '{0}' versions".format(data["app_name"]), links=[
                a.link("app_version", v_name, icon="tags", app_name=app_name,
                       app_version=v_name) for v_name in data["versions"]
            ]),
            a.links("Navigate", [
                a.link("apps", "Go back", icon="chevron-left"),
                a.link("/environment/app", "Manage app '{0}' at 'Environment' service.".format(data["app_title"]),
                       icon="link text-danger", record_id=data["app_record_id"]),
            ])
        ]

    def access_scopes(self):
        return ["report_admin"]


class ReportController(a.AdminController):
    @coroutine
    def get(self, report_id, download=False):
        env_service = self.application.env_service
        reports = self.application.reports

        try:
            report = yield reports.get_report(self.gamespace, report_id)
        except ReportError as e:
            raise a.ActionError(e)

        app_name = report.application_name
        app_version = report.application_version

        if download:
            if report.format == ReportFormat.TEXT:
                ext = ".txt"
            elif report.format == ReportFormat.JSON:
                ext = ".json"
            else:
                ext = ".data"

            raise a.BinaryFile(report.payload,
                               name="report_" + str(report.report_id) + "_" + str(app_name) +
                                    "_" + str(app_version) + ext)

        try:
            app = yield env_service.get_app_info(app_name)
        except AppNotFound as e:
            app_title = app_name
        else:
            app_title = app["title"]

        raise Return({
            "account_id": report.account_id,
            "app_name": app_name,
            "app_version": app_version,
            "app_title": app_title,
            "category": report.category,
            "message": report.message,
            "info": report.info,
            "time": str(report.time),
            "format": report.format,
            "format_title": str(report.format).upper(),
            "payload": report.payload
        })

    def render(self, data):
        r = [
            a.breadcrumbs([
                a.link("index", "Reports"),
                a.link("apps", "Applications"),
                a.link("app", data["app_title"], app_name=data["app_name"]),
                a.link("app_version", data["app_version"], app_name=data["app_name"], app_version=data["app_version"]),
            ], "Report {0}".format(self.context.get("report_id")))
        ]

        report_format = data["format"]

        if report_format == ReportFormat.JSON:
            r.append(a.form("Contents", fields={
                "payload": a.field("Report Contents", "json", "primary", height=400, parse=True)
            }, methods={}, data=data))

        elif report_format == ReportFormat.TEXT:
            r.append(a.form("Contents", fields={
                "payload": a.field("Report Contents", "text", "primary", multiline=20)
            }, methods={}, data=data))

        r.extend([
            a.links("Download", [
                a.link("report", "Download the Report", icon="download", report_id=self.context.get("report_id"),
                       download=True)
            ]),
            a.form("Report Information", fields={
                "account_id": a.field("Reporter Account", "text", "primary", order=1),
                "category": a.field("Report Category", "status", "default", order=2),
                "message": a.field("Report Message", "text", "primary", multiline=3, order=3),
                "info": a.field("Report Info", "json", "primary", height=140, order=4),
                "time": a.field("Report Time", "text", "primary", order=5),
                "format_title": a.field("Report Format", "text", "primary", order=6)
            }, methods={}, data=data),
            a.links("Navigate", [
                a.link("app_version", "Go back", icon="chevron-left", app_name=data["app_name"])
            ])
        ])

        return r


class ApplicationVersionController(a.AdminController):
    REPORTS_PER_PAGE = 20

    @coroutine
    def get(self, app_name, app_version, page=1,
            info=None,
            account_id=None,
            report_message=None,
            category=None,
            export=False):

        env_service = self.application.env_service
        reports = self.application.reports

        try:
            app = yield env_service.get_app_info(app_name)
        except AppNotFound as e:
            raise a.ActionError("App was not found.")

        versions = app["versions"]

        if app_version not in versions:
            raise a.ActionError("No such app version")

        query = reports.reports_query(self.gamespace, app_name, app_version)

        if export:
            query.offset = 0
            query.limit = 10000
            query.include_payload = True
        else:
            query.offset = (int(page) - 1) * ApplicationVersionController.REPORTS_PER_PAGE
            query.limit = ApplicationVersionController.REPORTS_PER_PAGE

        if account_id:
            query.account_id = str(account_id)

        if report_message:
            query.message = str(report_message)

        if category:
            query.category = str(category)

        if info:
            try:
                info = ujson.loads(info)
            except (KeyError, ValueError):
                raise a.ActionError("Corrupted info")

            try:
                cond = format_conditions_json('report_info', info)
            except ConditionError as e:
                raise a.ActionError(e.message)

            query.add_conditions(cond)
        else:
            info = {}

        if export:
            reports = yield query.query(one=False, count=False)

            output = StringIO.StringIO()
            data = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

            data.writerow(["Report ID", "Category", "Message", "Sender", "Info", "Time", "Format", "Contents"])

            for report in reports:
                if report.format == ReportFormat.BINARY:
                    contents = base64.b64encode(report.payload)
                else:
                    contents = str(report.payload)

                data.writerow([
                    str(report.report_id),
                    str(report.category),
                    str(report.message),
                    str(report.account_id),
                    str(ujson.dumps(report.info)),
                    str(report.time),
                    str(report.format),
                    contents
                ])

            raise a.BinaryFile(output.getvalue(), "reports.csv")

        reports, count = yield query.query(one=False, count=True)
        pages = int(math.ceil(float(count) / float(ApplicationVersionController.REPORTS_PER_PAGE)))

        raise Return({
            "app_name": app_name,
            "app_title": app["title"],
            "app_record_id": app["id"],
            "reports": reports,
            "account_id": account_id,
            "report_message": report_message,
            "category": category,
            "info": info,
            "pages_count": pages,
            "total_count": count
        })

    @coroutine
    def clear_filters(self, **args):

        app_name = self.context.get("app_name")
        app_version = self.context.get("app_version")

        raise a.Redirect("app_version", app_name=app_name, app_version=app_version)

    @coroutine
    def filter(self, **args):

        app_name = self.context.get("app_name")
        app_version = self.context.get("app_version")

        page = self.context.get("page", 1)

        filters = {
            "app_name": app_name,
            "app_version": app_version,
            "page": page
        }

        filters.update(args)
        raise a.Redirect("app_version", **filters)

    @coroutine
    def export_reports(self, **args):

        app_name = self.context.get("app_name")
        app_version = self.context.get("app_version")

        page = self.context.get("page", 1)

        filters = {
            "app_name": app_name,
            "app_version": app_version,
            "page": page,
            "export": True
        }

        filters.update(args)
        raise a.Redirect("app_version", **filters)

    def render(self, data):

        reports = [
            {
                "see": [
                    a.link("report", str(r.report_id), icon="flag", report_id=r.report_id)
                ],
                "account_id": [
                    a.link("app_version", str(r.account_id), icon="filter", app_name=self.context.get("app_name"),
                           app_version=self.context.get("app_version"), account_id=r.account_id)
                ],
                "message": r.message,
                "category": [
                    a.link("app_version", str(r.category), icon="filter", app_name=self.context.get("app_name"),
                           app_version=self.context.get("app_version"), category=r.category)
                ],
                "info": [
                    a.json_view(r.info)
                ],
                "time": str(r.time)
            }
            for r in data["reports"]
        ]

        methods = {
            "filter": a.method("Filter reports", "primary", order=1),
            "export_reports": a.method("Export reports to CSV", "default", icon="download", order=3),
        }

        if self.context.get("account_id") or self.context.get("info"):
            methods["clear_filters"] = a.method("Clear filters", "default", order=2)

        r = [
            a.breadcrumbs([
                a.link("index", "Reports"),
                a.link("apps", "Applications"),
                a.link("app", data["app_title"], app_name=self.context.get("app_name")),
            ], self.context.get("app_version")),

            a.content("Reports: {0} total".format(data["total_count"]), [
                {
                    "id": "see",
                    "title": "See"
                }, {
                    "id": "message",
                    "title": "Report Message"
                }, {
                    "id": "category",
                    "title": "Report Category"
                }, {
                    "id": "account_id",
                    "title": "Reporter"
                }, {
                    "id": "info",
                    "title": "Report info"
                }, {
                    "id": "time",
                    "title": "Report Time"
                }], reports, "default", empty="No reports to display")
        ]

        if data["pages_count"]:
            r.append(a.pages(data["pages_count"]))

        r.extend([
            a.form("Filters", fields={
                "account_id": a.field("Reporter Account", "text", "primary", order=1),
                "report_message": a.field("Report Message", "text", "primary", order=2),
                "category": a.field("Report Category", "text", "primary", order=3),
                "info": a.field("Report Info", "json", "primary", order=4, height=120),
            }, methods=methods, data=data, icon="filter"),

            a.links("Navigate", [
                a.link("app", "Go back", icon="chevron-left", app_name=self.context.get("app_name"))
            ])
        ])

        return r
