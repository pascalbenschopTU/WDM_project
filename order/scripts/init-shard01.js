rs.initiate(
    {
        _id: "order_rs-shard-01", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order-shard01-a:27130" }, 
            { _id: 1, host: "order-shard01-b:27131" },
            { _id: 2, host: "order-shard01-c:27132" },
        ] 
    }
)