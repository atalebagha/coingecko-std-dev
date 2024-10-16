import { StartingPosition } from "aws-cdk-lib/aws-lambda";
import {
  StackContext,
  Api,
  EventBus,
  Table,
  Cron,
  Queue,
} from "sst/constructs";

export function API({ stack }: StackContext) {
  const priceTable = new Table(stack, "PairPrice", {
    fields: {
      pair: "string",
      value: "number",
      time: "number",
    },
    primaryIndex: { partitionKey: "pair", sortKey: "time" },
    globalIndexes: {
      pairTimeIndex: {
        partitionKey: "pair",
        sortKey: "time",
        projection: "all",
      },
      pairIndex: {
        partitionKey: "pair",
        projection: "all",
      },
    },
    stream: "new_image",
  });

  const latestUpdateTable = new Table(stack, "LatestUpdate", {
    fields: {
      id: "string",
    },
    primaryIndex: { partitionKey: "id" },
  });

  const stdDevTable = new Table(stack, "StdDeviationTable", {
    fields: {
      pair: "string",
      stddev: "number",
      updateBatch: "number",
    },
    primaryIndex: { partitionKey: "updateBatch", sortKey: "pair" },
    globalIndexes: {
      stdDevIndex: {
        partitionKey: "updateBatch",
        sortKey: "pair",
        projection: "all",
      },
      StdDevIndex: {
        partitionKey: "updateBatch",
        sortKey: "stddev",
        projection: "all",
      },
    },
  });

  const priceFetcherJob = new Cron(stack, "PriceFetchJob", {
    schedule: "rate(1 minute)",
    job: {
      function: {
        bind: [priceTable, latestUpdateTable],
        handler: "packages/functions/src/pricefetcher.handler",
        runtime: "python3.12",
        environment: {
          TABLE_NAME: priceTable.tableName,
          LATEST_UPDATE_TABLE_NAME: latestUpdateTable.tableName,
          API_KEY: process.env.API_KEY!,
        },
      },
    },
  });

  const api = new Api(stack, "api", {
    defaults: {
      function: {
        bind: [priceTable, stdDevTable, latestUpdateTable],
      },
    },
    routes: {
      "GET /coin-pairs": {
        function: {
          handler: "packages/functions/src/api.handler",
          runtime: "python3.12",
          environment: {
            PRICE_TABLE_NAME: priceTable.tableName,
            LATEST_UPDATE_TABLE_NAME: latestUpdateTable.tableName,
            STDDEV_TABLE_NAME: stdDevTable.tableName,
          },
        },
      },
      "GET /coin-pairs/:pair": {
        function: {
          handler: "packages/functions/src/api.handler",
          runtime: "python3.12",
          environment: {
            PRICE_TABLE_NAME: priceTable.tableName,
            LATEST_UPDATE_TABLE_NAME: latestUpdateTable.tableName,
            STDDEV_TABLE_NAME: stdDevTable.tableName,
          },
        },
      },
    },
  });

  priceTable.addConsumers(stack, {
    stdDevConsumer: {
      function: {
        functionName: "StdDevConsumer",
        permissions: [stdDevTable, priceTable],
        handler: "packages/functions/src/stddev.handler",
        runtime: "python3.12",
        environment: {
          PRICE_TABLE_NAME: priceTable.tableName,
          STDDEV_TABLE_NAME: stdDevTable.tableName,
        },
      },
      cdk: {
        eventSource: {
          startingPosition: StartingPosition.LATEST,
          batchSize: 25,
          bisectBatchOnError: true,
          retryAttempts: 3,
        },
      },
    },
  });
  stack.addOutputs({
    ApiEndpoint: api.url,
  });
}
