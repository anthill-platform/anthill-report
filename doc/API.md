## Upload a Report

Uploads a Report to the service, returning the report ID.

#### ← Request

```rest
PUT /upload
```

File body should be passed as `PUT` request contents, other arguments should be passed
as query arguments.

| Argument         | Description                        |
|------------------|------------------------------------|
| `message`        | A string message relating to the report. Can be used for full-text search. |
| `category`       | Report category (string). For example, `cheater`, `crash`, etc. |
| `format`         | Report content format. Could be `json`, `text`, or `binary`. |
| `info`           | JSON Object with information about report (used to filter reports out). |
| `access_token`   | A valid `AccessToken` with `report_upload` scope. |
| `<Request Body>` | Report contents (either file, text or json document, depending on the `format`. |

#### → Response

In case of success, a JSON object with report ID is returned:
```json
{
    "id": "12345"
}
```

