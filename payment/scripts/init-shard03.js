rs.initiate({
  _id: "payment_rs-shard-03",
  version: 1,
  members: [
    { _id: 0, host: "payment_shard03-a:27017" },
    { _id: 1, host: "payment_shard03-b:27017" },
    { _id: 2, host: "payment_shard03-c:27017" },
  ],
});
