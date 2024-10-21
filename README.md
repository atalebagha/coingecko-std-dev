# TODOs

## Architecture

The architecture in this project relies on managed services, mainly EventBus, Lambda and DynamoDB.  It take's advantage of DynamoDB streams to calculate standard deviation of coins in streams, which are triggered by write events.  Initially, the EventBus has a cron job setup at 1 minute intervals, which triggers a Lambda (Price Fetcher) to fetch coingecko prices and then write them to the Price History Table, which has a Write Stream attached to it.  That stream triggers the Standard Deviation Lambda which calculates the standard deviation based on the last 24 hours of data, and it is handled in batches (currently set at 10).  The Standard Deviation lambda stores the currently calculated Standard Deviation of each coin pair in the Standard Deviation Table where the partition key is the updatedAt and the sort key is Standard Deviation value.  This allows for quick querying of the sorted list of coins based off Standard Deviation ranking.  In order to handle the latency in the stream (as some coins will be updated at slightly different times), the updatedAt value is calculated once at the Price Fetcher lambda, stored in a table and passed/queried throughout the process so that coins can be grouped by a specific timestamp, rather than all having unique timestamps.  

#### List of Architectural Components

  - **EventBus** to trigger the Price Fetcher job at 1 minute intervals
  - **Price Fetcher Lambda** which fetches the coin prices (currently all are paired with USD)
  - **DynamoDB**
    - _Pricing History_
      - Partition key is set as the coin pair `<coin1>/<coin2>`
      - Sort key is set as price
        - this PK and SK will make queries per coin pairs faster and sorted by time, which is what we want
      -  **DynamoDB Stream** which triggers the Standard Deviation Lambda
    - _Standard Deviation Table_
      - This table stores the standard deviation calculated per coin
        - PK is set to updatedAt
        - SK is set to standard deviation value
          - This is so we can grab all coin pairs updated at a specific time and sort them by the standard deviation value
    - _UpdatedAt table_
      - This table has a single record which is the latest updated at value to track, so that we can query the Standard Deviation Table based off of updated at time (which is the sort key in that table)
  - **Standard Deviation lambda** is triggered once a bulk of items are written to the Pricing History table via the dynamodb stream on the Pricing Table
  - **Api Handler Lambda** which handles the requests to get standard deviation details
  - **Api Gateway** which is the public facing gateway for the Api Handler Lambda and to fetch coin details

#### Architectural Diagram
   
<img width="1138" alt="Screenshot 2024-10-21 at 10 55 00 AM" src="https://github.com/user-attachments/assets/8a4d76ec-aebf-469f-84fc-ed8b9352d9db">

## Potential enhancements
  - purge or archive older data in Price History and Standard Deviation Table, or have two separate datbases, one for current data which is highly performant, and one as record history, higher integrity and availability.
  - Use CoinGecko API(s) that matches coins with non USD coins
  - Possibly calculate coin comparisons based on USD values
  - Adding Observability and metrics
  - Logging
  - Setting up concurrency for lambdas
  - Multi Region DynamoDB for enhanced performance
   
## Scalability:
  - since this is using lambda scalability from the service layer shouldn't be much of an issue.  We may need to fine tune our lambda and properly set concurrency, memmory, regions etc.
  - We are using managed service so some of the scalability issues are handled for us.
  - If it was a non managed service using ECS, we would definitely need to setup some auto scaling policy, and on the DB side redundancy and relying on multiple db technologies (ex. Redis for current data, and another database for historical records)


## what would you change if you needed to track many other metrics or support every exchange and pair available?
  - multiple lambdas/services that simultaneously fetch coins, that way we won't have an issue of a variance due to time.
  - I'd consider having a separate service for each exchange and/or each metric, since much of this data is time sensitive
    - The only exception would be if a specific API gives us multiple metrics we can use the same layer that fetches, but probably push each metric to it's own service layer downstream to isolate any dependencies

## what if you needed to sample them more frequently?
  - I wouldn't use a cron job, just have a continuously active service that runs the request on interval.
  - Consider using a coin service that offers websocket or server side events.

## what if you had many users accessing your dashboard to view metrics?
  - We can setup the Standard Deviation DB to be multi regional and as long as we purge older data it should be okay with users accessing the Std Deviation data.
  - Api Gateway and lambdas can also be multi regional and we can setup Route53 to route to the closest gateway to that user.
  - If the users want to access historical prices for past 24 hours, that might be doable even with the current setup as the partitions and sort keys are setup to be performant to fetch a specific coin pair, sorted by time

## Production Readiness: What would you change or add to make the service production ready?
  - Logging
  - Metrics & Observability
  - Multiple Regions
  - Service level alarms in case a service goes down
  - Health checks
  - Fallback plan in case AWS region becomes unavailable
  - Failure plan in case CoinGecko becomes unavailable
  - DB Backups
  - Authentication
  - Have a migration plan to move away from Lambda.  Lambda is a good start, but if we want this service to be continuously sampling pricing data, a service would be better.
  - Consider an Coin API that provides streaming data of coin information, so we are not pulling on interval, so that we are continuously connected
    - Consider APIs that have websocket or server side event.  Something like [this](https://docs.coinapi.io/market-data/how-to-guides/real-time-trades-stream-using-websocket-with-different-languages#python-example)
      - Note: I've never used coinapi before, it would need some more research if it's feasible

## Testing: how would you extend testing for an application of this kind (beyond what you implemented)?
  - E2E tests to ensure our jobs initiate the data stream from dynamo and create standard deviation data
  - Unit/Integration Tests
  - Load testing
  - Proper pipelines setup to run these tests appropriately (Unit & integration at PR level, E2E before or after merge or deployment)

## Time spent on the assignment and use of coding assistant tools
  - 7-8 hours
  - SST Dev, SST Discord, ChatGPT, StackOverflow
