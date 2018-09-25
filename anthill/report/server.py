
from anthill.common.options import options
from anthill.common import server, handler, database, access, sign, ratelimit, keyvalue

from . import handler as h
from . import options as _opts
from . model.report import ReportsModel
from . import admin


class ReportServer(server.Server):
    def __init__(self):
        super(ReportServer, self).__init__()

        self.db = database.Database(
            host=options.db_host,
            database=options.db_name,
            user=options.db_username,
            password=options.db_password)

        self.reports = ReportsModel(self.db, self)
        self.ratelimit = ratelimit.RateLimit({
            "report_upload": options.rate_report_upload
        })

        self.cache = keyvalue.KeyValueStorage(
            host=options.cache_host,
            port=options.cache_port,
            db=options.cache_db,
            max_connections=options.cache_max_connections)

    def get_models(self):
        return [self.reports]

    def get_admin(self):
        return {
            "index": admin.RootAdminController,
            "apps": admin.ApplicationsController,
            "app": admin.ApplicationController,
            "app_version": admin.ApplicationVersionController,
            "report": admin.ReportController,
        }

    def get_metadata(self):
        return {
            "title": "Report",
            "description": "User-submitted reports service",
            "icon": "flag"
        }

    def get_handlers(self):
        return [
            (r"/upload/(.*)/(.*)", h.UploadReportHandler),
        ]


if __name__ == "__main__":
    stt = server.init()
    access.AccessToken.init([access.public()])
    server.start(ReportServer)
