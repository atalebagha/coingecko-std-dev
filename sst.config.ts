import { SSTConfig } from "sst";
import { API } from "./stacks/MyStack";
require("dotenv").config();

export default {
  config(_input) {
    return {
      name: "crypto-pricing",
      region: "us-east-1",
    };
  },
  stacks(app) {
    app.stack(API);
    app.setDefaultRemovalPolicy("destroy");
  },
} satisfies SSTConfig;
