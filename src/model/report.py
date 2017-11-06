
from tornado.gen import coroutine, Return

from common.model import Model
from common.validate import validate
from common.database import DatabaseError
from common.options import options

from common import Enum

import ujson
import re


class ReportFormat(Enum):
    BINARY = 'binary'
    TEXT = 'text'
    JSON = 'json'

    ALL = {BINARY, TEXT, JSON}


class ReportError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return str(self.code) + ": " + str(self.message)


class ReportAdapter(object):
    def __init__(self, data):
        self.report_id = data.get("report_id")
        self.account_id = data.get("account_id")
        self.application_name = data.get("application_name")
        self.application_version = data.get("application_version")
        self.category = data.get("report_category")
        self.message = data.get("report_message")
        self.info = data.get("report_info")
        self.time = data.get("report_time")
        self.format = ReportFormat(data.get("report_format", "binary").lower())


class ReportPayloadAdapter(ReportAdapter):
    def __init__(self, data):
        super(ReportPayloadAdapter, self).__init__(data)
        self.payload = data.get("report_payload")


class ReportQuery(object):
    def __init__(self, db, gamespace_id, application_name, application_version):
        self.db = db

        self.gamespace_id = gamespace_id
        self.application_name = application_name
        self.application_version = application_version

        self.account_id = None
        self.category = None
        self.message = None
        self.include_payload = False

        self.limit = 0
        self.offset = 0
        self.other_conditions = []
        self.for_update = False

    def add_conditions(self, conditions):

        if not isinstance(conditions, list):
            raise RuntimeError("conditions expected to be a list")

        self.other_conditions.extend(conditions)

    def __values__(self):
        conditions = [
            "`reports`.`gamespace_id`=%s",
            "`reports`.`application_name`=%s",
            "`reports`.`application_version`=%s"
        ]

        data = [
            str(self.gamespace_id),
            self.application_name,
            self.application_version
        ]

        if self.category:
            conditions.append("`reports`.`report_category`=%s")
            data.append(str(self.category))

        if self.message:
            words = re.findall(r'[^\s]+', self.message)

            if words:
                if len(words) > 32:
                    # too many words
                    words = words[:32]

                compiled = u" ".join(u"+" + word + u"*" for word in words if len(word) > 2)
                conditions.append("MATCH(`reports`.`report_message`) AGAINST (%s IN BOOLEAN MODE)")
                data.append(compiled)

        if self.account_id:
            conditions.append("`reports`.`account_id`=%s")
            data.append(str(self.account_id))

        for condition, values in self.other_conditions:
            conditions.append(condition)
            data.extend(values)

        return conditions, data

    @coroutine
    def query(self, one=False, count=False):
        conditions, data = self.__values__()

        fields = "`report_id`, `account_id`, `report_category`, " \
                 "`report_format`, `report_message`, `report_info`, `report_time`"

        if self.include_payload:
            fields += ", `report_payload`"

        query = """
            SELECT {0} {1} FROM `reports`
        """.format(
            "SQL_CALC_FOUND_ROWS" if count else "", fields)

        query += """
            WHERE {0}
        """.format(" AND ".join(conditions))

        if self.limit:
            query += """
                LIMIT %s,%s
            """
            data.append(int(self.offset))
            data.append(int(self.limit))

        if self.for_update:
            query += """
                FOR UPDATE
            """

        query += ";"

        adapter = ReportPayloadAdapter if self.include_payload else ReportAdapter

        with (yield self.db.acquire()) as db:
            if one:
                result = yield db.get(query, *data)

                if not result:
                    raise Return(None)

                raise Return(adapter(result))
            else:
                result = yield db.query(query, *data)

                count_result = 0

                if count:
                    count_result = yield db.get(
                        """
                            SELECT FOUND_ROWS() AS count;
                        """)
                    count_result = count_result["count"]

                items = map(adapter, result)

                if count:
                    raise Return((items, count_result))

                raise Return(items)


class ReportsModel(Model):
    def __init__(self, db):
        self.db = db
        self.max_report_size = options.max_report_size

    def get_setup_tables(self):
        return ["reports"]

    def get_setup_db(self):
        return self.db

    @coroutine
    @validate(gamespace_id="int", account_id="int", application_name="str_name",
              application_version="str", category="str_name", message="str",
              report_info="json_dict", report_format=ReportFormat, report_payload="bytes")
    def create_report(self, gamespace_id, account_id, application_name, application_version,
                      category, message, report_info, report_format, report_payload):

        if len(report_payload) > self.max_report_size:
            raise ReportError(400, "Report maximum size exceeded")

        try:
            report_id = yield self.db.insert(
                """
                    INSERT INTO `reports`
                    (`gamespace_id`, `account_id`, `application_name`, `application_version`, 
                     `report_category`, `report_message`, `report_info`, `report_format`, `report_payload`) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, gamespace_id, account_id, application_name, application_version,
                category, message, ujson.dumps(report_info), str(report_format), report_payload)
        except DatabaseError as e:
            raise ReportError(500, e.args[1])

        raise Return(report_id)

    @coroutine
    @validate(gamespace_id="int", report_id="int")
    def get_report(self, gamespace_id, report_id):
        try:
            report = yield self.db.get(
                """
                    SELECT * FROM `reports`
                    WHERE `gamespace_id`=%s AND `report_id`=%s
                    LIMIT 1;
                """, gamespace_id, report_id)
        except DatabaseError as e:
            raise ReportError(500, e.args[1])

        if not report:
            raise ReportError(404, "No such report")

        raise Return(ReportPayloadAdapter(report))

    @validate(gamespace_id="int", application_name="str_name", application_version="str")
    def reports_query(self, gamespace_id, application_name, application_version):
        return ReportQuery(self.db, gamespace_id, application_name, application_version)
