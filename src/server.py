
from tornado.gen import coroutine
from common.options import options

import common.server
import common.handler
import common.database
import common.access
import common.sign
import common.ratelimit

from common.keyvalue import KeyValueStorage

from model.report import ReportsModel

import handler
import admin
import options as _opts


class ReportServer(common.server.Server):
    def __init__(self):
        super(ReportServer, self).__init__()

        self.db = common.database.Database(
            host=options.db_host,
            database=options.db_name,
            user=options.db_username,
            password=options.db_password)

        self.reports = ReportsModel(self.db, self)
        self.ratelimit = common.ratelimit.RateLimit({
            "report_upload": options.rate_report_upload
        })

        self.cache = KeyValueStorage(
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
            (r"/upload/(.*)/(.*)", handler.UploadReportHandler),
        ]


if __name__ == "__main__":
    stt = common.server.init()
    common.access.AccessToken.init([common.access.public()])
    common.server.start(ReportServer)
