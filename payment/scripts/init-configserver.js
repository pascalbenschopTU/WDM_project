rs.initiate({
  _id: "payment_rs-config-server",
  configsvr: true,
  version: 1,
  members: [
    { _id: 0, host: "payment_configsvr01:27017" },
    { _id: 1, host: "payment_configsvr02:27017" },
    { _id: 2, host: "payment_configsvr03:27017" },
  ],
});
