# Get some data by telling app_server to get data from ref_server to S3. Check only status code:
curl  -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8080/process-request?date=2024-05-01"
curl  -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8080/process-request?date=2024-05-02"
curl  -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8080/process-request?date=2024-05-04"
curl  -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8080/process-request?date=2024-05-05"

# Get statistics from app_server. See full json response:
curl -s -X GET "http://127.0.0.1:8080/country-stats?from=2024-05-02&to2024-05-04"
# To easily parse json response, you can send this last request from browser.