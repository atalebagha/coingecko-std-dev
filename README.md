# TODOs

## Architecture
  - EventBus + Lambda to trigger an event every minute
  - I made a request to an api that returns coin values in USD, so for this case all coins are compared to USD.
  - Coin values are persisted to DynamoDB which triggers an event stream
  - Event stream invokes standard deviation lambda (batched)
  - Time of initial event is persisted throughout the cycle to preserve original time (even though the delay in the stddev calculation)
  - Databases:
      - Historical value database - Internal Records
      - Standard Deviation database - User accessed
      - Latest Update Database (1 record only)
   

## Potential enhancements
  - purge older data
  - Use an API(s) that matches coins with non USD coins
  - Possibly calculate coin comparisons based on USD values instead of invoking another API
  - observability
  - Multiple lambda jobs, rather than 1 lambda invoke to get 250 coins, have multiple invoke at the same time
   
## Scalability:
  - since this is using lambda scalability from the service layer shouldn't be much of an issue
  - Database will grow over time, we need to purge data older than 24 hours to keep the db footprint low and querying fast


## what would you change if you needed to track many other metrics or support every exchange and pair available?
  - multiple lambdas/services that simultaneously fetch coins, that way we won't have an issue of a variance due to time.

## what if you needed to sample them more frequently?
  - I wouldn't use a cron job, just have a continuously active service that runs the request on interval.

## what if you had many users accessing your dashboard to view metrics?
  - We can setup the DB to be multi regional and as long as we purge older data it should be fine with users accessing the Std Deviation data.
  - If the users want to access historical prices for past 24 hours, that might be doable even with the current setup as the partitions and sort keys are setup to be performant to fetch a specific coin pair, sorted by time

## Production Readiness: What would you change or add to make the service production ready?
  - Logging
  - Metrics & Observability
  - I'm fetching all coins, we probably want to fetch specific types of coins etc.
  - DB Backups
  - Authentication

## Testing: how would you extend testing for an application of this kind (beyond what you implemented)?
  - E2E tests to ensure our jobs initiate the data stream from dynamo and create standard deviation data

## Time spent on the assignment and use of coding assistant tools
  - 7-8 hours
  - SST Dev, SST Discord, ChatGPT, StackOverflow
