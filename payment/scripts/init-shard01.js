rs.initiate({
  _id: "payment_rs-shard-01",
  version: 1,
  members: [
    { _id: 0, host: "payment_shard01-a:27017" },
    { _id: 1, host: "payment_shard01-b:27017" },
    { _id: 2, host: "payment_shard01-c:27017" },
  ],
});
