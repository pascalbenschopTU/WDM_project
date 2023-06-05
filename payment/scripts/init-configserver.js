rs.initiate({
  _id: "payment_rs-config-server",
  configsvr: true,
  version: 1,
  members: [
    { _id: 0, host: "payment-configsvr01:27119" },
    // { _id: 1, host: "payment-configsvr02:27120" },
    // { _id: 2, host: "payment-configsvr03:27121" },
  ],
});
