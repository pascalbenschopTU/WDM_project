rs.initiate({
  _id: "payment_rs-shard-02",
  version: 1,
  members: [
    { _id: 0, host: "payment-shard02-a:27125" },
    { _id: 1, host: "payment-shard02-b:27126" }
  ],
});
