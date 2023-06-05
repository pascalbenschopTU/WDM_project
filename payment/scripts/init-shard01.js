rs.initiate({
  _id: "payment_rs-shard-01",
  version: 1,
  members: [
      { _id: 0, host: "payment-shard01-a:27122" },
      { _id: 1, host: "payment-shard01-b:27123" },
      { _id: 2, host: "payment-shard01-b:27124" },
  ],
});
