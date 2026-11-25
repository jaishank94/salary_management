# Tradeoffs

## One currency per country

Averaging US dollars with rupees produces a number nobody can use. Salaries are stored in the country's currency, and every insight is grouped by country and currency. Changing an employee's country does not convert the amount; the form says so. Live foreign-exchange rates were rejected because they would make yesterday's average move without anyone's pay changing. The seed uses a static pay index only to invent plausible local amounts.

## Decimal math instead of SQLite AVG

SQLite `SUM` and `AVG` are floating point. At 10,000 employees the salary column for one country is small, so the service loads those values and aggregates with `Decimal`. That keeps half-up rounding exact. The directory list does not load the whole table: it is filtered, sorted, and paginated in SQL. If the workforce grew past a few hundred thousand rows, the next step would be integer cents and SQL aggregates, not a bigger in-process list.

## Who is in an average

Terminated people are excluded by default. They are still counted in the workforce and can be included with one switch. On-leave employees remain in the average because they are still employed.

## Median and percentiles

Median uses the average of the two middle values when the count is even, which is what HR readers expect. Percentiles use nearest rank, which is stable and does not invent a salary between two people. The two definitions are labeled in the UI.

## Seed performance

The script builds rows in memory from `data/first_names.txt` and `data/last_names.txt`, then inserts them in chunks of 400 inside one transaction. File databases used by the CLI also set `synchronous=OFF` for that load only; the API does not. Generation of 10,000 rows is tested under 2 seconds and the insert under 10. Re-running without `--reset` refuses to overwrite, because a regular refresh should be explicit.

## Authentication

The assessment does not ask for sign-in. Adding a decorative login would imply a control that does not exist. The sidebar says this is a demo workspace and real employee data should stay out. A production deployment would put SSO in front of this service without changing the salary rules.

## Stack

The brief allows the stack from the job description or another choice. This solution uses FastAPI, SQLAlchemy, and SQLite on the server, and React with Vite on the client. SQLite is enough for 10,000 employees and keeps the app one process. The schema is ordinary SQLAlchemy, so Postgres is a connection-string change plus a migration, not a rewrite.
