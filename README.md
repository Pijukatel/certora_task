# certora_task
Hiring task for certora

# Assignment description:
We want to create an application to process data from an external HTTP server on user request and save them to S3 for further processing & serving. Processing will begin with the user calling the `POST /process-request?date=<date>` API which will register a task to gather data from the reference server about all available cities on the selected date. Afterward, the user can call the `GET /country-stats?from=<date>&to<date>` API that will read the data from S3 and return statistics per country and day, how many busses started, what is the total amount of passengers, if there was an accident that day, and what was the average delay. When implementing these APIs let's imagine that they should be used "infrequently" (thus processing files from S3 rather than DB) and the amount of data per file should be >>100 MB but still procassable in memory. Also, we know that this application should be running in production for several years.

Additional assignment notes:
- Use a git repository hosted on GitHub (please add me there as a collaborator https://github.com/H00N24)
- Use mocked S3 using Moto (https://github.com/getmoto/moto)
- Apply modern best practices for Python
- Add simple CI for verifying these practices and tests
- Simple docker file for deployment


# Notes and comments about the implementation.
How to Use:
- Install poetry. 
- Clone repo.
- run "poetry install" from the repo folder
- use poetry to run tests, ruff or mypy. For detailed commands see **check.sh** (used for local development) or see **.github\workflows\Check.yml** which is used in CI
- Can work in different os types and versions, but CI is using only one docker image to verify it. See **dockerfile**
- Demo deployment on local machine by using docker compose and hosting app_server on localhost:8080 which is exposed. Both mocked_moto and ref_server are not exposed outside of containers.\
To see example deployment and example use case and run:
  - **demo_setup.sh** in one console to create docker image, run docker_compose and see compose logs
  - **demo_example_requests.sh** in another console to send some example requests

Design comments:
- Data in S3 is structured in buckets named after countries and following keys {date}/{city}
- Each raw file is uploaded to S3 with precalculated stats saved in file's Metadata to make further processing faster.
- Aggregated stats per country per date (if already computed) are stored in S3 {date}/{aggregated_stats_file_name}
- Aggregated stats are calculated only if they don't already exist as consequence of previous requests.
- If new data is uploaded, then connected aggregated data is no longer valid, and it's file is deleted from s3. It will have to be recreated from new inputs.
- mocked_moto.py contains dummy S3 server that works with async requests locally. Used both in tests and demo.

Basic CI ensures following:
- Running unit tests through Pytest
- Static type checks through mypy
- Linting and formatting using Ruff
Checks are used in the default way and further customization would be possible if some specific code standards are required.
- Working environment and docker image build. (Deployment is not in the scope of this task, so docker image is not uploaded to any repository.)

# Out of scope improvements:
- Handling race conditions in concurrent requests for new data and aggregated results.
  - Current implementation will leave such behavior as undefined with high probability of failed request and issue will be mentioned here as documentation.
  - Could be prevented by creating data locks on specific portion of S3 keys that can be either used for updates or for aggregation. But never both at the same time.
- Proper app deployment configuration.
  - Deployment is out of scope of the assignment and currently only simle hardcoded strings in configuration file are used.
- Requests throttling. In case of too frequent /process-request some limit could be imposed. For example using simple semaphore from asyncio.
- Input data validation.
  - If data is from external server, then it should be validated against our expectations. In current implementation placeholder function.
- Checksum based data updates.
  - Some data from reference server can be identical to what is already saved in S3 (for example old historical data that will never be updated again). To prevent expensive data transfer, some checksum of data could be saved in S3 metadata and compared to "new" data checksum and overwrite S3 only if checksum differs.
- Splitting CI to purely code change or environment change:
  - Environment change is either pure CI change or mixed (code + CI) change:
    - Condition: If change changes any poetry related files like pyproject.toml, poetry.lock, any workflow files
    - Action: Run full scope (docker image build + all checks. Same as current version of Basic CI). If successful, upload docker image to specified image repository.
  - Pure code:
    - Condition: Only files in src or test folder were edited
    - Action: Download latest verified environment docker image from repository and run only checks (pytest, mypy, ruff). Checks could be run in parallel if time optimization is needed.

