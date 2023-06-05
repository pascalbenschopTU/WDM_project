rs.initiate({
  _id: "payment_rs-shard-03",
  version: 1,
  members: [
    { _id: 0, host: "payment-shard03-a:27128" },
    { _id: 1, host: "payment-shard03-b:27129" }
  ],
});
