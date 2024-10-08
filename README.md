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

Basic CI ensures following:
- Running unit tests through Pytest
- Static type checks through mypy
- Linting and formatting using Ruff
Checks are used in the default way and further customization would be possible if some specific code standards are required.
- Working environment and docker image build. (Deployment is not in the scope of this task, so docker image is not uploaded to any repository.)

Out of scope improvements:
- Splitting CI to purely code change or environment change:
  - Environment change is either pure CI change or mixed (code + CI) change:
    - Condition: If change changes any poetry related files like pyproject.toml, poetry.lock, any workflow files
    - Action: Run full scope (docker image build + all checks. Same as current version of Basic CI). If successful, upload docker image to specified image repository.
  - Pure code:
    - Condition: Only files in src or test folder were edited
    - Action: Download latest verified environment docker image from repository and run only checks (pytest, mypy, ruff). Checks could be run in parallel if time optimization is needed.

